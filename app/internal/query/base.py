# app/internal/query/base.py
from datetime import date
from enum import Enum
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, select
from typing import Generic, TypeVar

from app.internal.log import factory_logger

ModelDB = TypeVar('ModelDB', bound=SQLModel)
ModelCreate = TypeVar('ModelCreate', bound=SQLModel)


log_base_query = factory_logger('base_query', file=True)


class Sort(str, Enum):
    ASC = 'asc'
    DESC = 'desc'


class DateRange(BaseModel):
    start_date: date
    end_date: date


class BaseQuery(Generic[ModelDB, ModelCreate]):
    def __init__(self, model_db: type[ModelDB], model_create: type[ModelCreate]) -> None:
        self.model_db = model_db
        self.model_create = model_create

    async def get(self, session: AsyncSession, id: int | str) -> ModelDB | None:
        """Obtiene un objeto por su ID"""
        result = await session.get(self.model_db, id)
        return result

    async def get_list(
        self, session: AsyncSession, skip: int = 0, limit: int = 100, sort: Sort = Sort.DESC
    ) -> list[ModelDB]:
        """Obtiene una lista de objetos de forma asíncrona."""
        order_id = self.model_db.id.asc() if sort == 'asc' else self.model_db.id.desc()  # type: ignore
        stmt = select(self.model_db).offset(skip).limit(limit).order_by(order_id)
        result = await session.execute(stmt)
        return list(result.scalars().all()) or []

    async def get_list_by_ids(
        self, session: AsyncSession, ids: list[int], sort: Sort = Sort.DESC
    ) -> list[ModelDB]:
        """Obtiene una lista de objetos de forma asíncrona."""
        order_id = self.model_db.id.asc() if sort == 'asc' else self.model_db.id.desc()  # type: ignore
        stmt = select(self.model_db).where(self.model_db.id.in_(ids)).order_by(order_id)  # type: ignore
        result = await session.execute(stmt)
        return list(result.scalars().all()) or []

    async def create(self, session: AsyncSession, obj: ModelCreate) -> ModelDB:
        """Crea un nuevo objeto de forma asíncrona."""
        create_model = self.model_create(
            **obj.model_dump(mode='json')
        )  # Se garantiza que el objeto sea del tipo correcto
        db_model = self.model_db(**create_model.model_dump(mode='json'))  # Modelo de retorno
        session.add(db_model)
        await session.commit()
        await session.refresh(db_model)  # Refresca para obtener el ID generado por la BD
        return db_model

    async def bulk_insert(self, session: AsyncSession, objs: list[ModelDB]):
        """Inserta varios objetos de forma asíncrona."""
        if len(objs) == 0:
            return
        objs_in_data = [obj.model_dump() for obj in objs]
        base_objs = [self.model_db(**obj_in_data) for obj_in_data in objs_in_data]
        session.add_all(base_objs)
        await session.commit()

    async def safe_bulk_insert(self, session: AsyncSession, objs: list[ModelDB]):
        objs = [obj for obj in objs if getattr(obj, 'id', None)]
        update_objs = []
        for obj in objs:
            update_obj = await self.upsert(session, obj)
            if update_obj:
                update_objs.append(update_obj)

        return update_objs

    async def update(self, session: AsyncSession, new_obj: ModelDB, pk: int | str) -> ModelDB:
        """Actualiza un objeto existente de forma asíncrona."""
        # Se garantiza que el objeto recibido si exista.
        db_obj = await session.get(self.model_db, pk)
        if not db_obj:
            exception = ValueError(f'No existe el objeto con id {pk}')
            log_base_query.error(str(exception))
            raise exception

        # Actualiza el objeto que ya está en la sesión
        update_data = new_obj.model_dump(exclude_unset=True)
        db_obj.sqlmodel_update(update_data)

        session.add(db_obj)  # Añade el objeto modificado a la sesión
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def upsert(self, session: AsyncSession, obj: ModelDB):
        id = getattr(obj, 'id', None)
        if id is None:
            log_base_query.debug(f'No se proporcionó un id para crear/actualizar, {obj.model_dump_json()}')
            return None

        if getattr(obj, 'id', None):
            db_obj = await self.get(session, id=id)
            if db_obj:
                return await self.update(session, obj, id)
            else:
                model_create = self.model_create(**obj.model_dump(mode='json'))
                return await self.create(session, model_create)

        return None

    async def delete(self, session: AsyncSession, id: int | str) -> ModelDB | None:
        """Elimina un objeto de forma asíncrona."""
        db_obj = await self.get(session, id)
        if not db_obj:
            return None

        await session.delete(db_obj)  # Marca para eliminación
        await session.commit()  # Confirma la eliminación
        # El objeto db_usuario todavía contiene los datos antes de ser eliminado,
        # lo cual es útil si quieres devolverlo como confirmación.
        return self.model_db(**db_obj.model_dump(mode='json'))

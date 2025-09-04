# app/internal/query/base.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, select
from typing import Generic, TypeVar

from app.internal.log import factory_logger

ModelDB = TypeVar('ModelDB', bound=SQLModel)
ModelCreate = TypeVar('ModelCreate', bound=SQLModel)


log_base_query = factory_logger('base_query', file=True)


class BaseQuery(Generic[ModelDB, ModelCreate]):
    def __init__(self, model_db: type[ModelDB], model_create: type[ModelCreate]) -> None:
        self.model_db = model_db
        self.model_create = model_create

    async def get(self, session: AsyncSession, id: int | str) -> ModelDB | None:
        """Obtiene un objeto por su ID"""
        result = await session.get(self.model_db, id)
        return result

    async def get_list(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> list[ModelDB]:
        """Obtiene una lista de objetos de forma asíncrona."""
        stmt = select(self.model_db).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all()) or []

    async def create(self, session: AsyncSession, obj: ModelCreate) -> ModelDB:
        """Crea un nuevo objeto de forma asíncrona."""
        obj_in_data = obj.model_dump()
        create_model = self.model_create(**obj_in_data)  # Se garantiza que el objeto sea del tipo correcto
        db_model = self.model_db(**create_model.model_dump())  # Modelo de retorno
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
        """
        Solo usar si los objetos tienen id
        """
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
        update_data = new_obj.model_dump(exclude_none=True, exclude_defaults=True)
        for key, value in update_data.items():
            if hasattr(db_obj, key) and getattr(db_obj, key) != value:
                setattr(db_obj, key, value)

        session.add(db_obj)  # Añade el objeto modificado a la sesión
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def upsert(self, session: AsyncSession, obj: ModelDB):
        id = getattr(obj, 'id', None)
        if id is None:
            log_base_query.debug(f'No hay id para actualizar, {obj.model_dump_json()}')
            return None

        if getattr(obj, 'id', None):
            db_obj = await self.get(session, id=id)
            if db_obj:
                return await self.update(session, obj, id)
            else:
                model_create = self.model_create(**obj.model_dump())
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
        return self.model_db(**db_obj.model_dump())

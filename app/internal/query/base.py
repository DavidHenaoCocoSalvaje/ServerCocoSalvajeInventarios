# app/internal/query/base.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, select
from typing import Generic, TypeVar

ModelDB = TypeVar('ModelDB', bound=SQLModel)
ModelCreate = TypeVar('ModelCreate', bound=SQLModel)


class BaseQuery(Generic[ModelDB, ModelCreate]):
    def __init__(self, model: type[ModelDB]) -> None:
        self.model = model

    async def get(self, session: AsyncSession, id: int | str) -> ModelDB | None:
        """Obtiene un objeto por su ID"""
        result = await session.get(self.model, id)
        return result

    async def get_list(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> list[ModelDB]:
        """Obtiene una lista de objetos de forma asíncrona."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all()) or [self.model()]

    async def create(self, session: AsyncSession, obj: ModelCreate) -> ModelDB:
        """Crea un nuevo objeto de forma asíncrona."""
        obj_in_data = obj.model_dump()
        base_obj = self.model(**obj_in_data)  # Se garantiza que el objeto sea del tipo correcto
        merge_obj = await session.merge(base_obj)
        await session.commit()
        await session.refresh(merge_obj)  # Refresca para obtener el ID generado por la BD
        return merge_obj

    async def bulk_insert(self, session: AsyncSession, objs: list[ModelDB]):
        """Inserta varios objetos de forma asíncrona."""
        if len(objs) == 0:
            return
        objs_in_data = [obj.model_dump() for obj in objs]
        base_objs = [self.model(**obj_in_data) for obj_in_data in objs_in_data]
        session.add_all(base_objs)
        await session.commit()

    async def update(self, session: AsyncSession, db_obj: SQLModel, obj: SQLModel):
        """Actualiza un objeto existente de forma asíncrona."""
        # Obtiene los datos a actualizar, excluyendo los no proporcionados (None)
        update_data = obj.model_dump(exclude_none=True)
        if not update_data:  # Si no se proporcionaron datos para actualizar
            return self.model(**db_obj.model_dump())  # Devuelve el usuario sin cambios

        # Actualiza los campos del objeto SQLAlchemy
        for key, value in update_data.items():
            # Verifica si el atributo existe en el objeto
            if hasattr(db_obj, key) and getattr(db_obj, key) != value:
                setattr(db_obj, key, value)

        session.add(db_obj)  # Añade el objeto modificado a la sesión (necesario para commit)
        await session.commit()
        await session.refresh(db_obj)
        return self.model(**db_obj.model_dump())

    async def delete(self, session: AsyncSession, id: int | str) -> ModelDB | None:
        """Elimina un objeto de forma asíncrona."""
        db_obj = await self.get(session, id)
        if not db_obj:
            return None

        await session.delete(db_obj)  # Marca para eliminación
        await session.commit()  # Confirma la eliminación
        # El objeto db_usuario todavía contiene los datos antes de ser eliminado,
        # lo cual es útil si quieres devolverlo como confirmación.
        return self.model(**db_obj.model_dump())

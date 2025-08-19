# app/routers/base.py
from typing import TypeVar, Generic
from fastapi import APIRouter, HTTPException, status
from sqlmodel import SQLModel

from app.internal.gen.utilities import pluralizar_por_sep
from app.models.db.session import AsyncSessionDep
from app.internal.query.base import BaseQuery

# Define un TypeVar para los modelos de SQLModel
Model = TypeVar('Model', bound=SQLModel)


class CRUD(Generic[Model]):
    def __init__(self, router: APIRouter, query: BaseQuery, name: str) -> None:
        super().__init__()
        """
        Crea rutas CRUD genéricas para un modelo dado.

        Args:
            model (type[ModelType]): La clase del modelo SQLModel.
            query_class (type[BaseQuery[ModelType]]): La clase de consulta correspondiente al modelo.
            name (str): El nombre singular del recurso (ej. "bodega_inventario").
            id_type (type): El tipo de dato del ID (int o str), por defecto int.
        """

        # POST - Crear un nuevo recurso
        @router.post(
            f'/{name}',
            response_model=Model,
            status_code=status.HTTP_201_CREATED,
            response_model_exclude_unset=True,
            response_model_exclude_none=True,
            summary=f'Crear un nuevo {name.replace("_", " ")}',
            description=f'Crea un nuevo {name.replace("_", " ")} con los datos proporcionados.',
        )
        async def create_resource(
            resource: Model,
            session: AsyncSessionDep,
        ) -> Model:
            """Crea un nuevo recurso."""
            await query.create(session, resource)
            return resource

        # GET - Obtener lista de recursos
        @router.get(
            f'/{pluralizar_por_sep(name, "_", 1)}',  # Plural para la lista (ej. /bodegas_inventario)
            response_model=list[Model],
            response_model_exclude_none=True,
            summary=f'Obtener lista de {name.replace("_", " ")}s',
            description=f'Obtiene una lista paginada de {pluralizar_por_sep(name, "_", 1).replace("_", " ")}.',
        )
        async def get_resources(
            session: AsyncSessionDep,
            skip: int = 0,
            limit: int = 100,
        ) -> list[Model]:
            """Obtiene una lista de recursos."""
            resources = await query.get_list(session=session, skip=skip, limit=limit)
            return resources

        # GET - Obtener un recurso por ID
        @router.get(
            f'/{name}/{{{name}_id}}',
            response_model=Model,
            summary=f'Obtener un {name.replace("_", " ")} por ID',
            description=f'Obtiene los detalles de un {name.replace("_", " ")} específico mediante su ID.',
            response_model_exclude_none=True,
        )
        async def get_resource(
            session: AsyncSessionDep,
            resource_id: int,
        ) -> Model:
            """Obtiene un recurso por ID."""
            db_resource = await query.get(session, resource_id)
            if db_resource is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f'{Model.__name__} con ID {resource_id} no encontrado',
                )
            return db_resource

        # PUT - Actualizar un recurso
        @router.put(
            f'/{name}/{{{name}_id}}',
            response_model=Model,
            summary=f'Actualizar un {name.replace("_", " ")}',
        )
        async def update_resource(
            session: AsyncSessionDep,
            resource_id: int,
            new_data: Model,
        ) -> Model:
            """Actualiza un recurso."""
            resourse_db = await query.get(session, resource_id)
            if resourse_db is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f'{Model.__name__} con ID {resource_id} no encontrado',
                )
            updated_resource = await query.update(session, resourse_db, new_data)
            return updated_resource

        # DELETE - Eliminar un recurso
        @router.delete(
            f'/{name}/{{{name}_id}}',
            response_model=Model,
            summary=f'Eliminar un {name.replace("_", " ")}',
        )
        async def delete_resource(
            session: AsyncSessionDep,
            resource_id: int,
        ) -> Model:
            """Elimina un recurso."""
            deleted_resource = await query.delete(session, resource_id)
            if deleted_resource is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f'{Model.__name__} con ID {resource_id} no encontrado',
                )
            return deleted_resource

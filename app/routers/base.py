# app/routers/base.py
from typing import Annotated, TypeVar
from fastapi import APIRouter, HTTPException, status
from sqlmodel import SQLModel

from app.internal.gen.utilities import pluralizar_por_sep
from app.internal.query.base import BaseQuery, Sort
from app.models.db.session import AsyncSessionDep


# Define un TypeVar para los modelos de SQLModel
ModelQuery = TypeVar('ModelQuery', bound=BaseQuery)
ModelDB = TypeVar('ModelDB', bound=SQLModel)
ModelCreate = TypeVar('ModelCreate', bound=SQLModel)


class CRUD:
    def __init__(
        self,
        router: APIRouter,
        name: str,
        model_query: BaseQuery,
        model_db: type[ModelDB],
        model_create: type[ModelCreate],
    ) -> None:
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
            operation_id=f'create_{name}',
            response_model=model_db,
            status_code=status.HTTP_201_CREATED,
            summary=f'Crear un nuevo {name.replace("_", " ")}',
            description=f'Crea un nuevo {name.replace("_", " ")} con los datos proporcionados.',
        )
        async def create_resource(
            resource: Annotated[SQLModel, model_create],
            session: AsyncSessionDep,
        ) -> ModelDB:
            """Crea un nuevo recurso."""
            return await model_query.create(session, resource)

        # GET - Obtener lista de recursos
        @router.get(
            f'/{pluralizar_por_sep(name, "_", 1)}',  # Plural para la lista (ej. /bodegas_inventario)
            operation_id=f'get_{pluralizar_por_sep(name, "_", 1)}',
            response_model=list[model_db],
            summary=f'Obtener lista de {name.replace("_", " ")}s',
            description=f'Obtiene una lista paginada de {pluralizar_por_sep(name, "_", 1).replace("_", " ")}.',
        )
        async def get_resources(
            session: AsyncSessionDep,
            skip: int = 0,
            limit: int = 100,
            sort: Sort = Sort.DESC,
        ) -> list[ModelDB]:
            """Obtiene una lista de recursos."""
            return await model_query.get_list(session=session, skip=skip, limit=limit, sort=sort)

        # GET - Obtener un recurso por ID
        @router.get(
            f'/{name}/{{{name}_id}}',
            operation_id=f'get_{name}_by_id',
            response_model=model_db,
            summary=f'Obtener {name.replace("_", " ")} por ID',
            description=f'Obtiene los detalles de {name.replace("_", " ")} específico mediante su ID.',
        )
        async def get_resource(
            session: AsyncSessionDep,
            resource_id: int,
        ) -> ModelDB:
            """Obtiene un recurso por ID."""
            db_resource = await model_query.get(session, resource_id)
            if db_resource is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f'{ModelDB.__name__} con ID {resource_id} no encontrado',
                )
            return db_resource

        # PUT - Actualizar un recurso
        @router.put(
            f'/{name}/{{{name}_id}}',
            operation_id=f'update_{name}',
            response_model=model_db,
            summary=f'Actualizar {name.replace("_", " ")}',
        )
        async def update_resource(
            session: AsyncSessionDep,
            resource_id: int,
            new_data: Annotated[SQLModel, model_create],
        ) -> ModelDB:
            """Actualiza un recurso."""
            resourse_db = await model_query.get(session, resource_id)
            if resourse_db is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f'{ModelDB.__name__} con ID {resource_id} no encontrado',
                )
            updated_resource = await model_query.update(session, new_data, resource_id)
            return updated_resource

        # DELETE - Eliminar un recurso
        @router.delete(
            f'/{name}/{{{name}_id}}',
            operation_id=f'delete_{name}',
            response_model=model_db,
            summary=f'Eliminar {name.replace("_", " ")}',
        )
        async def delete_resource(
            session: AsyncSessionDep,
            resource_id: int,
        ) -> ModelDB:
            """Elimina un recurso."""
            deleted_resource = await model_query.delete(session, resource_id)
            if deleted_resource is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f'{ModelDB.__name__} con ID {resource_id} no encontrado',
                )
            return deleted_resource

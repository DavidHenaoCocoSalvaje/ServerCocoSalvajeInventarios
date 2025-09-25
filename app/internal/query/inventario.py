# app/internal/query/inventario.py
import json
from os import path
from sqlmodel import SQLModel, select, desc, func

if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))


from app.models.db.inventario import (
    Bodega,
    BodegaCreate,
    ComponentesPorVariante,
    ComponentesPorVarianteCreate,
    Elemento,
    ElementoCreate,
    EstadoVariante,
    EstadoVarianteCreate,
    Grupo,
    GrupoCreate,
    Medida,
    MedidaCreate,
    MedidasPorVariante,
    MedidasPorVarianteCreate,
    Movimiento,
    MovimientoCreate,
    PreciosPorVariante,
    PreciosPorVarianteCreate,
    TipoMovimiento,
    TipoMovimientoCreate,
    TipoPrecio,
    TipoPrecioCreate,
    TipoSoporteCreate,
    TiposMedida,
    TiposMedidaCreate,
    TipoSoporte,
    VarianteElemento,
    VarianteElementoCreate,
)
from app.internal.query.base import BaseQuery, ModelCreate, ModelDB
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db.session import get_async_session


class BaseQueryWithShopifyId(BaseQuery[ModelDB, ModelCreate]):
    def __init__(self, model_db: type[ModelDB], model_create: type[ModelCreate]) -> None:
        super().__init__(model_db, model_create)

    async def get_by_shopify_id(self, session: AsyncSession, shopify_id: int) -> ModelDB | None:
        statement = select(self.model_db).where(self.model_db.shopify_id == shopify_id)  # type: ignore
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_shopify_ids(self, session: AsyncSession, shopify_ids: list[int]) -> list[ModelDB]:
        statement = select(self.model_db).where(self.model_db.shopify_id.in_(shopify_ids))  # type: ignore
        result = await session.execute(statement)
        return list(result.scalars().all()) or []


class BaseQeuryTipo(BaseQuery[ModelDB, ModelCreate]):
    def __init__(self, model_db: type[ModelDB], model_create: type[ModelCreate]):
        super().__init__(model_db, model_create)

    async def get_by_nombre(self, session: AsyncSession, nombre: str) -> ModelDB:
        statement = select(self.model_db).where(func.lower(self.model_db.nombre) == nombre.lower())  # type: ignore
        result = await session.execute(statement)
        obj = result.scalar_one_or_none()
        if obj is None:
            raise ValueError(f"{self.model_db.__name__} con '{nombre}' no encontrado")
        return obj


class PrecioPorVarianteQuery(BaseQuery[PreciosPorVariante, PreciosPorVarianteCreate]):
    def __init__(self) -> None:
        super().__init__(PreciosPorVariante, PreciosPorVarianteCreate)

    async def get_last(self, session: AsyncSession, variante_id: int, tipo_precio_id: int) -> PreciosPorVariante | None:
        statement = (
            select(self.model_db)
            .where(self.model_db.variante_id == variante_id)
            .where(self.model_db.tipo_precio_id == tipo_precio_id)
            .order_by(desc(self.model_db.fecha))
            .limit(1)
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_lasts(
        self, session: AsyncSession, variante_ids: list[int], tipo_precio_id: int
    ) -> list[PreciosPorVariante]:
        """Obtiene el último precio para cada variante y tipo de precio"""
        subq = (
            select(
                self.model_db.id,
                func.row_number()
                .over(
                    partition_by=self.model_db.variante_id,  # type: ignore
                    order_by=desc(self.model_db.fecha),
                )
                .label('rn'),
            )
            .where(self.model_db.variante_id.in_(variante_ids))  # type: ignore
            .where(self.model_db.tipo_precio_id == tipo_precio_id)
            .subquery()
        )

        # IMPORTANTE seleccionar self.model para que SQLModel pueda mapear los campos
        statement = select(self.model_db).join(subq, self.model_db.id == subq.c.id).where(subq.c.rn == 1)  # type: ignore
        result = await session.execute(statement)
        return list(result.scalars().all()) or []  # type: ignore


class MovimientoQuery(BaseQuery[Movimiento, MovimientoCreate]):
    def __init__(self) -> None:
        super().__init__(Movimiento, MovimientoCreate)

    async def get_total_by(self, session: AsyncSession, variante_id: int, tipo_movimiento_id: int):
        statement = (
            select(func.sum(self.model_db.cantidad))
            .where(self.model_db.variante_id == variante_id)
            .where(self.model_db.tipo_movimiento_id == tipo_movimiento_id)
        )
        result = await session.execute(statement)
        suma = result.scalar_one()
        return suma

    async def get_by_soporte_variante_id(
        self, session: AsyncSession, tipo_soporte_id: int, soporte_id: str, variante_elemento_id: int
    ) -> Movimiento | None:
        statement = (
            select(self.model_db)
            .where(self.model_db.variante_id == variante_elemento_id)
            .where(self.model_db.tipo_soporte_id == tipo_soporte_id)
            .where(self.model_db.soporte_id == soporte_id)
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()


class ElementoQuery(BaseQueryWithShopifyId[Elemento, ElementoCreate]):
    def __init__(self) -> None:
        super().__init__(Elemento, ElementoCreate)


class BodegaQuery(BaseQueryWithShopifyId[Bodega, BodegaCreate]):
    def __init__(self) -> None:
        super().__init__(Bodega, BodegaCreate)


class VarianteElementoQuery(BaseQueryWithShopifyId[VarianteElemento, VarianteElementoCreate]):
    def __init__(self) -> None:
        super().__init__(VarianteElemento, VarianteElementoCreate)

    async def get_by_sku(self, session: AsyncSession, sku: str) -> VarianteElemento | None:
        statement = select(self.model_db).where(self.model_db.sku == sku)
        result = await session.execute(statement)
        return result.scalar_one_or_none()


class ComponentesPorVarianteQuery(BaseQuery[ComponentesPorVariante, ComponentesPorVarianteCreate]):
    def __init__(self) -> None:
        super().__init__(ComponentesPorVariante, ComponentesPorVarianteCreate)


class GrupoQuery(BaseQuery[Grupo, GrupoCreate]):
    def __init__(self) -> None:
        super().__init__(Grupo, GrupoCreate)


class MedidaQuery(BaseQuery[Medida, MedidaCreate]):
    def __init__(self) -> None:
        super().__init__(Medida, MedidaCreate)


class TipoPrecioQuery(BaseQuery[TipoPrecio, TipoPrecioCreate]):
    def __init__(self) -> None:
        super().__init__(TipoPrecio, TipoPrecioCreate)


class TiposMedidaQuery(BaseQuery[TiposMedida, TiposMedidaCreate]):
    def __init__(self) -> None:
        super().__init__(TiposMedida, TiposMedidaCreate)


class TipoSoporteQuery(BaseQeuryTipo[TipoSoporte, TipoSoporteCreate]):
    def __init__(self) -> None:
        super().__init__(TipoSoporte, TipoSoporteCreate)


class MedidasPorVarianteQuery(BaseQuery[MedidasPorVariante, MedidasPorVarianteCreate]):
    def __init__(self) -> None:
        super().__init__(MedidasPorVariante, MedidasPorVarianteCreate)


class TipoMovimientoQuery(BaseQeuryTipo[TipoMovimiento, TipoMovimientoCreate]):
    def __init__(self) -> None:
        super().__init__(TipoMovimiento, TipoMovimientoCreate)


class EstadoVarianteQuery(BaseQeuryTipo[EstadoVariante, EstadoVarianteCreate]):
    def __init__(self) -> None:
        super().__init__(EstadoVariante, EstadoVarianteCreate)


async def seed_data_inventario():
    # Leer el archivo JSON usando ruta relativa
    data_path = path.join('app', 'default_data', 'data.json')
    with open(data_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    async for session in get_async_session():
        async with session:
            # Upserts (ON CONFLICT DO UPDATE) por tabla, en orden de dependencias
            # Nota: se usa conflicto por PK 'id' y se actualizan todas las columnas excepto la PK
            models: list[tuple[type[SQLModel], str, BaseQuery]] = [
                (EstadoVariante, 'estados_variante', EstadoVarianteQuery()),
                (TipoMovimiento, 'tipos_movimiento', TipoMovimientoQuery()),
                (TipoPrecio, 'tipos_precios', TipoPrecioQuery()),
                (Grupo, 'grupos', GrupoQuery()),
                (TiposMedida, 'tipos_medida', TiposMedidaQuery()),
                (TipoSoporte, 'tipos_soporte', TipoSoporteQuery()),
                (Medida, 'medidas', MedidaQuery()),
            ]

            for Model, data_key, model_query in models:
                items: list[dict] = data.get(data_key, [])
                if not items:
                    continue

                models = [Model(**item) for item in items]
                for model in models:
                    await model_query.upsert(session, model)


if __name__ == '__main__':
    import asyncio

    async def main():
        async for session in get_async_session():
            async with session:
                await seed_data_inventario()
                movimiento_query = MovimientoQuery()
                await movimiento_query.get_total_by(session, variante_id=5, tipo_movimiento_id=1)

    asyncio.run(main())

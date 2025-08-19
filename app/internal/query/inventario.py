# app/internal/query/inventario.py
import json
from os import path
from typing import Generic
from sqlmodel import select, desc
from app.models.db.inventario import (
    Elemento,
    Bodega,
    Grupo,
    Medida,
    TiposMedida,
    MedidasPorVariante,
    PreciosPorVariante,
    TipoPrecio,
    Movimiento,
    TipoMovimiento,
    EstadoVariante,
    VarianteElemento,
    ComponentesPorVariante,
    TipoSoporte,
)
from app.internal.query.base import BaseQuery, ModelDB, ModelCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func
from app.models.db.session import get_async_session
from sqlalchemy.dialects.postgresql import insert


class BaseQueryWithShopifyId(BaseQuery, Generic[ModelDB, ModelCreate]):
    def __init__(self, model: type[ModelDB]) -> None:
        super().__init__(model)

    async def get_by_shopify_id(self, session: AsyncSession, shopify_id: int) -> ModelDB | None:
        statement = select(self.model).where(self.model.shopify_id == shopify_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_shopify_ids(self, session: AsyncSession, shopify_ids: list[int]) -> list[ModelDB]:
        statement = select(self.model).where(self.model.shopify_id.in_(shopify_ids))
        result = await session.execute(statement)
        return list(result.scalars().all()) or [self.model()]


class PrecioPorVarianteQuery(BaseQuery[PreciosPorVariante, PreciosPorVariante]):
    def __init__(self) -> None:
        super().__init__(PreciosPorVariante)

    async def get_last(self, session: AsyncSession, variante_id: int, tipo_precio_id: int) -> PreciosPorVariante | None:
        statement = (
            select(self.model)
            .where(self.model.variante_id == variante_id)
            .where(self.model.tipo_precio_id == tipo_precio_id)
            .order_by(desc(self.model.fecha))
            .limit(1)
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_lasts(
        self, session: AsyncSession, variante_ids: list[int], tipo_precio_id: int
    ) -> list[PreciosPorVariante]:
        subq = (
            select(
                self.model.id,
                func.row_number()
                .over(
                    partition_by=self.model.variante_id,  # type: ignore
                    order_by=desc(self.model.fecha),
                )
                .label('rn'),
            )
            .where(self.model.variante_id.in_(variante_ids))  # type: ignore
            .where(self.model.tipo_precio_id == tipo_precio_id)
            .subquery()
        )

        # IMPORTANTE seleccionar self.model para que SQLModel pueda mapear los campos
        statement = select(self.model).join(subq, self.model.id == subq.c.id).where(subq.c.rn == 1)  # type: ignore
        result = await session.execute(statement)
        return list(result.scalars().all()) or [self.model()]  # type: ignore


class MovimientoQuery(BaseQuery[Movimiento, Movimiento]):
    def __init__(self) -> None:
        super().__init__(Movimiento)

    async def get_by_varante_ids(self, session: AsyncSession, variante_ids: list[int]) -> list[Movimiento]:
        statement = select(self.model).where(self.model.variante_id.in_(variante_ids))  # type: ignore
        result = await session.execute(statement)
        return list(result.scalars().all()) or [self.model()]  # type: ignore


elemento_query = BaseQueryWithShopifyId(Elemento)
bodega_query = BaseQueryWithShopifyId(Bodega)
variante_elemento_query = BaseQueryWithShopifyId(VarianteElemento)
componentes_por_variante_query = BaseQuery(ComponentesPorVariante)
grupo_query = BaseQuery(Grupo)
unidad_medida_query = BaseQuery(Medida)
precio_variante_query = PrecioPorVarianteQuery()
tipo_precio_query = BaseQuery(TipoPrecio)
tipo_medida_query = BaseQuery(TiposMedida)
tipo_soporte_query = BaseQuery(TipoSoporte)
medidas_por_variante_query = BaseQuery(MedidasPorVariante)
movimiento_query = MovimientoQuery()
tipo_movimiento_query = BaseQuery(TipoMovimiento)
estado_elemento_query = BaseQuery(EstadoVariante)


async def seed_data_inventario():
    # Leer el archivo JSON usando ruta relativa
    data_path = path.join('app', 'default_data', 'data.json')
    with open(data_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    session_gen = get_async_session()
    session: AsyncSession = await anext(session_gen)
    try:
        # Upserts (ON CONFLICT DO UPDATE) por tabla, en orden de dependencias
        # Nota: se usa conflicto por PK 'id' y se actualizan todas las columnas excepto la PK
        pares = [
            (EstadoVariante, 'estados_variante'),
            (TipoMovimiento, 'tipos_movimiento'),
            (TipoPrecio, 'tipos_precios'),
            (Grupo, 'grupos'),
            (TiposMedida, 'tipos_medida'),
            (TipoSoporte, 'tipos_soporte'),
            (Medida, 'medidas'),
        ]

        for Model, key in pares:
            items = data.get(key, [])
            if not items:
                continue

            table = Model.__table__  # type: ignore[attr-defined]
            insert_stmt = insert(table).values(items)

            # Construir set_ dinámico: todas las columnas excepto la PK 'id'
            update_cols = [c.name for c in table.c if c.name != 'id']
            set_dict = {col: getattr(insert_stmt.excluded, col) for col in update_cols}

            stmt = insert_stmt.on_conflict_do_update(
                index_elements=[table.c.id],
                set_=set_dict,
            )
            await session.execute(stmt)
        await session.commit()

    finally:
        await session_gen.aclose()

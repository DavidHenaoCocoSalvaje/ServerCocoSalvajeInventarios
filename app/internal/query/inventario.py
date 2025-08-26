# app/internal/query/inventario.py
import json
from os import path
from typing import Generic
from sqlmodel import select, desc
from app.models.db.inventario import (
    BodegaCreate,
    ComponentesPorVarianteCreate,
    Elemento,
    Bodega,
    ElementoCreate,
    EstadoVarianteCreate,
    Grupo,
    GrupoCreate,
    Medida,
    MedidaCreate,
    MedidasPorVarianteCreate,
    MovimientoCreate,
    PreciosPorVarianteCreate,
    TipoMovimientoCreate,
    TipoPrecioCreate,
    TipoSoporteCreate,
    TiposMedida,
    MedidasPorVariante,
    PreciosPorVariante,
    TipoPrecio,
    Movimiento,
    TipoMovimiento,
    EstadoVariante,
    TiposMedidaCreate,
    VarianteElemento,
    ComponentesPorVariante,
    TipoSoporte,
    VarianteElementoCreate,
)
from app.internal.query.base import BaseQuery, ModelDB, ModelCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func
from app.models.db.session import get_async_session
from sqlalchemy.dialects.postgresql import insert


class BaseQueryWithShopifyId(BaseQuery, Generic[ModelDB, ModelCreate]):
    def __init__(self, model_db: type[ModelDB], model_create: type[ModelCreate]) -> None:
        super().__init__(model_db, model_create)

    async def get_by_shopify_id(self, session: AsyncSession, shopify_id: int) -> ModelDB | None:
        statement = select(self.model_db).where(self.model_db.shopify_id == shopify_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_shopify_ids(self, session: AsyncSession, shopify_ids: list[int]) -> list[ModelDB]:
        statement = select(self.model_db).where(self.model_db.shopify_id.in_(shopify_ids))
        result = await session.execute(statement)
        return list(result.scalars().all()) or []


class PrecioPorVarianteQuery(BaseQuery[PreciosPorVariante, PreciosPorVarianteCreate]):
    def __init__(self) -> None:
        super().__init__(PreciosPorVariante, PreciosPorVariante)

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
        super().__init__(Movimiento, Movimiento)

    async def get_by_varante_ids(self, session: AsyncSession, variante_ids: list[int]) -> list[Movimiento]:
        statement = select(self.model_db).where(self.model_db.variante_id.in_(variante_ids))  # type: ignore
        result = await session.execute(statement)
        return list(result.scalars().all()) or []  # type: ignore


elemento_query = BaseQueryWithShopifyId(Elemento, ElementoCreate)
bodega_query = BaseQueryWithShopifyId(Bodega, BodegaCreate)
variante_elemento_query = BaseQueryWithShopifyId(VarianteElemento, VarianteElementoCreate)
componentes_por_variante_query = BaseQuery(ComponentesPorVariante, ComponentesPorVarianteCreate)
grupo_query = BaseQuery(Grupo, GrupoCreate)
unidad_medida_query = BaseQuery(Medida, MedidaCreate)
precio_variante_query = PrecioPorVarianteQuery()
tipo_precio_query = BaseQuery(TipoPrecio, TipoPrecioCreate)
tipo_medida_query = BaseQuery(TiposMedida, TiposMedidaCreate)
tipo_soporte_query = BaseQuery(TipoSoporte, TipoSoporteCreate)
medidas_por_variante_query = BaseQuery(MedidasPorVariante, MedidasPorVarianteCreate)
movimiento_query = MovimientoQuery()
tipo_movimiento_query = BaseQuery(TipoMovimiento, TipoMovimientoCreate)
estado_elemento_query = BaseQuery(EstadoVariante, EstadoVarianteCreate)


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

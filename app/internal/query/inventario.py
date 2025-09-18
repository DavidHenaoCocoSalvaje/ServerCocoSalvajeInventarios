# app/internal/query/inventario.py
import json
from os import path
from sqlmodel import select, desc


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
    TiposMedida,
    TiposMedidaCreate,
    TipoSoporte,
    VarianteElemento,
    VarianteElementoCreate,
)
from app.internal.query.base import BaseQuery, ModelCreate, ModelDB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func
from app.models.db.session import get_async_session
from sqlalchemy.dialects.postgresql import insert


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

    async def get_by_varante_ids(self, session: AsyncSession, variante_ids: list[int]) -> list[Movimiento]:
        statement = select(self.model_db).where(self.model_db.variante_id.in_(variante_ids))  # type: ignore
        result = await session.execute(statement)
        return list(result.scalars().all()) or []  # type: ignore

    async def get_by_soporte_ids(
        self, session: AsyncSession, tipo_soporte_id: int, soporte_ids: list[str]
    ) -> list[Movimiento]:
        statement = (
            select(self.model_db)
            .where(self.model_db.tipo_soporte_id == tipo_soporte_id)
            .where(self.model_db.soporte_id.in_(soporte_ids))  # type: ignore
        )
        result = await session.execute(statement)
        return list(result.scalars().all()) or []


class ElementoQuery(BaseQueryWithShopifyId[Elemento, ElementoCreate]):
    def __init__(self) -> None:
        super().__init__(Elemento, ElementoCreate)


class BodegaQuery(BaseQueryWithShopifyId[Bodega, BodegaCreate]):
    def __init__(self) -> None:
        super().__init__(Bodega, BodegaCreate)


class VarianteElementoQuery(BaseQueryWithShopifyId[VarianteElemento, VarianteElementoCreate]):
    def __init__(self) -> None:
        super().__init__(VarianteElemento, VarianteElementoCreate)


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


class MedidasPorVarianteQuery(BaseQuery[MedidasPorVariante, MedidasPorVarianteCreate]):
    def __init__(self) -> None:
        super().__init__(MedidasPorVariante, MedidasPorVarianteCreate)


class TipoMovimientoQuery(BaseQuery[TipoMovimiento, TipoMovimientoCreate]):
    def __init__(self) -> None:
        super().__init__(TipoMovimiento, TipoMovimientoCreate)


class EstadoVarianteQuery(BaseQuery[EstadoVariante, EstadoVarianteCreate]):
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

                models = [Model(**item) for item in items]
                table = Model.__table__  # type: ignore[attr-defined]
                models_dump = [model.model_dump() for model in models]
                insert_stmt = insert(table).values(models_dump)

                stmt = insert_stmt.on_conflict_do_nothing(
                    index_elements=['id'],
                )
                await session.execute(stmt)
            await session.commit()

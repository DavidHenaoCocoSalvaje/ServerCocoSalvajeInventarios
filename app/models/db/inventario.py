# app/models/inventario.py
from datetime import datetime, date
from enum import Enum
from pydantic import ConfigDict
from sqlmodel import SQLModel, Field, Relationship, SMALLINT, DATE, TEXT, BIGINT, TIMESTAMP

if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))

from app.internal.gen.utilities import DateTz


class InventarioBase(SQLModel):
    __table_args__ = {'schema': 'inventario'}


class BodegaCreate(InventarioBase):
    ubicacion: str = Field(max_length=150)
    shopify_id: int = Field(sa_type=BIGINT)


class Bodega(BodegaCreate, table=True):
    __tablename__ = 'bodegas'  # type: ignore

    id: int = Field(primary_key=True, sa_type=SMALLINT)

    def __hash__(self):
        return hash(self.id)

    # Relationships
    movimientos: list['Movimiento'] = Relationship(back_populates='bodega')


class GrupoCreate(InventarioBase):
    nombre: str = Field(max_length=50)


class Grupo(GrupoCreate, table=True):
    __tablename__ = 'grupos'  # type: ignore

    id: int | None = Field(primary_key=True, sa_type=SMALLINT, default=None)

    # Relationships
    elementos: list['Elemento'] = Relationship(back_populates='grupo')


class TiposMedidaCreate(InventarioBase):
    nombre: str = Field(max_length=50)


class TiposMedida(TiposMedidaCreate, table=True):
    __tablename__ = 'tipos_medida'  # type: ignore

    id: int | None = Field(primary_key=True, sa_type=SMALLINT, default=None)

    # Relationships
    medidas: list['Medida'] = Relationship(back_populates='tipo_medida')


class MedidaCreate(InventarioBase):
    nombre: str = Field(max_length=50)
    nombre_largo: str = Field(max_length=50)
    tipo_medida_id: int = Field(foreign_key='inventario.tipos_medida.id', default=None, nullable=True)


class Medida(MedidaCreate, table=True):
    __tablename__ = 'medidas'  # type: ignore

    id: int | None = Field(primary_key=True, sa_type=SMALLINT, default=None)

    # Relationships
    tipo_medida: 'TiposMedida' = Relationship(back_populates='medidas')
    variantes: list['MedidasPorVariante'] = Relationship(back_populates='medida')


class MedidasPorVarianteCreate(InventarioBase):
    medida_id: int = Field(foreign_key='inventario.medidas.id', default=None, nullable=True)
    variante_id: int = Field(foreign_key='inventario.variantes_elemento.id', default=None, nullable=True)


class MedidasPorVariante(MedidasPorVarianteCreate, table=True):
    __tablename__ = 'medidas_por_variante'  # type: ignore

    id: int = Field(primary_key=True)

    # Relationships
    medida: 'Medida' = Relationship(back_populates='variantes')
    variante: 'VarianteElemento' = Relationship(back_populates='medidas')


class TipoPrecioCreate(InventarioBase):
    nombre: str = Field(max_length=50)
    descripcion: str | None = Field(sa_type=TEXT, default=None)


class TipoPrecio(TipoPrecioCreate, table=True):
    __tablename__ = 'tipos_precio'  # type: ignore

    id: int | None = Field(primary_key=True, sa_type=SMALLINT, default=None)

    # Relationships
    precios: list['PreciosPorVariante'] = Relationship(back_populates='tipo_precio')


class PreciosPorVarianteCreate(InventarioBase):
    variante_id: int = Field(foreign_key='inventario.variantes_elemento.id', default=None, nullable=True)
    tipo_precio_id: int = Field(foreign_key='inventario.tipos_precio.id', default=None, nullable=True)
    precio: float = Field(default=0.0)
    fecha: date = Field(sa_type=DATE, default_factory=DateTz.today)


class PreciosPorVariante(PreciosPorVarianteCreate, table=True):
    __tablename__ = 'precios_variante'  # type: ignore

    id: int = Field(primary_key=True)

    # Relationships
    tipo_precio: 'TipoPrecio' = Relationship(back_populates='precios')
    variante: 'VarianteElemento' = Relationship(back_populates='precios')


class Comportamiento(int, Enum):
    entrada = 1
    salida = -1


class TipoMovimientoCreate(InventarioBase):
    nombre: str = Field(max_length=50)
    descripcion: str | None = Field(sa_type=TEXT, default=None)
    comportamiento: Comportamiento = Field(sa_type=SMALLINT)

    model_config = ConfigDict(use_enum_values=True)  # type: ignore


class TipoMovimiento(TipoMovimientoCreate, table=True):
    __tablename__ = 'tipos_movimiento'  # type: ignore

    id: int = Field(primary_key=True, sa_type=SMALLINT, default=None)

    # Relationships
    movimientos: list['Movimiento'] = Relationship(back_populates='tipo_movimiento')


class TipoSoporteCreate(InventarioBase):
    nombre: str = Field(max_length=50)


class TipoSoporte(TipoSoporteCreate, table=True):
    __tablename__ = 'tipos_soporte'  # type: ignore

    id: int = Field(primary_key=True, sa_type=SMALLINT, default=None)

    # Relationships
    movimientos: list['Movimiento'] = Relationship(back_populates='tipo_soporte')


class MovimientoCreate(InventarioBase):
    tipo_movimiento_id: int | None = Field(foreign_key='inventario.tipos_movimiento.id', default=None)
    tipo_soporte_id: int | None = Field(foreign_key='inventario.tipos_soporte.id', default=None)
    variante_id: int | None = Field(foreign_key='inventario.variantes_elemento.id', default=None)
    estado_variante_id: int | None = Field(foreign_key='inventario.estados_variante.id', default=None)
    cantidad: int = Field(default=0)
    valor: float = Field(default=0.0)
    bodega_id: int = Field(foreign_key='inventario.bodegas.id', default=None, nullable=True)
    soporte_id: str | None = Field(sa_type=TEXT, default=None)
    nota: str | None = Field(sa_type=TEXT, default=None)
    fecha: datetime = Field(sa_type=TIMESTAMP(timezone=True), default_factory=DateTz.local)  # type: ignore


class Movimiento(MovimientoCreate, table=True):
    __tablename__ = 'movimientos'  # type: ignore

    id: int = Field(primary_key=True)

    # Relationships
    variante: 'VarianteElemento' = Relationship(back_populates='movimientos')
    estado_variante: 'EstadoVariante' = Relationship(back_populates='movimientos')
    bodega: 'Bodega' = Relationship(back_populates='movimientos')
    tipo_movimiento: 'TipoMovimiento' = Relationship(back_populates='movimientos')
    tipo_soporte: 'TipoSoporte' = Relationship(back_populates='movimientos')
    meta_atributos: list['MovimientoPorMetaAtributo'] = Relationship(back_populates='movimiento')


# region metadatos
# Modelo EAV (Entity-Attribute-Value) para metadatos de movimientos
class MovimientoPorMetaAtributoCreate(InventarioBase):
    movimiento_id: int = Field(foreign_key='inventario.movimientos.id', default=None, nullable=True)
    meta_atributo_id: int = Field(foreign_key='inventario.meta_atributos.id', default=None, nullable=True)
    meta_valor_id: int = Field(foreign_key='inventario.meta_valores.id', default=None, nullable=True)


class MovimientoPorMetaAtributo(MovimientoPorMetaAtributoCreate, table=True):
    __tablename__ = 'movimiento_meta_atributo'  # type: ignore

    id: int = Field(primary_key=True)

    # Relationships
    movimiento: 'Movimiento' = Relationship(back_populates='meta_atributos')
    meta_atributo: 'MetaAtributo' = Relationship(back_populates='movimientos')
    meta_valor: 'MetaValor' = Relationship(back_populates='movimientos')


class MetaAtributoCreate(InventarioBase):
    nombre: str = Field(max_length=120)


class MetaAtributo(MetaAtributoCreate, table=True):
    __tablename__ = 'meta_atributos'  # type: ignore

    id: int = Field(primary_key=True)

    # Relationships
    movimientos: 'MovimientoPorMetaAtributo' = Relationship(back_populates='meta_atributo')


class MetaValorCreate(InventarioBase):
    valor: str = Field(max_length=120)


class MetaValor(MetaValorCreate, table=True):
    __tablename__ = 'meta_valores'  # type: ignore

    id: int = Field(primary_key=True)

    # Relationships
    movimientos: 'MovimientoPorMetaAtributo' = Relationship(back_populates='meta_valor')


# endregion metadatos


class EstadoVarianteCreate(InventarioBase):
    nombre: str = Field(max_length=50)
    descripcion: str | None = Field(sa_type=TEXT, default=None)


class EstadoVariante(EstadoVarianteCreate, table=True):
    __tablename__ = 'estados_variante'  # type: ignore

    id: int | None = Field(primary_key=True, sa_type=SMALLINT, default=None)

    # Relationships
    movimientos: list['Movimiento'] = Relationship(back_populates='estado_variante')


class ElementoCreate(InventarioBase):
    shopify_id: int = Field(sa_type=BIGINT)
    nombre: str = Field(max_length=120)
    tipo_medida_id: int = Field(foreign_key='inventario.tipos_medida.id', default=None, nullable=True)
    grupo_id: int = Field(foreign_key='inventario.grupos.id', default=None, nullable=True)
    descripcion: str | None = Field(sa_type=TEXT, default=None)
    fabricado: bool = Field(default=False)


class Elemento(ElementoCreate, table=True):
    __tablename__ = 'elementos'  # type: ignore

    id: int = Field(primary_key=True)

    # Relationships
    grupo: 'Grupo' = Relationship(back_populates='elementos')
    variantes: list['VarianteElemento'] = Relationship(back_populates='elemento')


class VarianteElementoCreate(InventarioBase):
    nombre: str = Field(max_length=120)
    sku: str | None = Field(max_length=120, default=None)
    shopify_id: int = Field(sa_type=BIGINT)
    elemento_id: int = Field(foreign_key='inventario.elementos.id', default=None, nullable=True)


class VarianteElemento(VarianteElementoCreate, table=True):
    __tablename__ = 'variantes_elemento'  # type: ignore

    id: int = Field(primary_key=True)

    # Relationships
    precios: list['PreciosPorVariante'] = Relationship(back_populates='variante')
    medidas: list['MedidasPorVariante'] = Relationship(back_populates='variante')
    componentes: list['ComponentesPorVariante'] = Relationship(
        back_populates='elemento',
        sa_relationship_kwargs={'foreign_keys': 'ComponentesPorVariante.variante_id'},
    )
    derivados: list['ComponentesPorVariante'] = Relationship(
        back_populates='elemento_padre',
        sa_relationship_kwargs={'foreign_keys': 'ComponentesPorVariante.variante_padre_id'},
    )
    movimientos: list['Movimiento'] = Relationship(back_populates='variante')
    elemento: 'Elemento' = Relationship(back_populates='variantes')


class ComponentesPorVarianteCreate(InventarioBase):
    variante_id: int = Field(foreign_key='inventario.variantes_elemento.id', default=None, nullable=True)
    variante_padre_id: int = Field(foreign_key='inventario.variantes_elemento.id', default=None, nullable=True)
    cantidad_elemento: int


class ComponentesPorVariante(ComponentesPorVarianteCreate, table=True):
    __tablename__ = 'componentes_por_variante'  # type: ignore
    id: int = Field(primary_key=True)

    # Relationships
    elemento: 'VarianteElemento' = Relationship(
        back_populates='componentes',
        sa_relationship_kwargs={'foreign_keys': 'ComponentesPorVariante.variante_id'},
    )
    elemento_padre: 'VarianteElemento' = Relationship(
        back_populates='derivados',
        sa_relationship_kwargs={'foreign_keys': 'ComponentesPorVariante.variante_padre_id'},
    )


if __name__ == '__main__':
    # for item, key in Elemento.model_fields.items():
    #     print(item, key)

    bodega = BodegaCreate(ubicacion='test', shopify_id=1)
    same_bodega = BodegaCreate(ubicacion='test', shopify_id=1)
    tipo_movimiento = TipoMovimientoCreate(**{'nombre': 'Entrada', 'comportamiento': 1})
    print(bodega == same_bodega)

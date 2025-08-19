# app/models/inventario.py
from datetime import datetime, date
from sqlmodel import Field, Relationship, SQLModel, SMALLINT, DATE, TEXT, BIGINT, TIMESTAMP


class InventarioBase(SQLModel):
    __table_args__ = {'schema': 'inventario'}


class BodegaUpdate(InventarioBase):
    ubicacion: str = Field(max_length=150)
    shopify_id: int = Field(sa_type=BIGINT)


class Bodega(BodegaUpdate, table=True):
    __tablename__ = 'bodegas'  # type: ignore

    id: int | None = Field(primary_key=True, sa_type=SMALLINT, default=None)

    # Relationships
    movimientos: list['Movimiento'] = Relationship(back_populates='bodega')


class GrupoUpdate(InventarioBase):
    nombre: str = Field(max_length=50)


class Grupo(GrupoUpdate, table=True):
    __tablename__ = 'grupos'  # type: ignore

    id: int | None = Field(primary_key=True, sa_type=SMALLINT, default=None)

    # Relationships
    elementos: list['Elemento'] = Relationship(back_populates='grupo')


class TiposMedidaUpdate(InventarioBase):
    nombre: str = Field(max_length=50)


class TiposMedida(TiposMedidaUpdate, table=True):
    __tablename__ = 'tipos_medida'  # type: ignore

    id: int | None = Field(primary_key=True, sa_type=SMALLINT, default=None)

    # Relationships
    medidas: list['Medida'] = Relationship(back_populates='tipo_medida')


class MedidaUpdate(InventarioBase):
    nombre: str = Field(max_length=50)
    nombre_largo: str = Field(max_length=50)
    tipo_medida_id: int = Field(foreign_key='inventario.tipos_medida.id')


class Medida(MedidaUpdate, table=True):
    __tablename__ = 'medidas'  # type: ignore

    id: int | None = Field(primary_key=True, sa_type=SMALLINT, default=None)

    # Relationships
    tipo_medida: 'TiposMedida' = Relationship(back_populates='medidas')
    variantes: list['MedidasPorVariante'] = Relationship(back_populates='medida')


class MedidasPorVarianteUpdate(InventarioBase):
    medida_id: int = Field(foreign_key='inventario.medidas.id')
    variante_id: int = Field(foreign_key='inventario.variantes_elemento.id')


class MedidasPorVariante(MedidasPorVarianteUpdate, table=True):
    __tablename__ = 'medidas_por_variante'  # type: ignore

    id: int | None = Field(primary_key=True, default=None)

    # Relationships
    medida: 'Medida' = Relationship(back_populates='variantes')
    variante: 'VarianteElemento' = Relationship(back_populates='medidas')


class TipoPrecioUpdate(InventarioBase):
    nombre: str = Field(max_length=50)
    descripcion: str | None = Field(sa_type=TEXT, default=None)


class TipoPrecio(TipoPrecioUpdate, table=True):
    __tablename__ = 'tipos_precio'  # type: ignore

    id: int | None = Field(primary_key=True, sa_type=SMALLINT, default=None)

    # Relationships
    precios: list['PreciosPorVariante'] = Relationship(back_populates='tipo_precio')


class PreciosPorVarianteUpdate(InventarioBase):
    variante_id: int = Field(foreign_key='inventario.variantes_elemento.id')
    tipo_precio_id: int = Field(foreign_key='inventario.tipos_precio.id')
    precio: float = Field(default=0.0)
    fecha: date = Field(sa_type=DATE, default_factory=date.today)


class PreciosPorVariante(PreciosPorVarianteUpdate, table=True):
    __tablename__ = 'precios_variante'  # type: ignore

    id: int | None = Field(primary_key=True, default=None)

    # Relationships
    tipo_precio: 'TipoPrecio' = Relationship(back_populates='precios')
    variante: 'VarianteElemento' = Relationship(back_populates='precios')


class TipoMovimientoUpdate(InventarioBase):
    nombre: str = Field(max_length=50)
    descripcion: str | None = Field(sa_type=TEXT, default=None)


class TipoMovimiento(TipoMovimientoUpdate, table=True):
    __tablename__ = 'tipos_movimiento'  # type: ignore

    id: int | None = Field(primary_key=True, sa_type=SMALLINT, default=None)

    # Relationships
    movimientos: list['Movimiento'] = Relationship(back_populates='tipo_movimiento')


class TipoSoporteUpdate(InventarioBase):
    nombre: str = Field(max_length=50)


class TipoSoporte(TipoSoporteUpdate, table=True):
    __tablename__ = 'tipos_soporte'  # type: ignore

    id: int | None = Field(primary_key=True, sa_type=SMALLINT, default=None)

    # Relationships
    movimientos: list['Movimiento'] = Relationship(back_populates='tipo_soporte')


class MovimientoUpdate(InventarioBase):
    tipo_movimiento_id: int | None = Field(foreign_key='inventario.tipos_movimiento.id', default=None)
    tipo_soporte_id: int | None = Field(foreign_key='inventario.tipos_soporte.id', default=None)
    variante_id: int | None = Field(foreign_key='inventario.variantes_elemento.id', default=None)
    estado_variante_id: int | None = Field(foreign_key='inventario.estados_variante.id', default=None)
    cantidad: int = Field(default=0)
    bodega_id: int = Field(foreign_key='inventario.bodegas.id', default=0)
    soporte_id: str | None = Field(sa_type=TEXT, default=None)
    nota: str | None = Field(sa_type=TEXT, default=None)
    fecha: datetime = Field(sa_type=TIMESTAMP, default_factory=datetime.now)


class Movimiento(MovimientoUpdate, table=True):
    id: int | None = Field(primary_key=True, default=None)

    # Relationships
    variante: 'VarianteElemento' = Relationship(back_populates='movimientos')
    estado_variante: 'EstadoVariante' = Relationship(back_populates='movimientos')
    bodega: 'Bodega' = Relationship(back_populates='movimientos')
    tipo_movimiento: 'TipoMovimiento' = Relationship(back_populates='movimientos')
    tipo_soporte: 'TipoSoporte' = Relationship(back_populates='movimientos')


class EstadoVarianteUpdate(InventarioBase):
    nombre: str = Field(max_length=50)
    descripcion: str | None = Field(sa_type=TEXT, default=None)


class EstadoVariante(EstadoVarianteUpdate, table=True):
    __tablename__ = 'estados_variante'  # type: ignore

    id: int | None = Field(primary_key=True, sa_type=SMALLINT, default=None)

    # Relationships
    movimientos: list['Movimiento'] = Relationship(back_populates='estado_variante')


class ElementoUpdate(InventarioBase):
    shopify_id: int = Field(sa_type=BIGINT)
    nombre: str = Field(max_length=120)
    tipo_medida_id: int = Field(foreign_key='inventario.tipos_medida.id')
    grupo_id: int | None = Field(foreign_key='inventario.grupos.id')
    descripcion: str | None = Field(sa_type=TEXT, default=None)
    fabricado: bool = Field(default=False)


class Elemento(ElementoUpdate, table=True):
    __tablename__ = 'elementos'  # type: ignore

    id: int | None = Field(primary_key=True, default=None)

    # Relationships
    grupo: 'Grupo' = Relationship(back_populates='elementos')
    variantes: list['VarianteElemento'] = Relationship(back_populates='elemento')


class VarianteElementoUpdate(InventarioBase):
    nombre: str = Field(max_length=120)
    sku: str | None = Field(max_length=120, default=None)
    shopify_id: int = Field(sa_type=BIGINT)
    elemento_id: int = Field(foreign_key='inventario.elementos.id')


class VarianteElemento(VarianteElementoUpdate, table=True):
    __tablename__ = 'variantes_elemento'  # type: ignore

    id: int | None = Field(primary_key=True, default=None)

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


class ComponentesPorVarianteUpdate(InventarioBase):
    variante_id: int = Field(foreign_key='inventario.variantes_elemento.id')
    variante_padre_id: int = Field(foreign_key='inventario.variantes_elemento.id')
    cantidad_elemento: int


class ComponentesPorVariante(ComponentesPorVarianteUpdate, table=True):
    __tablename__ = 'componentes_por_variante'  # type: ignore
    id: int | None = Field(primary_key=True)

    # Relationships
    elemento: 'VarianteElemento' = Relationship(
        back_populates='componentes',
        sa_relationship_kwargs={'foreign_keys': 'ComponentesPorVariante.variante_id'},
    )
    elemento_padre: 'VarianteElemento' = Relationship(
        back_populates='derivados',
        sa_relationship_kwargs={'foreign_keys': 'ComponentesPorVariante.variante_padre_id'},
    )

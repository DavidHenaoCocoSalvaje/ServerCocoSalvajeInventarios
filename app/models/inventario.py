# app/models/inventario.py
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel, SMALLINT, DATE, TEXT


class Bodega(SQLModel, table=True):
    __tablename__ = "bodegas_inventario"  # type: ignore

    id: int = Field(primary_key=True, sa_type=SMALLINT)
    nombre: str = Field(max_length=50)
    ubicacion: str = Field(max_length=150)

    # Relationships
    elementos: list["Elemento"] = Relationship(back_populates="bodega_inventario")
    elementos_compuestos: list["ElementoCompuesto"] = Relationship(
        back_populates="bodega_inventario"
    )


class Grupo(SQLModel, table=True):
    __tablename__ = "grupos_inventario"  # type: ignore

    id: int = Field(primary_key=True, sa_type=SMALLINT)
    nombre: str = Field(max_length=50)

    # Relationships
    elementos: list["Elemento"] = Relationship(back_populates="grupo_inventario")
    elementos_compuestos: list["ElementoCompuesto"] = Relationship(
        back_populates="grupo_inventario"
    )


class UnidadMedida(SQLModel, table=True):
    __tablename__ = "unidades_medida"  # type: ignore

    id: int = Field(sa_type=SMALLINT, primary_key=True)
    nombre: str = Field(max_length=50)
    tipo_unidad_medida: str = Field(max_length=50)

    # Relationships
    variantes_um_cantidad: list["VarianteElemento"] = Relationship(
        back_populates="unidad_medida_cantidad",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoInventario.unidad_medida_cantidad_id"
        },
    )
    variantes_um_peso: list["VarianteElemento"] = Relationship(
        back_populates="unidad_medida_peso",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoInventario.unidad_medida_peso_id"
        },
    )
    variantes_um_volumen: list["VarianteElemento"] = Relationship(
        back_populates="unidad_medida_volumen",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoInventario.unidad_medida_volumen_id"
        },
    )

    elementos_compuestos_cantidad: list["ElementoCompuesto"] = Relationship(
        back_populates="unidad_medida_cantidad",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoCompuestoInventario.unidad_medida_cantidad_id"
        },
    )
    elementos_compuestos_peso: list["ElementoCompuesto"] = Relationship(
        back_populates="unidad_medida_peso",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoCompuestoInventario.unidad_medida_peso_id"
        },
    )
    elementos_compuestos_volumen: list["ElementoCompuesto"] = Relationship(
        back_populates="unidad_medida_volumen",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoCompuestoInventario.unidad_medida_volumen_id"
        },
    )


class TipoEstadoElemento(SQLModel, table=True):
    __tablename__ = "tipos_estado_elemento_inventario"  # type: ignore

    id: int = Field(sa_type=SMALLINT, primary_key=True)
    nombre: str = Field(max_length=50)

    # Relationships
    estados_elemento: list["EstadoElemento"] = Relationship(
        back_populates="tipo_estado"
    )


class EstadoElemento(SQLModel, table=True):
    __tablename__ = "estados_elemento_inventario"  # type: ignore

    id: int = Field(sa_type=SMALLINT, primary_key=True)
    tipo_estado_id: int = Field(foreign_key="tipos_estado_elemento_inventario.id")
    elemento_id: int | None = Field(foreign_key="elementos_inventario.id", default=None)
    elemento_compuesto_id: int | None = Field(
        foreign_key="elementos_compuestos_inventario.id", default=None
    )
    fecha: datetime = datetime.now()

    # Relationships
    tipo_estado: "TipoEstadoElemento" = Relationship(back_populates="estados_elemento")
    elemento: "Elemento" = Relationship(back_populates="estados_elemento")
    elemento_compuesto: "ElementoCompuesto" = Relationship(
        back_populates="estados_elemento"
    )


class TipoPrecioVariante(SQLModel, table=True):
    __tablename__ = "tipos_precio_elemento_inventario"  # type: ignore

    id: int = Field(sa_type=SMALLINT, primary_key=True)
    nombre: str = Field(max_length=50)

    # Relationships
    precios: list["PrecioVariante"] = Relationship(back_populates="tipo_precio")


class PrecioVariante(SQLModel, table=True):
    __tablename__ = "precios_variante_inventario"  # type: ignore

    id: int = Field(primary_key=True)
    variante_id: int = Field(foreign_key="variantes_elemento_inventario.id")
    precio: float
    tipo_precio_id: int = Field(foreign_key="tipos_precio_elemento_inventario.id")
    fini: datetime = Field(sa_type=DATE)
    ffin: datetime | None = Field(sa_type=DATE, default=None)

    # Relationships
    tipo_precio: "TipoPrecioVariante" = Relationship(back_populates="precios")
    variantes: "VarianteElemento" = Relationship(back_populates="precios")


class TipoMovimiento(SQLModel, table=True):
    __tablename__ = "tipos_movimiento_inventario"  # type: ignore

    id: int = Field(sa_type=SMALLINT, primary_key=True)
    nombre: str = Field(max_length=50)

    # Relationships
    movimientos: list["Movimiento"] = Relationship(back_populates="tipo_movimiento")


class Movimiento(SQLModel, table=True):
    __tablename__ = "movimientos_inventario"  # type: ignore

    id: int = Field(primary_key=True)
    nombre: str = Field(max_length=120)
    cantidad: int
    elemento_id: int | None = Field(foreign_key="elementos_inventario.id", default=None)
    elemento_compuesto_id: int | None = Field(
        foreign_key="elementos_compuestos_inventario.id", default=None
    )
    bodega_id: int = Field(foreign_key="bodegas_inventario.id")
    fecha: datetime = datetime.now()
    tipo_movimiento_id: int = Field(foreign_key="tipos_movimiento_inventario.id")

    # Relationships
    elemento: "Elemento" = Relationship(back_populates="movimientos_inventario")
    elemento_compuesto: "ElementoCompuesto" = Relationship(
        back_populates="movimientos_inventario"
    )
    bodega: "Bodega" = Relationship(back_populates="movimientos_inventario")
    tipo_movimiento: "TipoMovimiento" = Relationship(
        back_populates="movimientos_inventario"
    )


class Elemento(SQLModel, table=True):
    __tablename__ = "elementos_inventario"  # type: ignore

    id: int = Field(primary_key=True)
    nombre: str = Field(max_length=120)
    bodega_id: int | None = Field(foreign_key="bodegas_inventario.id")
    grupo_id: int | None = Field(foreign_key="grupos_inventario.id")
    descripcion: str | None = Field(sa_type=TEXT, max_length=250, default=None)
    estado_elemento_id: int = Field(foreign_key="estados_elemento_inventario.id")

    # Relationships
    bodega: "Bodega" = Relationship(back_populates="elementos_inventario")
    grupo: "Grupo" = Relationship(back_populates="elementos_inventario")
    estado_elemento: "EstadoElemento" = Relationship(
        back_populates="elementos_inventario"
    )
    movimientos: list["Movimiento"] = Relationship(back_populates="elemento_inventario")
    variantes: list["VarianteElemento"] = Relationship(back_populates="elemento")


class ElementoCompuesto(SQLModel, table=True):
    __tablename__ = "elementos_compuestos_inventario"  # type: ignore

    id: int = Field(primary_key=True)
    nombre: str = Field(max_length=120)
    bodega_id: int | None = Field(foreign_key="bodegas_inventario.id")
    grupo_id: int | None = Field(foreign_key="grupos_inventario.id", default=None)
    descripcion: str | None = Field(sa_type=TEXT, max_length=250, default=None)
    estado_elemento_id: int = Field(foreign_key="estados_elemento_inventario.id")
    fecha: datetime = datetime.now()

    # Relationships
    elementos: list["ElementosPorElementoCompuesto"] = Relationship(
        back_populates="elemento_compuesto_inventario"
    )
    bodega: "Bodega" = Relationship(back_populates="elementos_compuestos_inventario")
    grupo: "Grupo" = Relationship(back_populates="elementos_compuestos_inventario")
    estado_elemento: "EstadoElemento" = Relationship(
        back_populates="elementos_compuestos_inventario"
    )
    movimientos: list["Movimiento"] = Relationship(
        back_populates="elemento_compuesto_inventario"
    )
    variantes: list["VarianteElemento"] = Relationship(
        back_populates="elemento_compuesto"
    )


class VarianteElemento(SQLModel, table=True):
    __tablename__ = "variantes_elemento_inventario"  # type: ignore

    id: int = Field(primary_key=True)
    elemento_id: int = Field(foreign_key="elementos_inventario.id", default=None)
    elemento_compuesto_id: int | None = Field(
        foreign_key="elementos_compuestos_inventario.id", default=None
    )
    cantidad: int | None = None
    unidad_medida_cantidad_id: int | None = Field(
        foreign_key="unidades_medida.id", default=None
    )
    peso: int | None = None
    unidad_medida_peso_id: int | None = Field(
        foreign_key="unidades_medida.id", default=None
    )
    volumen: int | None = None
    unidad_medida_volumen_id: int | None = Field(
        foreign_key="unidades_medida.id", default=None
    )

    # Relationships
    precios: list["PrecioVariante"] = Relationship(back_populates="variante_inventario")
    elemento: "Elemento" = Relationship(back_populates="variantes_inventario")
    elemento_compuesto: "ElementoCompuesto" = Relationship(
        back_populates="variantes_inventario"
    )
    unidad_medida_cantidad: "UnidadMedida" = Relationship(
        back_populates="variantes_um_cantidad",
        sa_relationship_kwargs={
            "foreign_keys": "VarianteElemento.unidad_medida_cantidad_id"
        },
    )
    unidad_medida_peso: "UnidadMedida" = Relationship(
        back_populates="variantes_um_peso",
        sa_relationship_kwargs={
            "foreign_keys": "VarianteElemento.unidad_medida_peso_id"
        },
    )
    unidad_medida_volumen: "UnidadMedida" = Relationship(
        back_populates="variantes_um_volumen",
        sa_relationship_kwargs={
            "foreign_keys": "VarianteElemento.unidad_medida_volumen_id"
        },
    )


class ElementosPorElementoCompuesto(SQLModel, table=True):
    __tablename__ = "elementos_por_elemento_compuesto_inventario"  # type: ignore
    # Añadidos primary_key para la tabla de enlace
    elemento_compuesto_id: int = Field(
        foreign_key="elementos_compuestos_inventario.id", primary_key=True
    )
    elemento_id: int = Field(foreign_key="elementos_inventario.id", primary_key=True)

    # Relationships
    variante: "Elemento" = Relationship(  # Usar cadena
        back_populates="elementos_compuestos_inventario"
    )
    elemento_compuesto: "ElementoCompuesto" = Relationship(  # Usar cadena
        back_populates="elementos_inventario"
    )

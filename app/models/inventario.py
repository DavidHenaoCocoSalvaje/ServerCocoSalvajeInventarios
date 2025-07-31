# app/models/inventario.py
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel, SMALLINT, DATE, TEXT


class Bodega(SQLModel, table=True):
    __tablename__ = "bodegas_inventario"  # type: ignore

    id: int = Field(primary_key=True, sa_type=SMALLINT)
    nombre: str = Field(max_length=50)
    ubicacion: str = Field(max_length=150)

    # Relationships
    elementos: list["Elemento"] = Relationship(back_populates="bodega")
    movimientos: list["Movimiento"] = Relationship(back_populates="bodega")
    elementos_compuestos: list["ElementoCompuesto"] = Relationship(
        back_populates="bodega"
    )


class Grupo(SQLModel, table=True):
    __tablename__ = "grupos_inventario"  # type: ignore

    id: int = Field(primary_key=True, sa_type=SMALLINT)
    nombre: str = Field(max_length=50)

    # Relationships
    elementos: list["Elemento"] = Relationship(back_populates="grupo")
    elementos_compuestos: list["ElementoCompuesto"] = Relationship(
        back_populates="grupo"
    )


class UnidadMedida(SQLModel, table=True):
    __tablename__ = "unidades_medida"  # type: ignore

    id: int = Field(sa_type=SMALLINT, primary_key=True)
    nombre: str = Field(max_length=50)
    tipo_unidad_medida: str = Field(max_length=50)

    # Relationships
    elementos_cantidad: list["Elemento"] = Relationship(
        back_populates="unidad_medida_cantidad",
        sa_relationship_kwargs={"foreign_keys": "Elemento.unidad_medida_cantidad_id"},
    )
    elementos_peso: list["Elemento"] = Relationship(
        back_populates="unidad_medida_peso",
        sa_relationship_kwargs={"foreign_keys": "Elemento.unidad_medida_peso_id"},
    )
    elementos_volumen: list["Elemento"] = Relationship(
        back_populates="unidad_medida_volumen",
        sa_relationship_kwargs={"foreign_keys": "Elemento.unidad_medida_volumen_id"},
    )

    elementos_compuestos_cantidad: list["ElementoCompuesto"] = Relationship(
        back_populates="unidad_medida_cantidad",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoCompuesto.unidad_medida_cantidad_id"
        },
    )
    elementos_compuestos_peso: list["ElementoCompuesto"] = Relationship(
        back_populates="unidad_medida_peso",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoCompuesto.unidad_medida_peso_id"
        },
    )
    elementos_compuestos_volumen: list["ElementoCompuesto"] = Relationship(
        back_populates="unidad_medida_volumen",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoCompuesto.unidad_medida_volumen_id"
        },
    )


class TipoPrecioVariante(SQLModel, table=True):
    __tablename__ = "tipos_precio_elemento_inventario"  # type: ignore

    id: int = Field(sa_type=SMALLINT, primary_key=True)
    nombre: str = Field(max_length=50)

    # Relationships
    precios: list["PreciosPorVariante"] = Relationship(back_populates="tipo_precio")


class PreciosPorVariante(SQLModel, table=True):
    __tablename__ = "precios_variante_inventario"  # type: ignore

    id: int = Field(primary_key=True)
    variante_id: int = Field(foreign_key="variantes_elemento_inventario.id")
    tipo_precio_id: int = Field(foreign_key="tipos_precio_elemento_inventario.id")
    precio: float
    fecha: datetime = Field(sa_type=DATE)

    # Relationships
    tipo_precio: "TipoPrecioVariante" = Relationship(back_populates="precios")
    variante: "VarianteElemento" = Relationship(back_populates="precios")


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
    elemento: "Elemento" = Relationship(back_populates="movimientos")
    elemento_compuesto: "ElementoCompuesto" = Relationship(back_populates="movimientos")
    bodega: "Bodega" = Relationship(back_populates="movimientos")
    tipo_movimiento: "TipoMovimiento" = Relationship(back_populates="movimientos")


class EstadoElemento(SQLModel, table=True):
    __tablename__ = "estados_elemento_inventario"  # type: ignore

    id: int = Field(sa_type=SMALLINT, primary_key=True)
    nombre: str = Field(max_length=50)
    descripcion: str | None = Field(sa_type=TEXT, default=None)

    # Relationships
    estados_elemento: list["EstadoPorElemento"] = Relationship(
        back_populates="estado_elemento"
    )


class Elemento(SQLModel, table=True):
    __tablename__ = "elementos_inventario"  # type: ignore

    id: int = Field(primary_key=True)
    nombre: str = Field(max_length=120)
    unidad_medida_cantidad_id: int | None = Field(
        foreign_key="unidades_medida.id", default=None
    )
    unidad_medida_peso_id: int | None = Field(
        foreign_key="unidades_medida.id", default=None
    )
    unidad_medida_volumen_id: int | None = Field(
        foreign_key="unidades_medida.id", default=None
    )
    bodega_id: int | None = Field(foreign_key="bodegas_inventario.id")
    grupo_id: int | None = Field(foreign_key="grupos_inventario.id")
    descripcion: str | None = Field(sa_type=TEXT, max_length=250, default=None)

    # Relationships
    bodega: "Bodega" = Relationship(back_populates="elementos")
    grupo: "Grupo" = Relationship(
        back_populates="elementos",
    )
    unidad_medida_cantidad: "UnidadMedida" = Relationship(
        back_populates="elementos_cantidad",
        sa_relationship_kwargs={"foreign_keys": "Elemento.unidad_medida_cantidad_id"},
    )
    unidad_medida_peso: "UnidadMedida" = Relationship(
        back_populates="elementos_peso",
        sa_relationship_kwargs={"foreign_keys": "Elemento.unidad_medida_peso_id"},
    )
    unidad_medida_volumen: "UnidadMedida" = Relationship(
        back_populates="elementos_volumen",
        sa_relationship_kwargs={"foreign_keys": "Elemento.unidad_medida_volumen_id"},
    )
    estados_elemento: list["EstadoPorElemento"] = Relationship(
        back_populates="elemento",
    )
    movimientos: list["Movimiento"] = Relationship(back_populates="elemento")
    variantes: list["VarianteElemento"] = Relationship(back_populates="elemento")


class ElementoCompuesto(SQLModel, table=True):
    __tablename__ = "elementos_compuestos_inventario"  # type: ignore

    id: int = Field(primary_key=True)
    shopify_id: int | None
    nombre: str = Field(max_length=120)
    unidad_medida_cantidad_id: int | None = Field(
        foreign_key="unidades_medida.id", default=None
    )
    unidad_medida_peso_id: int | None = Field(
        foreign_key="unidades_medida.id", default=None
    )
    unidad_medida_volumen_id: int | None = Field(
        foreign_key="unidades_medida.id", default=None
    )
    bodega_id: int | None = Field(foreign_key="bodegas_inventario.id")
    grupo_id: int | None = Field(foreign_key="grupos_inventario.id", default=None)
    descripcion: str | None = Field(sa_type=TEXT, max_length=250, default=None)
    fecha: datetime = datetime.now()

    # Relationships
    bodega: "Bodega" = Relationship(back_populates="elementos_compuestos")
    grupo: "Grupo" = Relationship(back_populates="elementos_compuestos")
    unidad_medida_cantidad: "UnidadMedida" = Relationship(
        back_populates="elementos_compuestos_cantidad",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoCompuesto.unidad_medida_cantidad_id"
        },
    )
    unidad_medida_peso: "UnidadMedida" = Relationship(
        back_populates="elementos_compuestos_peso",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoCompuesto.unidad_medida_peso_id"
        },
    )
    unidad_medida_volumen: "UnidadMedida" = Relationship(
        back_populates="elementos_compuestos_volumen",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoCompuesto.unidad_medida_volumen_id"
        },
    )
    estados_elemento: list["EstadoPorElemento"] = Relationship(
        back_populates="elemento_compuesto"
    )
    movimientos: list["Movimiento"] = Relationship(back_populates="elemento_compuesto")
    variantes: list["VarianteElemento"] = Relationship(
        back_populates="elemento_compuesto"
    )
    componentes: list["VariantesPorElementoCompuesto"] = Relationship(
        back_populates="elemento_compuesto"
    )


class VarianteElemento(SQLModel, table=True):
    __tablename__ = "variantes_elemento_inventario"  # type: ignore

    id: int = Field(primary_key=True)
    elemento_id: int = Field(foreign_key="elementos_inventario.id", default=None)
    elemento_compuesto_id: int | None = Field(
        foreign_key="elementos_compuestos_inventario.id", default=None
    )
    peso: int | None = None
    volumen: int | None = None

    # Relationships
    precios: list["PreciosPorVariante"] = Relationship(back_populates="variante")
    elementos_compuestos: list["VariantesPorElementoCompuesto"] = Relationship(
        back_populates="variante"
    )
    elemento: "Elemento" = Relationship(back_populates="variantes")
    elemento_compuesto: "ElementoCompuesto" = Relationship(back_populates="variantes")


class VariantesPorElementoCompuesto(SQLModel, table=True):
    __tablename__ = "variantes_por_elemento_compuesto_inventario"  # type: ignore
    id: int = Field(primary_key=True)
    elemento_compuesto_id: int = Field(foreign_key="elementos_compuestos_inventario.id")
    variante_elemento_id: int = Field(foreign_key="variantes_elemento_inventario.id")

    # Relationships
    elemento_compuesto: "ElementoCompuesto" = Relationship(back_populates="componentes")
    variante: "VarianteElemento" = Relationship(back_populates="elementos_compuestos")


class EstadoPorElemento(SQLModel, table=True):
    __tablename__ = "estados_por_elemento_inventario"  # type: ignore

    id: int = Field(primary_key=True)
    estado_elemento_id: int = Field(foreign_key="estados_elemento_inventario.id")
    elemento_id: int | None = Field(foreign_key="elementos_inventario.id", default=None)
    elemento_compuesto_id: int | None = Field(
        foreign_key="elementos_compuestos_inventario.id", default=None
    )
    fecha: datetime = datetime.now()

    # Relationships
    estado_elemento: "EstadoElemento" = Relationship(back_populates="estados_elemento")
    elemento: "Elemento" = Relationship(
        back_populates="estados_elemento",
    )
    elemento_compuesto: "ElementoCompuesto" = Relationship(
        back_populates="estados_elemento",
    )

# app/models/inventario.py
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel, SMALLINT, DATE, TEXT


class BodegaInventarioResponse(SQLModel):
    id: int = Field(primary_key=True, sa_type=SMALLINT)
    nombre: str = Field(max_length=50)
    ubicacion: str = Field(max_length=150)


class BodegaInventario(
    BodegaInventarioResponse, table=True
):  # Cuando se utiliza table=True, no se respeta el orden del modelo, por eso se define con herencia
    __tablename__ = "bodegas_inventario"  # type: ignore

    # Relationships
    elementos_inventario: list["ElementoInventario"] = Relationship(
        back_populates="bodega_inventario"
    )
    elementos_compuestos_inventario: list["ElementoCompuestoInventario"] = Relationship(
        back_populates="bodega_inventario"
    )


class GrupoInventarioResponse(SQLModel):
    id: int = Field(primary_key=True, sa_type=SMALLINT)
    nombre: str = Field(max_length=50)


class GrupoInventario(GrupoInventarioResponse, table=True):
    __tablename__ = "grupos_inventario"  # type: ignore

    # Relationships
    elementos_inventario: list["ElementoInventario"] = Relationship(
        back_populates="grupo_inventario"
    )
    elementos_compuestos_inventario: list["ElementoCompuestoInventario"] = Relationship(
        back_populates="grupo_inventario"
    )


class UnidadMedidaResponse(SQLModel):
    id: int = Field(sa_type=SMALLINT, primary_key=True)
    nombre: str = Field(max_length=50)
    tipo_unidad_medida: str = Field(max_length=50)


class UnidadMedida(UnidadMedidaResponse, table=True):
    __tablename__ = "unidades_medida"  # type: ignore

    # Relationships
    elementos_inventario_cantidad: list["ElementoInventario"] = Relationship(
        back_populates="unidad_medida_cantidad",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoInventario.unidad_medida_cantidad_id"
        },
    )
    elementos_inventario_peso: list["ElementoInventario"] = Relationship(
        back_populates="unidad_medida_peso",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoInventario.unidad_medida_peso_id"
        },
    )
    elementos_inventario_volumen: list["ElementoInventario"] = Relationship(
        back_populates="unidad_medida_volumen",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoInventario.unidad_medida_volumen_id"
        },
    )
    elementos_compuestos_inventario_cantidad: list["ElementoCompuestoInventario"] = (
        Relationship(
            back_populates="unidad_medida_cantidad",
            sa_relationship_kwargs={
                "foreign_keys": "ElementoCompuestoInventario.unidad_medida_cantidad_id"
            },
        )
    )
    elementos_compuestos_inventario_peso: list["ElementoCompuestoInventario"] = (
        Relationship(
            back_populates="unidad_medida_peso",
            sa_relationship_kwargs={
                "foreign_keys": "ElementoCompuestoInventario.unidad_medida_peso_id"
            },
        )
    )
    elementos_compuestos_inventario_volumen: list["ElementoCompuestoInventario"] = (
        Relationship(
            back_populates="unidad_medida_volumen",
            sa_relationship_kwargs={
                "foreign_keys": "ElementoCompuestoInventario.unidad_medida_volumen_id"
            },
        )
    )


class EstadoElementoInventarioResponse(SQLModel):
    id: int = Field(sa_type=SMALLINT, primary_key=True)
    nombre: str = Field(max_length=50)


class EstadoElementoInventario(EstadoElementoInventarioResponse, table=True):
    __tablename__ = "estados_elemento_inventario"  # type: ignore

    # Relationships
    elementos_inventario: list["ElementoInventario"] = Relationship(
        back_populates="estado_elemento"
    )
    elementos_compuestos_inventario: list["ElementoCompuestoInventario"] = Relationship(
        back_populates="estado_elemento"
    )


class ElementoInventarioResponse(SQLModel):
    id: int = Field(primary_key=True)
    nombre: str = Field(max_length=120)
    bodega_inventario_id: int | None = Field(foreign_key="bodegas_inventario.id")
    grupo_inventario_id: int | None = Field(foreign_key="grupos_inventario.id")
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
    descripcion: str | None = Field(sa_type=TEXT, max_length=250, default=None)
    estado_elemento_id: int = Field(foreign_key="estados_elemento_inventario.id")
    created_at: datetime = Field(default=datetime.now)
    usuario_id: int | None = Field(foreign_key="usuarios.id", default=None)


class ElementoInventario(ElementoInventarioResponse, table=True):
    __tablename__ = "elementos_inventario"  # type: ignore

    # Relationships
    precios: list["PrecioElementoInventario"] = Relationship(
        back_populates="elemento_inventario"
    )
    elementos_compuestos_inventario: list["ElementosPorElementoCompuestoInventario"] = (
        Relationship(back_populates="elemento_inventario")
    )
    unidad_medida_cantidad: "UnidadMedida" = Relationship(
        back_populates="elementos_inventario_cantidad",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoInventario.unidad_medida_cantidad_id"
        },
    )
    unidad_medida_peso: "UnidadMedida" = Relationship(
        back_populates="elementos_inventario_peso",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoInventario.unidad_medida_peso_id"
        },
    )
    unidad_medida_volumen: "UnidadMedida" = Relationship(
        back_populates="elementos_inventario_volumen",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoInventario.unidad_medida_volumen_id"
        },
    )
    bodega_inventario: "BodegaInventario" = Relationship(
        back_populates="elementos_inventario"
    )
    grupo_inventario: "GrupoInventario" = Relationship(
        back_populates="elementos_inventario"
    )
    estado_elemento: "EstadoElementoInventario" = Relationship(
        back_populates="elementos_inventario"
    )
    usuario: "UsuarioDB" = Relationship(back_populates="elementos_inventario")  # type: ignore # noqa: F821
    movimientos_inventario: list["MovimientoInventario"] = Relationship(
        back_populates="elemento_inventario"
    )


class ElementoCompuestoInventarioResponse(SQLModel):
    id: int = Field(primary_key=True)
    nombre: str = Field(max_length=120)
    bodega_inventario_id: int | None = Field(foreign_key="bodegas_inventario.id")
    grupo_inventario_id: int | None = Field(
        foreign_key="grupos_inventario.id", default=None
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
    descripcion: str | None = Field(sa_type=TEXT, max_length=250, default=None)
    estado_elemento_id: int = Field(foreign_key="estados_elemento_inventario.id")
    created_at: datetime = Field(default=datetime.now)
    usuario_id: int | None = Field(foreign_key="usuarios.id", default=None)


class ElementoCompuestoInventario(ElementoCompuestoInventarioResponse, table=True):
    __tablename__ = "elementos_compuestos_inventario"  # type: ignore

    # Relationships
    elementos_inventario: list["ElementosPorElementoCompuestoInventario"] = (
        Relationship(back_populates="elemento_compuesto_inventario")
    )
    unidad_medida_cantidad: "UnidadMedida" = Relationship(
        back_populates="elementos_compuestos_inventario_cantidad",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoCompuestoInventario.unidad_medida_cantidad_id"
        },
    )
    unidad_medida_peso: "UnidadMedida" = Relationship(
        back_populates="elementos_compuestos_inventario_peso",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoCompuestoInventario.unidad_medida_peso_id"
        },
    )
    unidad_medida_volumen: "UnidadMedida" = Relationship(
        back_populates="elementos_compuestos_inventario_volumen",
        sa_relationship_kwargs={
            "foreign_keys": "ElementoCompuestoInventario.unidad_medida_volumen_id"
        },
    )
    bodega_inventario: "BodegaInventario" = Relationship(
        back_populates="elementos_compuestos_inventario"
    )
    grupo_inventario: "GrupoInventario" = Relationship(
        back_populates="elementos_compuestos_inventario"
    )
    estado_elemento: "EstadoElementoInventario" = Relationship(
        back_populates="elementos_compuestos_inventario"
    )
    usuario: "UsuarioDB" = Relationship(  # type: ignore # noqa: F821
        back_populates="elementos_compuestos_inventario"
    )
    movimientos_inventario: list["MovimientoInventario"] = Relationship(
        back_populates="elemento_compuesto_inventario"
    )


class ElementosPorElementoCompuestoInventario(SQLModel, table=True):
    __tablename__ = "elementos_inventario_por_elemento_compuesto"  # type: ignore
    # Añadidos primary_key para la tabla de enlace
    elemento_compuesto_inventario_id: int = Field(
        foreign_key="elementos_compuestos_inventario.id", primary_key=True
    )
    elemento_inventario_id: int = Field(
        foreign_key="elementos_inventario.id", primary_key=True
    )

    # Relationships
    elemento_inventario: "ElementoInventario" = Relationship(  # Usar cadena
        back_populates="elementos_compuestos_inventario"
    )
    elemento_compuesto_inventario: "ElementoCompuestoInventario" = (
        Relationship(  # Usar cadena
            back_populates="elementos_inventario"
        )
    )


class TipoPrecioElementoInventarioResponse(SQLModel):
    id: int = Field(sa_type=SMALLINT, primary_key=True)
    nombre: str = Field(max_length=50)


class TipoPrecioElementoInventario(TipoPrecioElementoInventarioResponse, table=True):
    __tablename__ = "tipos_precio_elemento_inventario"  # type: ignore

    # Relationships
    precios: list["PrecioElementoInventario"] = Relationship(
        back_populates="tipo_precio"
    )


class PrecioElementoInventarioResponse(SQLModel):
    id: int = Field(primary_key=True)
    elemento_inventario_id: int = Field(foreign_key="elementos_inventario.id")
    precio: float
    tipo_precio_id: int = Field(foreign_key="tipos_precio_elemento_inventario.id")
    fini: datetime = Field(sa_type=DATE)
    ffin: datetime | None = Field(sa_type=DATE, default=None)


class PrecioElementoInventario(PrecioElementoInventarioResponse, table=True):
    __tablename__ = "precios_elemento_inventario"  # type: ignore

    # Relationships
    elemento_inventario: "ElementoInventario" = Relationship(back_populates="precios")
    tipo_precio: "TipoPrecioElementoInventario" = Relationship(back_populates="precios")


class MovimientoInventarioResponse(SQLModel):
    id: int = Field(primary_key=True)
    nombre: str = Field(max_length=120)
    cantidad: int
    elemento_inventario_id: int | None = Field(
        foreign_key="elementos_inventario.id", default=None
    )
    elemento_compuesto_inventario_id: int | None = Field(
        foreign_key="elementos_compuestos_inventario.id", default=None
    )
    tipo_movimiento_id: int = Field(foreign_key="tipos_movimiento_inventario.id")
    created_at: datetime = Field(default=datetime.now)
    usuario_id: int | None = Field(foreign_key="usuarios.id", default=None)


class MovimientoInventario(MovimientoInventarioResponse, table=True):
    __tablename__ = "movimientos_inventario"  # type: ignore

    # Relationships
    elemento_inventario: "ElementoInventario" = Relationship(
        back_populates="movimientos_inventario"
    )
    elemento_compuesto_inventario: "ElementoCompuestoInventario" = Relationship(
        back_populates="movimientos_inventario"
    )
    tipo_movimiento: "TipoMovimientoInventario" = Relationship(
        back_populates="movimientos_inventario"
    )
    usuario: "UsuarioDB" = Relationship(back_populates="movimientos_inventario")  # type: ignore  # noqa: F821


class TipoMovimientoInventarioResponse(SQLModel):
    id: int = Field(sa_type=SMALLINT, primary_key=True)
    nombre: str = Field(max_length=50)


class TipoMovimientoInventario(TipoMovimientoInventarioResponse, table=True):
    __tablename__ = "tipos_movimiento_inventario"  # type: ignore

    # Relationships
    movimientos_inventario: list["MovimientoInventario"] = Relationship(
        back_populates="tipo_movimiento"
    )

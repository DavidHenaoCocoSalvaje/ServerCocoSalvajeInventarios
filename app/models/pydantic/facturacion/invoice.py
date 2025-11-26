from app.models.pydantic.base import Base
from pydantic import Field

class EsquemaTributario(Base):
    id: str = ""
    name: str = ""

class Emisor(Base):
    razonsocial: str = ""
    nombrecomercial: str = ""
    telefono: str = ""
    email: str = ""
    documento: str = ""
    digitoverificacion: str = ""
    tipodocumento: str = ""
    responsabilidadesfiscales: str = ""
    nameresponsabilidadesfiscales: str = ""
    esquematributario: EsquemaTributario = Field(default_factory=EsquemaTributario)
    pais: str = ""
    departamento: str = ""
    ciudad: str = ""
    address: str = ""

class Receptor(Base):
    razonsocial: str = ""
    documento: str = ""

class Impuesto(Base):
    id: str = ""
    impuesto: str = ""
    # Solicitado: Usar float por semántica de nombre, aunque venga str en JSON
    base: float = 0.0
    porcentaje: float = 0.0
    monto: float = 0.0

class LineItem(Base):
    nombre: str = ""
    cantidad: str = ""
    valorunitario: str = ""
    total: float = 0.0
    unidad: str = ""
    cantidadbase: str = ""
    # Ahora tipamos la lista con el modelo Impuesto
    impuestos: list[Impuesto] = Field(default_factory=list)
    descripcion: str = ""
    nombre_unidad: str = ""
    inventario: str = ""
    cuenta: str = ""
    kg: str = ""
    und: str = ""

class Invoice(Base):
    id: str = ""
    uuid: str = ""
    fecha: str = ""
    emisor: Emisor = Field(default_factory=Emisor)
    receptor: Receptor = Field(default_factory=Receptor)
    moneda: str = ""
    subtotal: str = ""
    total: float = 0.0
    descuento: int = 0
    # Ahora tipamos la lista con el modelo Impuesto
    impuestos: list[Impuesto] = Field(default_factory=list)
    lineitems: list[LineItem] = Field(default_factory=list)
    pago: str = ""
    fechapago: str = ""
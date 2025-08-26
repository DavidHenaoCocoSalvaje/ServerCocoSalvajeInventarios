# app.models.pydantic.world_office.base
# Optional\[(\w+)\]
# $1 | None

from enum import Enum
from typing import Any

from app.models.pydantic.base import Base


class WOResponse(Base):
    status: str = ''
    userMessage: str = ''
    developerMessage: str = ''
    errorCode: str = ''
    moreInfo: Any = None


class TipoFiltroWoFiltro(str, Enum):
    IGUAL = 'IGUAL'
    CONTIENE = 'CONTIENE'
    MENOR_QUE = 'MENOR_QUE'
    MAYOR_QUE = 'MAYOR_QUE'
    EMPIEZA_CON = 'EMPIEZA_CON'
    MAYOR_O_IGUAL = 'MAYOR_O_IGUAL'
    MENOR_O_IGUAL = 'MENOR_O_IGUAL'
    TERMINA_CON = 'TERMINA_CON'
    ENTRE = 'ENTRE'
    IS_NULL = 'IS_NULL'
    LENGTH = 'LENGTH'
    DIFERENTE = 'DIFERENTE'
    IS_NOT_NULL = 'IS_NOT_NULL'
    LENGTH_IGUAL = 'LENGTH_IGUAL'
    NO_EMPIEZA_CON = 'NO_EMPIEZA_CON'


class TipoDatoWoFiltro(str, Enum):
    STRING = 'STRING'
    BOOLEAN = 'BOOLEAN'
    NUMERIC = 'NUMERIC'
    FECHA = 'FECHA'
    LONG = 'LONG'
    LISTA = 'LISTA'
    IN = 'IN'
    NOT_IN = 'NOT_IN'
    ENUM = 'ENUM'
    ENTIDAD = 'ENTIDAD'
    ARRAY_INT = 'ARRAY_INT'


class WOFiltro(Base):
    atributo: str = ''
    valor: str | int = ''
    tipoFiltro: TipoFiltroWoFiltro = TipoFiltroWoFiltro.IGUAL
    tipoDato: TipoDatoWoFiltro = TipoDatoWoFiltro.STRING
    operador: str = ''


class WOListar(Base):
    columnaOrdenar: str = ''
    pagina: int = 0
    registrosPorPagina: int = 0
    orden: str = ''
    filtros: list[WOFiltro] = []
    canal: int = 0
    registroInicial: int = 0


class Sort(Base):
    empty: bool = False
    sorted: bool = False
    unsorted: bool = True


class Pageable(Base):
    offset: int = 0
    sort: Sort = Sort()
    pageSize: int = 0
    pageNumber: int = 0
    paged: bool = False
    unpaged: bool = True


class WODataList(Base):
    pageable: Pageable = Pageable()
    last: bool = False
    totalElements: int = 0
    totalPages: int = 0
    first: bool = True
    size: int = 0
    number: int = 0
    sort: Sort = Sort()
    numberOfElements: int = 0
    empty: bool = True

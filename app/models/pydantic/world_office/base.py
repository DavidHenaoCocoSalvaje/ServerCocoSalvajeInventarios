# app.models.pydantic.world_office.base
# Optional\[(\w+)\]
# $1 | None

from enum import Enum
from typing import Any

from app.models.pydantic.base import Base


class WOResponse(Base):
    status: str | None = None
    userMessage: str | None = None
    developerMessage: str | None = None
    errorCode: str | None = None
    moreInfo: Any | None = None


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
    atributo: str | None = None
    valor: str | int | None = None
    tipoFiltro: TipoFiltroWoFiltro | None = None
    tipoDato: TipoDatoWoFiltro | None = None
    operador: str | None = None


class WOListar(Base):
    columnaOrdenar: str | None = None
    pagina: int | None = None
    registrosPorPagina: int | None = None
    orden: str | None = None
    filtros: list[WOFiltro] | None = None
    canal: int | None = None
    registroInicial: int | None = None


class Sort(Base):
    empty: bool | None = None
    sorted: bool | None = None
    unsorted: bool | None = True


class Pageable(Base):
    offset: int | None = None
    sort: Sort | None = None
    pageSize: int | None = None
    pageNumber: int | None = None
    paged: bool | None = None
    unpaged: bool | None = True


class WODataList(Base):
    pageable: Pageable | None = None
    last: bool | None = None
    totalElements: int | None = None
    totalPages: int | None = None
    first: bool | None = True
    size: int | None = None
    number: int | None = None
    sort: Sort | None = None
    numberOfElements: int | None = None
    empty: bool | None = True

# app.models.pydantic.world_office.base
# Optional\[(\w+)\]
# $1 | None

from enum import Enum
from typing import Any

if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))

from app.models.pydantic.base import Base


class WOResponse(Base):
    status: str | int = ''
    userMessage: str | int = ''
    developerMessage: str | int = ''
    errorCode: str | int = ''
    moreInfo: Any = None


class TipoFiltroWoFiltro(int, Enum):
    IGUAL = 0
    CONTIENE = 1
    MENOR_QUE = 2
    MAYOR_QUE = 3
    EMPIEZA_CON = 4
    MAYOR_O_IGUAL = 5
    MENOR_O_IGUAL = 6
    TERMINA_CON = 7
    ENTRE = 8
    IS_NULL = 9
    LENGTH = 10
    DIFERENTE = 11
    IS_NOT_NULL = 12
    LENGTH_IGUAL = 13
    NO_EMPIEZA_CON = 14


class TipoDatoWoFiltro(int, Enum):
    STRING = 0
    BOOLEAN = 1
    NUMERIC = 2
    FECHA = 3
    LONG = 4
    LISTA = 5
    IN = 6
    NOT_IN = 7
    ENUM = 8
    ENTIDAD = 9
    ARRAY_INT = 10


class Operador(int, Enum):
    AND = 0
    OR = 1


class WOFiltro(Base):
    atributo: str = ''
    valor: str | int = ''
    valor2: str | int | None = None
    tipoFiltro: TipoFiltroWoFiltro = TipoFiltroWoFiltro.IGUAL
    tipoDato: TipoDatoWoFiltro = TipoDatoWoFiltro.STRING
    nombreColumna: str = ''
    valores: list[str | int] | None = None
    clase: str = ''
    operador: Operador = Operador.AND
    subGrupo: str = ''


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


if __name__ == '__main__':
    filtro = WOFiltro()
    filtro.tipoFiltro = TipoFiltroWoFiltro.IGUAL
    print(filtro.model_dump())

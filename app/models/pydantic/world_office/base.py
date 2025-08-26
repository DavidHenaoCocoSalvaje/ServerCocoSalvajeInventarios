# app.models.pydantic.world_office.base
from typing import Any
from app.models.pydantic.base import Base


class WOResponse(Base):
    status: str | None = ''
    userMessage: str | None = ''
    developerMessage: str | None = ''
    errorCode: str | None = ''
    moreInfo: Any | None = None


class WOFiltro(Base):
    atributo: str | None = ''
    valor: str | None = ''
    tipoFiltro: str | None = ''
    tipoDato: str | None = ''
    operador: str | None = ''


class WOListar(Base):
    columnaOrdenar: str | None = ''
    pagina: int | None = 0
    registrosPorPagina: int | None = 0
    orden: str | None = ''
    filtros: list[WOFiltro] | None = []
    canal: int | None = 0
    registroInicial: int | None = 0


class Sort(Base):
    empty: bool | None = False
    sorted: bool | None = False
    unsorted: bool | None = True


class Pageable(Base):
    offset: int | None = 0
    sort: Sort | None = Sort()
    pageSize: int | None = 0
    pageNumber: int | None = 0
    paged: bool | None = False
    unpaged: bool | None = True


class WODataList(Base):
    pageable: Pageable | None = Pageable()
    last: bool | None = False
    totalElements: int | None = 0
    totalPages: int | None = 0
    first: bool | None = True
    size: int | None = 0
    number: int | None = 0
    sort: Sort | None = Sort()
    numberOfElements: int | None = 0
    empty: bool | None = True

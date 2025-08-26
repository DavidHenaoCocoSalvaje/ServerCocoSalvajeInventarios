# app.internal.integrations.world_office
if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))

from app.internal.log import factory_logger
from app.models.pydantic.world_office.base import WOFiltro, WOListar
from app.models.pydantic.world_office.general import WOListaCiudadesResponse
from app.models.pydantic.world_office.terceros import WOTerceroResponse, WOTerceroCreate
from app.internal.integrations.base import BaseClient
from app.config import config

wo_log = factory_logger('world_office', file=True)


class WoClient(BaseClient):
    class Paths:
        class Terceros:
            root: str = '/terceros'
            identificacion: str = f'{root}/identificacion'
            crear: str = f'{root}/crearTercero'

        class Ciudad:
            root: str = '/ciudad'
            listar_ciudades: str = f'{root}/listarCiudades'

    def __init__(self, host: str = 'https://api.worldoffice.cloud/api'):
        super().__init__(f'{host}/{config.wo_api_version}')
        self.set_header('Content-Type', 'application/json')
        self.set_header('Authorization', f'WO {config.wo_api_key}')

    async def get_tercero(self, identificacion: str) -> WOTerceroResponse:
        tercero_response = await self.get(self.Paths.Terceros.identificacion, [identificacion])
        return WOTerceroResponse(**tercero_response)

    async def crear_tercero(self, wo_tercero_create: WOTerceroCreate) -> WOTerceroResponse:
        tercero_response = await self.post(self.Paths.Terceros.crear, payload=wo_tercero_create.model_dump())
        return WOTerceroResponse(**tercero_response)

    async def buscar_ciudad(self, nombre: str):
        filtro = WOFiltro(atributo='nombre', valor=nombre, tipoFiltro='CONTIENE', tipoDato='STRING', operador='AND')
        wo_listar = WOListar(columnaOrdenar='id', registrosPorPagina=10, orden='ASC', filtros=[filtro])
        ciudades_json = await self.post(self.Paths.Ciudad.listar_ciudades, payload=wo_listar.model_dump())
        ciudades_response = WOListaCiudadesResponse(**ciudades_json)
        if not ciudades_response.data.content:
            wo_log.error(f'No se encontró la ciudad {nombre}')
            raise Exception(f'WO: No se encontró la ciudad {nombre}')
        ciudad = ciudades_response.data.content[0]
        return ciudad


if __name__ == '__main__':
    from asyncio import run
    # from random import randint

    async def main():
        wo_client = WoClient()
        tercero = await wo_client.get_tercero('1094240554')
        assert tercero.data.identificacion == '1094240554'

        ciudad = await wo_client.buscar_ciudad('Bogotá')
        print(ciudad)

    run(main())

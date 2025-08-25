# app.internal.integrations.world_office

import json

from asyncio import run

if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))

from app.internal.integrations.base import BaseClient
from app.config import config


class WoClient(BaseClient):
    class Paths:
        class Terceros:
            root: str = '/terceros'
            identificacion: str = f'{root}/identificacion'

    def __init__(self, host: str = 'https://api.worldoffice.cloud/api'):
        super().__init__(f'{host}/{config.wo_api_version}')
        self.set_header('Content-Type', 'application/json')
        self.set_header('Authorization', f'WO {config.wo_api_key}')


async def main():
    wo_client = WoClient()
    cliente = await wo_client.get(wo_client.Paths.Terceros.identificacion, ['1094240554'])
    print(json.dumps(cliente, indent=2))


run(main())

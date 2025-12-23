from dataclasses import dataclass
from os import getenv
from enum import Enum
from dotenv import load_dotenv


class Environments(Enum):
    DEVELOPMENT = 'development'
    STAGING = 'staging'
    PRODUCTION = 'production'


@dataclass(frozen=True)
class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            load_dotenv()

            # Environment
            cls.environment = str(getenv('ENVIRONMENT', 'development')).lower()
            cls.production = cls.environment in ['production', 'prod']

            # Database
            cls.db_host = str(getenv('DB_HOST', 'localhost'))
            cls.db_port = int(getenv('DB_PORT', 5432))
            cls.db_user = str(getenv('DB_USER', 'postgres'))
            cls.db_password = str(getenv('DB_PASSWORD', ''))
            cls.db_name = str(getenv('DB_NAME', ''))
            cls.database_url = (
                f'postgresql+psycopg://{cls.db_user}:{cls.db_password}@{cls.db_host}:{cls.db_port}/{cls.db_name}'
            )

            # General
            cls.local_timezone = str(getenv('LOCAL_TIMEZONE', 'America/Bogota'))

            # Security & Shopify
            cls.secret_key = str(getenv('SECRET_KEY', ''))
            cls.shop_shopify = str(getenv('SHOP_SHOPIFY', ''))
            cls.shop_version = str(getenv('SHOP_VERSION', '2025-07'))
            cls.api_key_shopify = str(getenv('API_KEY_SHOPIFY', ''))
            cls.webhook_secret_shopify = str(getenv('WEBHOOK_SECRET_SHOPIFY', ''))
            cls.algorithm = str(getenv('ALGORITHM', 'HS256'))
            cls.access_token_expire_minutes = int(getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))
            cls.admin_password = str(getenv('ADMIN_PWD', ''))

            # World Office
            cls.wo_api_key = str(getenv('WO_API_KEY', ''))
            cls.wo_api_version = str(getenv('WO_API_VERSION', 'v1'))
            cls.wo_prefijo = int(getenv('WO_PREFIJO', 1))
            cls.wo_concepto = str(getenv('WO_CONCEPTO', ''))

            # Addi
            cls.addi_email = str(getenv('ADDI_EMAIL', ''))
            cls.addi_password = str(getenv('ADDI_PASSWORD', ''))
            cls.addi_api_version = str(getenv('ADDI_API_VERSION', 'v1'))

            # Google Cloud
            # Gemini
            cls.gemini_api_key = str(getenv('GEMINI_API_KEY', ''))
            cls.google_credentials = str(getenv('GOOGLE_CREDENTIALS', '/credentials/integraciones-coco.json'))

            # Logs
            cls.logs_dir = str(getenv('LOGS_DIR', 'logs'))

        return cls._instance


Config()

# app/config.py
from enum import Enum
from os import getenv
from dotenv import load_dotenv


class Environments(Enum):
    STAGING = 'staging'
    DEVELOPMENT = 'development'
    PRODUCTION = 'production'


class Config:
    _instance = None

    def __new__(cls):
        # Asegura que solo se cree una instancia (Singleton)
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            # Carga las variables de entorno una sola vez al crear la instancia
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Carga la configuración desde variables de entorno."""
        load_dotenv()  # Carga el archivo .env

        # Configuración del ambiente
        self.environment: str = getenv('ENVIRONMENT', Environments.DEVELOPMENT.value).lower()

        # Variables específicas para Azure Container Apps (built-in)
        # Estas variables son proporcionadas automáticamente por Azure Container Apps
        self.container_app_name: str = getenv('CONTAINER_APP_NAME', '')
        self.container_app_revision: str = getenv('CONTAINER_APP_REVISION', '')
        self.container_app_hostname: str = getenv('CONTAINER_APP_HOSTNAME', '')
        self.container_app_env_dns_suffix: str = getenv('CONTAINER_APP_ENV_DNS_SUFFIX', '')
        self.container_app_replica_name: str = getenv('CONTAINER_APP_REPLICA_NAME', '')

        # Variables para Azure Container Jobs (si aplica)
        self.container_app_job_name: str = getenv('CONTAINER_APP_JOB_NAME', '')
        self.container_app_job_execution_name: str = getenv('CONTAINER_APP_JOB_EXECUTION_NAME', '')

        # Accede a las variables usando getenv
        # Los atributos ahora son públicos para acceso directo
        self.db_host: str = getenv('DB_HOST', 'localhost')  # Corregido 'localshost'
        self.db_port: int = int(getenv('DB_PORT', 5432))
        self.db_user: str = getenv('DB_USER', 'postgres')
        self.db_password: str = getenv('DB_PASSWORD', '')
        self.db_name: str = getenv('DB_NAME', '')

        self.local_timezone = str(getenv('LOCAL_TIMEZONE', 'America/Bogota'))

        # Construye la URL de la base de datos directamente aquí
        # Asegúrate de usar el driver correcto (postgresql+psycopg)
        self.database_url: str = (
            f'postgresql+psycopg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}'
        )

        # Seguridad
        self.secret_key: str = getenv('SECRET_KEY', '')
        self.shop_shopify: str = getenv('SHOP_SHOPIFY', '')
        self.shop_version: str = getenv('SHOP_VERSION', '2025-07')
        self.api_key_shopify: str = getenv('API_KEY_SHOPIFY', '')
        self.webhook_secret_shopify: str = getenv('WEBHOOK_SECRET_SHOPIFY', '')
        self.algorithm: str = getenv('ALGORITHM', 'HS256')
        self.access_token_expire_minutes: int = int(getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))
        self.admin_password: str = getenv('ADMIN_PWD', '')
        self.wo_api_key: str = getenv('WO_API_KEY', '')
        self.wo_api_version: str = getenv('WO_API_VERSION', 'v1')

        # Facturación
        self.wo_prefijo: int = int(getenv('WO_PREFIJO', 1))
        self.wo_concepto: str = getenv('WO_CONCEPTO', '')

        # Addi
        self.addi_email: str = getenv('ADDI_EMAIL', '')
        self.addi_password: str = getenv('ADDI_PASSWORD', '')
        self.addi_api_version: str = getenv('ADDI_API_VERSION', 'v1')

    @property
    def production(self) -> bool:
        """
        Determina si la aplicación está ejecutándose en producción.

        Returns:
            bool: True si está en producción, False si está en desarrollo
        """
        return self.environment in ['production', 'prod']

    @property
    def is_container(self) -> bool:
        """
        Determina si la aplicación está ejecutándose en Azure Container Apps.
        Usa las variables de entorno built-in proporcionadas automáticamente por Azure.

        Returns:
            bool: True si está en Azure Container, False en caso contrario
        """
        return bool(
            self.container_app_name
            or self.container_app_revision
            or self.container_app_hostname
            or self.container_app_env_dns_suffix
        )

    @property
    def container_info(self) -> dict:
        """
        Retorna información detallada del Azure Container App si está disponible.

        Returns:
            dict: Información del contenedor Azure
        """
        return {
            'container_app_name': self.container_app_name,
            'container_app_revision': self.container_app_revision,
            'container_app_hostname': self.container_app_hostname,
            'container_app_env_dns_suffix': self.container_app_env_dns_suffix,
            'container_app_replica_name': self.container_app_replica_name,
            'container_app_job_name': self.container_app_job_name,
            'container_app_job_execution_name': self.container_app_job_execution_name,
        }


config = Config()

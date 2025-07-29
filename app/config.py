# app/config.py
import os
from dotenv import load_dotenv


class Config:
    _instance = None

    def __new__(cls):
        # Asegura que solo se cree una instancia (Singleton)
        if cls._instance is None:
            print("Creando instancia de configuración...")  # Para depuración
            cls._instance = super(Config, cls).__new__(cls)
            # Carga las variables de entorno una sola vez al crear la instancia
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Carga la configuración desde variables de entorno."""
        load_dotenv()  # Carga el archivo .env

        # Accede a las variables usando os.getenv
        # Los atributos ahora son públicos para acceso directo
        self.db_host: str = os.getenv("DB_HOST", "localhost")  # Corregido 'localshost'
        self.db_port: int = int(os.getenv("DB_PORT", 5432))
        self.db_user: str = os.getenv("DB_USER", "postgres")
        self.db_password: str = os.getenv("DB_PASSWORD", "")
        self.db_name: str = os.getenv("DB_NAME", "")

        self.local_timezone = str(os.getenv("LOCAL_TIMEZONE", "America/Bogota"))

        # Construye la URL de la base de datos directamente aquí
        # Asegúrate de usar el driver correcto (postgresql+psycopg)
        self.database_url: str = (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

        # Seguridad
        self.secret_key: str = os.getenv("SECRET_KEY", "")
        self.api_key_shopify: str = os.getenv("API_KEY_SHOPIFY", "")
        self.algorithm: str = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_minutes: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
        )


config = Config()

# app/internal/log.py
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict


def _get_environment() -> str:
    """
    Detecta el ambiente de ejecución usando la configuración centralizada.

    Returns:
        str: 'production' si está en Azure Container App/producción, 'development' en caso contrario
    """
    # Importar config aquí para evitar imports circulares
    from app.config import config

    # Usar la variable de ambiente centralizada desde config.py
    return config.environment


class Logger:
    """
    Clase para manejar el logging de la aplicación.
    Permite crear múltiples instancias de logger por nombre.
    Configura logs según el ambiente detectado desde config.py:
    - Desarrollo: archivo (INFO) + consola (DEBUG)
    - Producción/Azure Container: consola (INFO) para logs del contenedor
    """

    _instances: Dict[str, 'Logger'] = {}
    _configured: bool = False

    def __init__(self, name: str = 'CocoSalvajeInventarios'):
        """
        Inicializa una instancia de Logger.

        Args:
            name: Nombre del logger. Por defecto es "CocoSalvajeInventarios"
        """
        self.name = name
        self._logger: Optional[logging.Logger] = None
        self._setup_logger()

    def __new__(cls, name: str = 'CocoSalvajeInventarios'):
        """
        Crea o retorna una instancia existente del logger con el nombre dado.
        """
        if name not in cls._instances:
            instance = super(Logger, cls).__new__(cls)
            cls._instances[name] = instance
        return cls._instances[name]

    def _setup_logger(self):
        """
        Configura el logger según el ambiente detectado desde config.py.
        """
        if self._logger is not None:
            return

        from app.config import config

        # Crear el logger específico
        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(logging.DEBUG)

        # Evitar duplicar handlers si el logger ya está configurado
        if self._logger.handlers:
            return

        # Configurar handlers
        self._configure_handlers(config)

    def _configure_handlers(self, config):
        """
        Configura los handlers según el ambiente.
        """
        if self._logger is None:
            return

        # Formato para los logs
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

        if config.is_production():
            # PRODUCCIÓN: Solo logs a consola (para Azure Container Apps)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)

            container_info = ' (Azure Container)' if config.is_azure_container() else ''
            self._logger.info(f'Logger configurado para PRODUCCIÓN{container_info} - logs a consola')

        else:
            # DESARROLLO: Archivo (INFO) + Consola (DEBUG)

            # Crear directorio de logs si no existe
            log_dir = Path('logs')
            log_dir.mkdir(exist_ok=True)

            # Handler para archivo con rotación
            file_handler = RotatingFileHandler(
                filename=log_dir / 'app.log',
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8',
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)

            # Handler para consola en desarrollo
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)

            # Agregar handlers al logger
            self._logger.addHandler(file_handler)
            self._logger.addHandler(console_handler)

            self._logger.info(f'Logger "{self.name}" configurado para DESARROLLO - archivo (INFO) + consola (DEBUG)')

    def get_logger(self) -> logging.Logger:
        """
        Retorna la instancia del logger configurado.
        """
        if self._logger is None:
            raise RuntimeError('Logger no está inicializado')
        return self._logger

    @property
    def logger(self) -> logging.Logger:
        """
        Propiedad para acceder directamente al logger.
        """
        return self.get_logger()

    @classmethod
    def get_instance(cls, name: str = 'CocoSalvajeInventarios') -> 'Logger':
        """
        Método de clase para obtener una instancia de Logger por nombre.

        Args:
            name: Nombre del logger

        Returns:
            Logger: Instancia del logger
        """
        return cls(name)

    def get_environment(self) -> str:
        """
        Retorna el ambiente actual detectado.
        """
        return _get_environment()


# Instancia global del logger principal
default_logger = Logger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Función helper para obtener un logger específico o el principal.

    Args:
        name: Nombre del logger. Si es None, retorna el logger principal.

    Returns:
        logging.Logger: Instancia del logger configurado.
    """
    if name:
        logger_instance = Logger.get_instance(name)
        return logger_instance.logger
    return default_logger.logger

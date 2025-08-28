# app/internal/log.py
import logging
from logging.handlers import TimedRotatingFileHandler
from enum import Enum
from app.config import config
from sys import stdout
from os import path, makedirs
import datetime
import pytz

from app.internal.gen.utilities import DateTz


class TimedSizeRotatingFileHandler(TimedRotatingFileHandler):
    """
    Handler que combina rotación por tiempo y por tamaño
    """

    def __init__(self, *args, maxBytes=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxBytes = maxBytes

    def shouldRollover(self, record):
        """
        Determina si se debe rotar el archivo por tiempo o por tamaño
        """
        # Verificar rotación por tiempo
        if super().shouldRollover(record):
            return True

        # Verificar rotación por tamaño
        if self.maxBytes > 0:
            msg = '%s\n' % self.format(record)
            self.stream.seek(0, 2)  # Ir al final del archivo
            if self.stream.tell() + len(msg) >= self.maxBytes:
                return True

        return False


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    FATAL = logging.FATAL
    CRITICAL = logging.CRITICAL


def factory_logger(
    name: str,
    level: LogLevel = LogLevel.INFO,
    file: bool = False,
    max_file_size: int = 10 * 1024 * 1024,
    backup_count: int = 5,
):
    """
    Crea un logger con configuración para consola y opcionalmente archivo con rotación.

    Args:
        name: Nombre del logger
        level: Nivel de logging
        file: Si True, también loggea a archivo
        max_file_size: Tamaño máximo del archivo en bytes (default: 10MB)
        backup_count: Número de archivos de backup a mantener (default: 5)
    """
    logger = logging.getLogger(name)
    logger.setLevel(level.value)

    # Evitar duplicar handlers si el logger ya existe
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt=f'{DateTz.local().strftime("%Y-%m-%d %H:%M:%S")} - %(name)s - %(levelname)s - %(pathname)s - %(filename)s:%(lineno)d - %(message)s'
    )

    # Handler para consola (siempre presente)
    console_handler = logging.StreamHandler(stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para archivo con rotación (solo en desarrollo o si se especifica file=True)
    if not config.production or file:
        # Crear directorio de logs si no existe
        logs_dir = 'logs'
        if not path.exists(logs_dir):
            makedirs(logs_dir)

        # Nombre base del archivo de log
        log_filename = path.join(logs_dir, f'{name}_{DateTz.local().strftime("%Y_%m_%d")}.log')

        # Configurar timezone de Colombia
        bogota_tz = pytz.timezone('America/Bogota')
        midnight_bogota = datetime.time(0, 0, 0, 0, bogota_tz)

        # TimedSizeRotatingFileHandler para rotación diaria y por tamaño
        file_handler = TimedSizeRotatingFileHandler(
            filename=log_filename,
            when='midnight',
            interval=1,
            backupCount=backup_count,
            encoding='utf-8',
            maxBytes=max_file_size,
            utc=False,
            atTime=midnight_bogota,
        )
        file_handler.suffix = '%Y_%m_%d'
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

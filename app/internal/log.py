# app/internal/log.py
import logging
from logging.handlers import RotatingFileHandler
from enum import Enum
from app.config import config
from sys import stdout
from os import path, makedirs


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
    Crea un logger con configuración para consola y opcionalmente archivo con rotación por tamaño.

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
        fmt='\n%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d\n%(message)s\n'
    )

    # Handler para consola (siempre presente)
    console_handler = logging.StreamHandler(stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para archivo con rotación por tamaño (solo en desarrollo o si se especifica file=True)
    if not config.production or file:
        # Crear directorio de logs si no existe
        logs_dir = 'logs'
        if not path.exists(logs_dir):
            makedirs(logs_dir)

        # Nombre del archivo de log
        log_filename = path.join(logs_dir, f'{name}.log')

        # RotatingFileHandler para rotación por tamaño
        file_handler = RotatingFileHandler(
            filename=log_filename,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8',
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
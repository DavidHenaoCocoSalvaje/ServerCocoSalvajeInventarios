# # app/models/usuario.py
# from sqlmodel import Field, SQLModel


# # Solo el modelo de tabla
# class Usuario(SQLModel, table=True):
#     __tablename__ = "usuarios"  # type: ignore

#     id: int = Field(primary_key=True)
#     primer_nombre: str = Field(max_length=25)
#     # Usar default=None para atributos opcionales
#     segundo_nombre: str | None = None
#     primer_apellido: str = Field(max_length=25)
#     segundo_apellido: str | None = None
#     sexo: str = Field(include=["F", "M"], default=None)


import logging
import sys

logger = logging.getLogger('simple_example')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('spam.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
ch.setFormatter(formatter)
fh.setFormatter(formatter)
# add the handlers to logger
logger.addHandler(ch)
logger.addHandler(fh)

# 'application' code
logger.debug('debug message')
logger.info('info message')
logger.warning('warn message')
logger.error('error message')
logger.critical('critical message')

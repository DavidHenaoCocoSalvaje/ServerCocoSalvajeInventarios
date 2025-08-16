# app/models/usuario.py
from sqlmodel import Field, SQLModel


class UsuarioBase(SQLModel):
    username: str = Field(max_length=50, unique=True)
    contacto_id: int | None = None


class UsuarioCreate(UsuarioBase):
    password: str = Field(min_length=8, max_length=120)


# Solo el modelo de tabla
class UsuarioDB(UsuarioCreate, table=True):
    __tablename__ = 'usuarios'  # type: ignore
    id: int | None = Field(primary_key=True, default=None)
    # back_populates indica que si algo cambia en este modelo, debe cambiar en el otro también.
    # https://sqlmodel.tiangolo.com/tutorial/relationship-attributes/create-and-update-relationships/#create-a-team-with-heroes


# https://fastapi.tiangolo.com/es/tutorial/sql-databases/?h=sqlmodel#crear-multiples-modelos

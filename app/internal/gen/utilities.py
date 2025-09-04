from datetime import date, datetime
from zoneinfo import ZoneInfo

if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))

from app.config import config


class DateTz(datetime):
    @classmethod
    def local(cls, tz: str = config.local_timezone) -> datetime:
        return cls.now(ZoneInfo(tz))

    @classmethod
    def local_date(cls, tz: str = config.local_timezone) -> datetime:
        return cls.now(ZoneInfo(tz))

    @classmethod
    def today(cls, tz: str = config.local_timezone) -> date:
        return cls.local(tz).date()

    @classmethod
    def from_isostring(cls, isostring: str, tz: str = config.local_timezone) -> datetime:
        isostring = isostring.replace('Z', '+00:00')
        return cls.fromisoformat(isostring).astimezone(ZoneInfo(tz))


def pluralizar_por_sep(cadena: str, sep: str, n: int | None = None) -> str:
    """
    Convierte a plural cada palabra en una cadena de texto estilo 'dunder_score'.

    Las reglas de pluralización que sigue son:
    1. Si la palabra termina en vocal (a, e, i, o, u), se le añade 's'.
    2. Si la palabra termina en 'z', se cambia la 'z' por 'ces'.
    3. Si la palabra termina en cualquier otra consonante, se le añade 'es'.
    """
    palabras = cadena.split(sep)
    palabras_en_plural = palabras[:n] if n else palabras
    palabras_en_singular = palabras[n:] if n else []

    for i in range(len(palabras_en_plural)):
        if not palabras_en_plural[i]:
            continue

        ultima_letra = palabras_en_plural[i][-1]

        if ultima_letra in 'aeiou':
            palabras_en_plural[i] = palabras_en_plural[i] + 's'
        elif ultima_letra == 'z':
            palabras_en_plural[i] = palabras_en_plural[i][:-1] + 'ces'
        else:
            palabras_en_plural[i] = palabras_en_plural[i] + 'es'

    return sep.join(palabras_en_plural + palabras_en_singular)


def divide(dividendo: int | float, divisor: int | float) -> float:
    """
    Evita ZeroDivisionError.
    """
    if divisor == 0:
        return 0
    else:
        return dividendo / divisor


if __name__ == '__main__':
    print(DateTz.local())

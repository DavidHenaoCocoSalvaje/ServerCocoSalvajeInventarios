import re
import calendar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import holidays_co

if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))

from app.config import Config


class DateTz(datetime):
    @property
    def utc(self) -> 'DateTz':
        return self.replace(tzinfo=ZoneInfo('UTC'))

    @property
    def to_isostring(self) -> str:
        isostring = self.isoformat()
        return isostring.replace('+00:00', 'Z')

    @classmethod
    def local(cls, datetime: datetime | None = None, tz: str = Config.local_timezone) -> 'DateTz':
        if datetime:
            return cls(
                datetime.year,
                datetime.month,
                datetime.day,
                datetime.hour,
                datetime.minute,
                datetime.second,
                datetime.microsecond,
                tzinfo=ZoneInfo(tz),
            )
        else:
            return cls.now(ZoneInfo(tz))

    @classmethod
    def today(cls, datetime: datetime | None = None, tz: str = Config.local_timezone) -> date:
        if datetime:
            return cls(
                datetime.year,
                datetime.month,
                datetime.day,
                datetime.hour,
                datetime.minute,
                datetime.second,
                datetime.microsecond,
                tzinfo=ZoneInfo(tz),
            ).date()
        else:
            return cls.now(ZoneInfo(tz)).date()

    @classmethod
    def from_isostring(cls, isostring: str, tz: str = Config.local_timezone) -> 'DateTz':
        isostring = isostring.replace('Z', '+00:00')
        return cls.fromisoformat(isostring).astimezone(ZoneInfo(tz))

    @classmethod
    def from_str(cls, date_string: str) -> 'DateTz':
        formatos = ['%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%Y', '%y-%m-%d', '%d-%m-%y', '%y/%m/%d', '%d/%m/%y']
        for formato in formatos:
            try:
                _datetime = datetime.strptime(date_string, formato)
                return cls.local(_datetime)
            except ValueError:
                continue
        raise ValueError(f'Formato de fecha no válido: {date_string}')


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


def reemplazar_acentos_graves(cadena: str) -> str:
    tabla_traduccion = str.maketrans('àèìòùÀÈÌÒÙ', 'áéíóúÁÉÍÓÚ')
    return cadena.translate(tabla_traduccion)


def contains_special_characters(cadena: str) -> bool:
    # Retorna True si contiene caracteres especiales como @, #, $, %, ^, *, (, ), _, +, =, ?, /, \, |, {, }, [, ], ;, :, ', ", <, >, ., ,
    pattern = r'[@#$%^*()_+=?/\\|{}\[\];:\'\"<>,.]'
    return bool(re.search(pattern, cadena))


def divide(dividendo: int | float, divisor: int | float) -> float:
    """
    Evita ZeroDivisionError.
    """
    if divisor == 0:
        return 0
    else:
        return dividendo / divisor


def get_weekday(fecha: datetime | date):
    return calendar.weekday(fecha.year, fecha.month, fecha.day)


def next_business_day(fecha: datetime | date, no_working_days: list[int] = [5, 6]):
    weekday = get_weekday(fecha)
    holidays = {h.date for h in holidays_co.get_colombia_holidays_by_year(fecha.year)}
    while fecha in holidays or weekday in no_working_days:
        fecha = fecha + timedelta(days=1)
        weekday = get_weekday(fecha)
    return fecha


if __name__ == '__main__':
    print(DateTz.local())
    texto_acentos_graves = 'Hòla, ¿còmo estàs? Espèro que èstes bìen. Ùltimamente...'
    assert reemplazar_acentos_graves(texto_acentos_graves) == 'Hóla, ¿cómo estás? Espéro que éstes bíen. Últimamente...'

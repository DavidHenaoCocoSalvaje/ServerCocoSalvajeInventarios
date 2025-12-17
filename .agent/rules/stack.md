---
trigger: always_on
---

# CONTEXTO
## Guía de Buenas Prácticas: "Clean Code 2025"
1. Expresividad a través del Tipado
Contexto sobre verbosidad: Aprovechar la inferencia de tipos de los lenguajes modernos para evitar nombres de variables redundantes (ej. evitar nameString, usar name: string).
Tipos precisos: Definir tipos explícitos para valores escalares cuando sea necesario evitar ambigüedades (ej. diferenciar entre id numérico y cantidad aunque ambos sean números).
Evitar genéricos vacíos: No usar sufijos como Info, Data o List si el tipo ya describe la estructura.

2. Funciones y Separación de Intereses
Nivel de abstracción único: Cada función debe operar en un solo nivel de abstracción.
Separación estricta: Distinguir claramente entre código de Negocio (lógica pura), Datos (acceso/fetch) y Presentación (UI/Consola). No mezclarlos en la misma función.
Extracción: Si una función realiza validaciones, cálculos y llamadas a API, debe dividirse en funciones más pequeñas y reutilizables.

3. Inmutabilidad por Defecto
Evitar mutación directa: En lugar de modificar objetos o arrays existentes (ej. lista.push(item)), preferir la creación de nuevas copias con los cambios aplicados (ej. [...lista, item]).
Ventajas: Facilita el rastreo de cambios de estado y evita efectos secundarios difíciles de depurar, especialmente en aplicaciones concurrentes o reactivas.

4. Manejo de Errores: "Fail Fast" (Fallar Rápido)
Programación Asertiva: Validar las condiciones críticas al inicio de la función. Si algo está mal, detener la ejecución inmediatamente (lanzar error o retornar) en lugar de anidar múltiples if/else.
Visibilidad: No ocultar los errores. Registrar el error (logging) para el desarrollador y, crucialmente, informar al usuario final de que algo ocurrió, evitando estados inconsistentes en la aplicación.

5. Documentación y Comentarios Modernos
Autodocumentación: El código debe ser lo suficientemente claro para no requerir comentarios que expliquen qué hace.
El "Por Qué" y los "Edge Cases": Reservar los comentarios únicamente para explicar decisiones de diseño complejas, razones de negocio no obvias o casos borde (edge cases) específicos.
Uso de Docstrings: Utilizar estándares como JSDoc (o equivalentes en otros lenguajes) para documentar interfaces públicas, aprovechando que los IDEs modernos muestran esta info al pasar el mouse.

6. Testing de Comportamiento
Enfoque en el usuario: Las pruebas deben verificar el comportamiento observable por el usuario (o consumidor de la API), no la implementación interna.
Resistencia al refactor: Un buen test no debería romperse si cambias el nombre de una función privada, siempre y cuando el resultado final (el comportamiento) siga siendo el mismo.

7. Simplicidad (KISS, YAGNI, DRY) Actualizada
DRY (Don't Repeat Yourself): Abstraer lógica repetida en funciones o módulos reutilizables.
YAGNI (You Aren't Gonna Need It): No implementar funcionalidades o abstracciones complejas "por si acaso". Resolver el problema actual de la forma más sencilla.
KISS (Keep It Simple, Stupid): Ante dos soluciones que funcionan, elegir siempre la que tenga menor complejidad cognitiva.

8. Herramientas y Automatización
Delegar en herramientas: Usar Linters, Formateadores y análisis estático para forzar reglas de estilo.

# BACKEND RULES: Python & FastAPI

## 0. PROTOCOLO DE NAVEGACIÓN (Smart Deep-Dive)
Cuando se te proporcione una URL de documentación
1. **Fase de Mapeo:** Lee la URL principal proporcionada para entender la estructura y localizar la "Tabla de Contenidos" o el menú lateral.
2. **Fase de Selección:** Identifica los 1 o 3 sub-enlaces más relevantes para la tarea específica que estás resolviendo.
   - *Ejemplo:* Si la tarea es "hacer un join", no leas "Instalación". Busca el enlace que diga "Select / Joins" o "Relationship Loading".
3. **Fase de Ejecución:** **TIENES PERMISO** para navegar a esos sub-enlaces y leer su contenido antes de escribir código.
4. **Límite de Profundidad:** Máximo 3 niveles de profundidad (Home -> Tema -> Detalle -> Especificidad). No navegues sin rumbo.


## 1. FUENTES DE VERDAD
- **Python:** Consulta `docs.python.org/3/.
- **Tipado:** https://docs.python.org/3/library/typing.html
- **FastAPI:** Lee los `.md` directamente del repo: `github.com/fastapi/fastapi/tree/master/docs/en/docs`.
- **SQLModel:** Lee los `.md` directamente del repo: `https://github.com/fastapi/sqlmodel/tree/main/docs`.
- **SQLAlchemy:** Consulta `https://docs.sqlalchemy.org/en/20/tutorial/index.html`

## 2. TIPADO MODERNO (Estricto)
- Usa sintaxis nativa de Python 3.14+.

## 3. ASINCRONÍA & I/O
- **Async:** prefiere implementaciones asincronas, para peticiones usa httpx con AsyncClient

## 4. DATA
- Usa **Pydantic V2** (`BaseModel`, `ConfigDict`).
- Usa `model_validate` en lugar de métodos viejos.

## CONSTRUCCION DE MODELOS PYDANTIC
1. **Campos Opcionales (Falsy Defaults):**
- Por defecto, **todos** los campos deben ser opcionales, pero **NO** uses `None` como valor predeterminado.
- Usa valores "falsy" según el tipo inferido: `str = ""`, `int = 0`, `float = 0.0`, `bool = False`, `list = []`, `dict = {}`.
- *Ejemplo:* `name: str = ""` en lugar de `name: str | None = None`.
2. **Inferencia de Nulos (`null`) al construir modelos a partir de json o ejemplos:**
- Si un valor de entrada es `null` o `None`, **no** lo tipes como `Any` ni `Optional[None]`.
- **Analiza semánticamente el nombre del campo** para deducir el tipo.
- Si no puedes deducirlo, usa `str` por defecto.
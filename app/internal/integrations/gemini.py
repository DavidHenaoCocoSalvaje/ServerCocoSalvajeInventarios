# app/internal/integrations/gemini.py
# To run this code you need to install the following dependencies:
# pip install google-genai

if __name__ == '__main__':
    from os.path import abspath
    from sys import path as sys_path

    sys_path.append(abspath('.'))


from google import genai
from google.genai import types
from app.config import Config


async def search_product_description(search_query: str) -> str:
    client = genai.Client(
        api_key=Config.gemini_api_key,
    )

    model = 'gemini-flash-latest'
    contents = [
        types.Content(
            role='user',
            parts=[
                types.Part.from_text(text=search_query),
            ],
        ),
    ]
    tools = [
        types.Tool(google_search=types.GoogleSearch()),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=0,
        ),
        tools=tools,
        system_instruction=[
            types.Part.from_text(
                text="""Eres un agente de búsqueda de contexto en Google, Siempre debes realizar una búsqueda web y entregar una descripción corta de un producto o servicio.

Recibes el nombre del producto y de la empresa lo vende estos datos opcionales: [nombre comercial, razón social, ubicación].

Entrega la respuesta en texto plano únicamente con la descripción del producto, máximo con 120 caracteres."""
            ),
        ],
    )

    response = await client.aio.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )

    return response.text or ''


if __name__ == '__main__':
    from asyncio import run

    async def main():
        result = await search_product_description('Bioacem b10, Masser SAS')
        print(result)

    run(main())

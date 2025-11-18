from playwright.async_api import async_playwright
from asyncio import run
from urllib.parse import quote_plus


async def search_bing_copilot(query: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=['--disable-blink-features=AutomationControlled', '--disable-gpu', '--no-sandbox']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        query_url = quote_plus(query)
        await page.goto(f'https://www.bing.com/copilotsearch?q={query_url}')
        # Obtener iframe
        iframe_response_locator = page.frame_locator('iframe[src*="https://www.bing.com/search?q="]')
        iframe_response_main_locator = iframe_response_locator.locator('main')
        # Esperar disponibilidad del iframe
        await iframe_response_main_locator.wait_for(state='attached', timeout=10000)
        heading_response = iframe_response_main_locator.locator('[class*="gs_heroTextHeader"][role="heading"]')
        # Esperar que el heading tenga texto
        await heading_response.wait_for(state='attached', timeout=10000)
        heading_response_text = await heading_response.inner_text()
        await browser.close()

    return heading_response_text


if __name__ == '__main__':

    async def main():
        query = 'Que es BIOACEM B10 de MASSER SAS'
        search = await search_bing_copilot(query)
        print(search)

    run(main())

from playwright.async_api import async_playwright


async def get_final_url(start_url):
    async with async_playwright() as p:
        # Chromium 브라우저를 실행
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="ko-KR")
        page = await context.new_page()

        # URL 열기
        await page.goto(start_url, timeout=5000)

        # 최종 URL 가져오기
        final_url = page.url

        # 브라우저 종료
        await browser.close()
        return final_url

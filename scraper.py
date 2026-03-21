import re
import asyncio
from playwright.async_api import async_playwright


def clean_price(text):
    clean = re.sub(r"[^\d]", "", text)
    return int(clean) if clean else None


async def scrape_amazon(page):
    await page.wait_for_timeout(1500)

    selectors = [
        "#corePrice_feature_div span.a-price-whole",
        ".a-price-whole",
        "span.a-price span.a-offscreen"
    ]

    for s in selectors:
        try:
            el = await page.query_selector(s)
            if el:
                raw = (await el.inner_text()).strip()
                price = clean_price(raw)
                if price:
                    return price
        except:
            continue

    return None


async def scrape_flipkart(page):
    await page.wait_for_timeout(1500)

    selectors = [
        "._30jeq3._16Jk6d",
        "._25b18c ._30jeq3"
    ]

    for s in selectors:
        try:
            el = await page.query_selector(s)
            if el:
                raw = (await el.inner_text()).strip()
                price = clean_price(raw)
                if price:
                    return price
        except:
            continue

    return None


async def get_product_details(url):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0",
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()

            await page.goto(url, wait_until="networkidle", timeout=45000)

            title = (await page.title()).strip()

            if "amazon" in url.lower():
                price = await scrape_amazon(page)
            elif "flipkart" in url.lower():
                price = await scrape_flipkart(page)
            else:
                await browser.close()
                return {"error": "Website not supported"}

            await browser.close()

            if not price:
                return {"error": "Price not found"}

            title = (
                title.replace("Amazon.in:", "")
                     .replace("Buy", "")
                     .replace("Online at Best Price", "")
                     .strip()
            )

            return {
                "name": title,
                "price": price
            }

    except Exception as e:
        return {"error": f"Scraper error: {str(e)}"}
import re
import asyncio
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


def clean_price(text):
    clean = re.sub(r"[^\d]", "", text)
    return int(clean) if clean else None


# 🔥 GOOGLE JUGAD (FINAL BACKUP)
def google_fallback(url):
    print("🌍 Using Google fallback...")

    try:
        query = "site:flipkart.com " + url.split("/")[-1]
        search_url = f"https://www.google.com/search?q={query}"

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        res = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        text = soup.get_text()

        match = re.search(r"₹\s?([\d,]+)", text)

        if match:
            price = clean_price(match.group(1))
            print("💰 Google Price:", price)
            return price

        return None

    except Exception as e:
        print("Google fallback error:", e)
        return None


def convert_to_mobile(url):
    if "flipkart.com" in url:
        return url.replace("www.", "m.")
    return url


async def _scrape_product(url):
    try:
        print("\n🚀 Starting scrape for:", url)

        async with async_playwright() as p:

            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="en-IN"
            )

            page = await context.new_page()

            # STEP 1: open URL
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(4000)

            final_url = page.url
            print("🔁 Redirected URL:", final_url)

            final_url = convert_to_mobile(final_url)

            await page.goto(final_url, timeout=60000)
            await page.wait_for_timeout(4000)

            # scroll
            for _ in range(2):
                await page.mouse.wheel(0, 1200)
                await page.wait_for_timeout(1500)

            title = await page.title()
            price = None

            # TRY PLAYWRIGHT
            selectors = [
                "div._30jeq3",
                "div._1_WHN1",
                "span._16Jk6d"
            ]

            for sel in selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        raw = (await el.inner_text()).strip()
                        price = clean_price(raw)
                        print("💰 PW Price:", price)
                        if price:
                            break
                except:
                    continue

            await browser.close()

            # 🔥 GOOGLE FALLBACK
            if not price and "flipkart" in final_url:
                price = google_fallback(final_url)

            if not price:
                return {
                    "error": "Price not found (all methods failed)",
                    "debug": {
                        "url": final_url,
                        "title": title
                    }
                }

            # clean title
            title = re.sub(
                r'(Amazon\.in|Flipkart\.com|Buy|Online at best price| -.*)',
                '',
                title,
                flags=re.I
            ).strip()

            print("✅ FINAL SUCCESS:", title, price)

            return {
                "name": title[:250],
                "price": price
            }

    except Exception as e:
        print("💥 ERROR:", str(e))
        return {"error": str(e)}


def get_product_details(url):
    try:
        return asyncio.run(_scrape_product(url))
    except Exception as e:
        return {"error": f"Runtime error: {str(e)}"}
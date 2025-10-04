from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_product(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            response = page.goto(url, timeout=60000)
            if response.status != 200:
                raise Exception(f"Failed to load page: {response.status}")

            page.wait_for_load_state('domcontentloaded')
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')

            if 'amazon' in url:
                title = soup.select_one('#productTitle')
                price = soup.select_one('.a-price .a-offscreen')
                features = [li.get_text(strip=True) for li in soup.select('#feature-bullets .a-list-item')]
            elif 'flipkart' in url:
                title = soup.select_one('span.B_NuCI')
                price = soup.select_one('div._30jeq3')
                features = [li.get_text(strip=True) for li in soup.select('div._2418kt ul li')]
            else:
                title = soup.title
                price = None
                features = [li.get_text(strip=True) for li in soup.select('li')][:10]

            return {
                "source": "Amazon" if 'amazon' in url else "Flipkart" if 'flipkart' in url else "Static Site",
                "title": title.get_text(strip=True) if title else "N/A",
                "price": price.get_text(strip=True) if price else "N/A",
                "description": "Extracted from page",
                "features": features,
                "url": url
            }

        except Exception as e:
            return {
                "source": "Error",
                "title": "Error",
                "price": "N/A",
                "description": str(e),
                "features": [],
                "url": url
            }
        finally:
            browser.close()

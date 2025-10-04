from playwright.sync_api import sync_playwright

def scrape_product(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)

        if 'flipkart' in url:
            page.wait_for_selector('span.B_NuCI', timeout=10000)
            title = page.query_selector('span.B_NuCI')
            price = page.query_selector('div._30jeq3')
            description = page.query_selector('div._1mXnXO')
            features = page.query_selector_all('div._2418kt ul li')

        elif 'amazon' in url:
            page.wait_for_selector('#productTitle', timeout=10000)
            title = page.query_selector('#productTitle')
            price = page.query_selector('.a-price .a-offscreen')
            description = page.query_selector('#productDescription')
            features = page.query_selector_all('#feature-bullets .a-list-item')

        else:
            browser.close()
            return {
                "source": "Unknown",
                "title": "Unsupported URL",
                "price": "N/A",
                "description": "Only Flipkart and Amazon are supported.",
                "features": [],
                "url": url
            }

        data = {
            "source": "Flipkart" if 'flipkart' in url else "Amazon",
            "title": title.inner_text().strip() if title else "N/A",
            "price": price.inner_text().strip() if price else "N/A",
            "description": description.inner_text().strip() if description else "N/A",
            "features": [f.inner_text().strip() for f in features if f.inner_text().strip()],
            "url": url
        }

        browser.close()
        return data

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/91.0.4472.124 Safari/537.36'
    )
}

PRICE_SELECTORS = ['.price', '.cost', '[class*="price"]', '[id*="price"]']
DESC_SELECTORS = ['.description', '.product-description', '[class*="description"]']

AMAZON_SELECTORS = {
    'price': ['#corePriceDisplay_desktop_feature_div', '.a-price .a-offscreen', '#priceblock_ourprice', '#priceblock_dealprice'],
    'title': ['#productTitle'],
    'description': ['#feature-bullets']
}

FLIPKART_SELECTORS = {
    'price': ['[class*="jeq3"]', '._30jeq3'],
    'title': ['.B_NuCI', '.VU-ZEz'],
    'description': ['._1mXcCf', '._1AN87F']
}

def is_valid_url(url):
    return url.startswith(('http://', 'https://'))

def extract_text(soup, selectors, truncate=200):
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(strip=True)
            return text[:truncate] + "..." if len(text) > truncate else text
    return None

def extract_amazon_features(soup):
    features = {}
    
    # Extract title
    title = soup.select_one(AMAZON_SELECTORS['title'][0])
    if title:
        features['Product'] = title.get_text(strip=True)

    # Extract price
    for selector in AMAZON_SELECTORS['price']:
        el = soup.select_one(selector)
        if el:
            features['Price'] = el.get_text(strip=True)
            break

    # Extract features/description
    desc = soup.select_one(AMAZON_SELECTORS['description'][0])
    if desc:
        items = [li.get_text(strip=True) for li in desc.select('li')]
        if items:
            features['Features'] = items

    return features

def extract_flipkart_features(soup):
    features = {}
    
    # Extract title
    for selector in FLIPKART_SELECTORS['title']:
        title = soup.select_one(selector)
        if title:
            features['Product'] = title.get_text(strip=True)
            break

    # Extract price
    for selector in FLIPKART_SELECTORS['price']:
        el = soup.select_one(selector)
        if el:
            features['Price'] = el.get_text(strip=True)
            break

    # Extract description
    for selector in FLIPKART_SELECTORS['description']:
        desc = soup.select_one(selector)
        if desc:
            features['Description'] = desc.get_text(strip=True)
            break

    return features

def scrape_features(url):
    try:
        logger.info(f"Scraping: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        features = {}
        
        if "amazon." in url:
            features = extract_amazon_features(soup)
        elif "flipkart." in url:
            features = extract_flipkart_features(soup)
        else:
            # Generic scraping
            title = soup.find('h1')
            if title:
                features['Product'] = title.get_text(strip=True)

            price = extract_text(soup, PRICE_SELECTORS)
            if price:
                features['Price'] = price

            description = extract_text(soup, DESC_SELECTORS, truncate=300)
            if not description:
                meta = soup.find('meta', attrs={'name': 'description'})
                if meta:
                    content = meta.get('content', '')
                    description = content[:300] + "..." if len(content) > 300 else content
            if description:
                features['Description'] = description

            # Try to extract feature lists
            if not features.get('Features'):
                import bs4
                for ul in soup.find_all(['ul', 'ol'])[:3]:
                    if isinstance(ul, bs4.element.Tag):
                        items = [li.get_text(strip=True) for li in ul.find_all('li')[:5]]
                        if items and len(items) > 1:
                            features['Features'] = items
                            break

        if not features or len(features) == 0:
            page_title = soup.find('title')
            features = {
                'Product': page_title.get_text(strip=True) if page_title else 'Unknown Product',
                'Description': 'Could not extract detailed information from this page.',
            }

        logger.info(f"Successfully scraped {len(features)} features from {url}")
        return features

    except requests.Timeout:
        logger.error(f"Timeout error for {url}")
        return {'error': f'Request timeout for {url}. The website took too long to respond.'}
    except requests.RequestException as e:
        logger.error(f"Request error for {url}: {e}")
        return {'error': f'Failed to fetch {url}: {str(e)}'}
    except Exception as e:
        logger.error(f"Scraping error for {url}: {e}")
        return {'error': f'Error scraping {url}: {str(e)}'}

def normalize_features(raw_data):
    """Normalize scraped data into consistent format"""
    return {
        'Product': raw_data.get('Product') or raw_data.get('Title') or 'Unnamed Product',
        'Description': raw_data.get('Description') or 'No description found',
        'Features': (
            raw_data.get('Features') if isinstance(raw_data.get('Features'), list)
            else [raw_data.get('Features')] if raw_data.get('Features')
            else ['No features found']
        ),
        'Price': raw_data.get('Price') or 'No price found'
    }

@app.route('/compare', methods=['POST'])
def compare():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON payload'}), 400

    url1, url2 = data.get('url1'), data.get('url2')
    if not (url1 and url2):
        return jsonify({'error': 'Both URLs are required'}), 400
    if not (is_valid_url(url1) and is_valid_url(url2)):
        return jsonify({'error': 'URLs must start with http:// or https://'}), 400

    logger.info(f"Comparing: {url1} vs {url2}")
    
    result1 = scrape_features(url1)
    result2 = scrape_features(url2)

    # Check for errors
    errors = {}
    if 'error' in result1:
        errors['url1'] = result1['error']
    if 'error' in result2:
        errors['url2'] = result2['error']
    if errors:
        return jsonify({'error': errors}), 400

    return jsonify({
        'data1': normalize_features(result1),
        'data2': normalize_features(result2)
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'API is running'})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'name': 'Universal Feature Comparator API',
        'version': '1.1.0',
        'endpoints': {
            '/compare': 'POST - Compare features from two URLs',
            '/health': 'GET - Health check'
        }
    })

# if __name__ == '__main__':
#     print("=" * 50)
#     print("Starting Flask server...")
#     print("API available at: http://127.0.0.1:5000/")
#     print("Health check: http://127.0.0.1:5000/health")
#     print("=" * 50)
#     app.run(debug=True, host='0.0.0.0', port=5000)


from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper import scrape_product
import traceback

app = Flask(__name__)
CORS(app)

@app.route('/compare', methods=['POST'])
def compare_products():
    try:
        data = request.json
        url1 = data.get('url1', '').strip()
        url2 = data.get('url2', '').strip()

        if not url1 and not url2:
            return jsonify({"error": "Please provide at least one valid URL."}), 400

        results = []

        if url1:
            result1 = scrape_product(url1)
            results.append(result1)

        if url2:
            result2 = scrape_product(url2)
            results.append(result2)

        return jsonify({"comparison": results})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == '__main__':
    print("Starting Flask server on http://127.0.0.1:5000/")
    app.run(debug=True, host='0.0.0.0', port=5000)

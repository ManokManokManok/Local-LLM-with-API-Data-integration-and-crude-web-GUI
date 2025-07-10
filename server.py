from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

ALPHA_VANTAGE_API_KEY = "1GPJAVBAPACY6D5K"

# FROM OUR API DATA RETRIEVAL
WATCHED_SYMBOLS = ["AAPL", "TSLA", "MSFT", "GOOGL", "NVDA"]

def fetch_stock_snapshot():
    summary = []
    for symbol in WATCHED_SYMBOLS:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            quote = data.get("Global Quote", {})
            price = quote.get("05. price")
            if price:
                summary.append(f"{symbol}: ${price}")
            else:
                summary.append(f"{symbol}: ❌ No data")
        except Exception as e:
            summary.append(f"{symbol}: ⚠️ Error")
    
    return "Stock Prices Snapshot:\n" + " | ".join(summary)

# FETCH ONCE AT START
STOCK_SNAPSHOT = fetch_stock_snapshot()

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '').strip()

    if not user_message:
        return jsonify({"reply": "⚠️ Please enter a message."})

    # ADDS DATA TO SYSTEM PROMPT (PRA ALAM AGAD NI AI)
    system_prompt = f"You are a helpful assistant.\n\n{STOCK_SNAPSHOT}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    try:
        response = requests.post("http://127.0.0.1:1234/v1/chat/completions", json={
            "model": "deepseek-r1-0528-qwen3-8b",
            "messages": messages,
            "stream": False
        }, timeout=999)

        response.raise_for_status()

        data = response.json()
        reply = data['choices'][0]['message']['content']
        return jsonify({"reply": reply})

    except requests.exceptions.RequestException as e:
        return jsonify({"reply": f"❌ API error: {str(e)}"}), 500

    except (KeyError, ValueError):
        return jsonify({"reply": "⚠️ Unexpected response format from the model."}), 500

if __name__ == '__main__':
    app.run(port=5000)

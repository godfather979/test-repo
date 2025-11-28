from flask import Flask, request, jsonify
from functions.bse_news import summarize_announcements_for_stock

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200


@app.route("/summaries", methods=["POST"])
def get_summaries():
    """
    Expected JSON body:

    {
      "stocks": ["RELIANCE", "TCS", "500112"],
      "days": 60,               # optional (default 60)
      "max_news_per_stock": 3   # optional (default 3)
    }
    """
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    stocks = data.get("stocks")
    if not isinstance(stocks, list) or not stocks:
        return jsonify({"error": "Field 'stocks' must be a non-empty list"}), 400

    days = data.get("days", 60)
    max_news_per_stock = data.get("max_news_per_stock", 3)

    response_payload = {}

    for stock in stocks:
        if not isinstance(stock, str):
            continue

        result = summarize_announcements_for_stock(
            stock_identifier=stock,
            days=days,
            max_news=max_news_per_stock,
        )

        # Final JSON will be: { "<stock>": { ...result... }, ... }
        response_payload[stock] = result

    return jsonify(response_payload), 200


if __name__ == "__main__":
    # Dev only
    app.run(host="0.0.0.0", port=5000, debug=True)

from flask import Flask, request, jsonify
import os

from functions.bse_news import summarize_announcements_for_stock
from functions.chart_maker import get_tradingview_chart_screenshot
from functions.chart_prediction import detect_chart_pattern, encode_image

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

@app.route("/chart-patterns", methods=["POST"])
def chart_patterns():
    """
    Analyze candlestick chart patterns for a list of TradingView symbols.

    Expected JSON body:

    {
      "symbols": ["NSE:RELIANCE", "NSE:TCS"],
      "interval": "D",                 # optional (default "D")
      "include_image_base64": true     # optional (default true)
    }

    Response:

    {
      "NSE:RELIANCE": {
        "symbol": "NSE:RELIANCE",
        "interval": "D",
        "chart_image_base64": "<base64-string> or null",
        "pattern": {
          "pattern_found": true,
          "pattern_name": "Double Bottom",
          "confidence": "moderate",
          "explanation": "..."
        },
        "error": null
      },
      "NSE:TCS": {
        ...
      }
    }
    """
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    symbols = data.get("symbols")
    if not isinstance(symbols, list) or not symbols:
        return jsonify({"error": "Field 'symbols' must be a non-empty list"}), 400

    interval = data.get("interval", "D")
    include_image_base64 = data.get("include_image_base64", True)

    # Ensure charts directory exists
    charts_dir = "./charts"
    os.makedirs(charts_dir, exist_ok=True)

    response_payload = {}

    for symbol in symbols:
        if not isinstance(symbol, str):
            continue

        result = {
            "symbol": symbol,
            "interval": interval,
            "chart_image_base64": None,
            "pattern": None,
            "error": None,
        }

        try:
            safe_symbol = symbol.replace(":", "_").replace("/", "_")
            output_path = os.path.join(
                charts_dir,
                f"{safe_symbol}_{interval}.png"
            )

            # 1) Get chart screenshot
            screenshot_path = get_tradingview_chart_screenshot(
                tv_symbol=symbol,
                interval=interval,
                output_path=output_path,
            )

            # 2) Optional: include base64 image for frontend display
            if include_image_base64:
                try:
                    img_b64 = encode_image(screenshot_path)
                    result["chart_image_base64"] = img_b64
                except Exception as e:
                    result["error"] = f"Error encoding image: {e}"

            # 3) Detect pattern using Groq vision
            pattern_info = detect_chart_pattern(screenshot_path)
            result["pattern"] = pattern_info

        except Exception as e:
            result["error"] = f"Error during chart processing: {e}"

        response_payload[symbol] = result

    return jsonify(response_payload), 200


if __name__ == "__main__":
    # Dev only
    app.run(host="0.0.0.0", port=5000, debug=True)

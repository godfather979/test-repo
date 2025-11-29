import os
import json
from functools import wraps

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, auth, firestore as admin_fs
from google.cloud import firestore as gc_fs
import requests

from functions.bse_news import summarize_announcements_for_stock
from functions.chart_maker import get_tradingview_chart_screenshot
from functions.chart_prediction import detect_chart_pattern, encode_image
from functions.financial_ratios import analyze_stock_ratios
from functions.financial_ratios import get_ratios_for_ticker
from functions.stock_signal_agent import StockSignalInput, run_stock_signal



# ================== ENV & APP SETUP ==================

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# ================== FIREBASE SETUP ===================

FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "firebase_credentials.json")
WEB_API_KEY = os.getenv("WEB_API_KEY")

if not os.path.exists(FIREBASE_CREDENTIALS):
    raise RuntimeError(f"Firebase credentials file not found: {FIREBASE_CREDENTIALS}")

if not WEB_API_KEY:
    raise RuntimeError("WEB_API_KEY not set in .env")

cred = credentials.Certificate(FIREBASE_CREDENTIALS)
firebase_admin.initialize_app(cred)

db = admin_fs.client()

# For Firestore helpers (timestamps, array ops)
ArrayUnion = gc_fs.ArrayUnion
ArrayRemove = gc_fs.ArrayRemove
SERVER_TIMESTAMP = gc_fs.SERVER_TIMESTAMP

FIREBASE_SIGNIN_URL = (
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={WEB_API_KEY}"
)

# ============== AUTH DECORATOR (FIREBASE TOKEN) ==============

def verify_firebase_token(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                raise ValueError("Authorization header missing or malformed")

            token = auth_header.split("Bearer ", 1)[1].strip()
            decoded_token = auth.verify_id_token(token)
            # Attach decoded firebase user info to request
            request.user = decoded_token
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": "Unauthorized", "details": str(e)}), 401

    return wrapper

# ====================== BASIC HEALTH ==========================

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

# ======================= AUTH ROUTES ==========================

@app.route("/user/signup", methods=["POST"])
def signup():
    """
    Body:
    {
      "name": "mihit",
      "email": "user@example.com",
      "password": "secret123"
    }
    Creates Firebase Auth user + Firestore user doc.
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name", "")
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    try:
        # Create user in Firebase Auth
        user = auth.create_user(
            email=email,
            password=password,
            display_name=name,
        )

        # Create Firestore user doc
        user_doc = {
            "userID": user.uid,
            "name": name,
            "email": email,
            "wishlist": [],
            "createdAt": SERVER_TIMESTAMP,
            "updatedAt": SERVER_TIMESTAMP,
        }
        db.collection("users").document(user.uid).set(user_doc)

        return jsonify({"message": "User created", "userID": user.uid}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/user/login", methods=["POST"])
def login():
    """
    Body:
    {
      "email": "user@example.com",
      "password": "secret123"
    }

    Returns:
    {
      "idToken": "...",
      "refreshToken": "...",
      "user": {
        "userID": "...",
        "name": "...",
        "email": "...",
        "wishlist": [...]
      }
    }
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    try:
        # Call Firebase Identity Toolkit REST API
        resp = requests.post(
            FIREBASE_SIGNIN_URL,
            json={
                "email": email,
                "password": password,
                "returnSecureToken": True,
            },
            timeout=10,
        )

        if resp.status_code != 200:
            return (
                jsonify(
                    {
                        "error": "Invalid credentials",
                        "details": resp.json(),
                    }
                ),
                401,
            )

        payload = resp.json()
        id_token = payload.get("idToken")
        refresh_token = payload.get("refreshToken")
        uid = payload.get("localId")  # Firebase uid

        # Fetch Firestore user doc
        user_ref = db.collection("users").document(uid)
        doc = user_ref.get()
        if doc.exists:
            user_data = doc.to_dict()
        else:
            # In case doc missing, create minimal one
            user_data = {
                "userID": uid,
                "name": "",
                "email": email,
                "wishlist": [],
                "createdAt": SERVER_TIMESTAMP,
                "updatedAt": SERVER_TIMESTAMP,
            }
            user_ref.set(user_data)

        # Update last updated timestamp
        user_ref.update({"updatedAt": SERVER_TIMESTAMP})

        return (
            jsonify(
                {
                    "idToken": id_token,
                    "refreshToken": refresh_token,
                    "user": user_data,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===================== USER / WISHLIST ROUTES ==================

@app.route("/me", methods=["GET"])
@verify_firebase_token
def get_me():
    uid = request.user["uid"]
    user_ref = db.collection("users").document(uid)
    doc = user_ref.get()

    if not doc.exists:
        return jsonify({"error": "User not found"}), 404

    return jsonify(doc.to_dict()), 200


@app.route("/me/wishlist", methods=["GET"])
@verify_firebase_token
def get_my_wishlist():
    uid = request.user["uid"]
    user_ref = db.collection("users").document(uid)
    doc = user_ref.get()

    if not doc.exists:
        return jsonify({"error": "User not found"}), 404

    data = doc.to_dict()
    wishlist = data.get("wishlist", [])

    return jsonify({"userID": uid, "wishlist": wishlist}), 200


@app.route("/me/wishlist/add", methods=["POST"])
@verify_firebase_token
def add_to_wishlist():
    uid = request.user["uid"]
    data = request.get_json(silent=True) or {}
    symbol = data.get("symbol")

    if not symbol or not isinstance(symbol, str):
        return jsonify({"error": "symbol must be a non-empty string"}), 400

    symbol = symbol.strip().upper()

    user_ref = db.collection("users").document(uid)
    user_ref.set(
        {
            "wishlist": ArrayUnion([symbol]),
            "updatedAt": SERVER_TIMESTAMP,
        },
        merge=True,
    )

    # Fetch updated wishlist
    doc = user_ref.get()
    wishlist = doc.to_dict().get("wishlist", [])

    # 🔥 NEW: compute + cache all data for this stock
    try:
        compute_and_cache_stock_for_user(uid, symbol)
        status_msg = "wishlist updated and stock data cached"
    except Exception as e:
        # We don't want to fail wishlist addition just because caching failed
        status_msg = f"wishlist updated but caching failed: {e}"

    return jsonify({"userID": uid, "wishlist": wishlist, "status": status_msg}), 200



@app.route("/me/wishlist/remove", methods=["POST"])
@verify_firebase_token
def remove_from_wishlist():
    uid = request.user["uid"]
    data = request.get_json(silent=True) or {}
    symbol = data.get("symbol")

    if not symbol or not isinstance(symbol, str):
        return jsonify({"error": "symbol must be a non-empty string"}), 400

    symbol = symbol.strip().upper()

    user_ref = db.collection("users").document(uid)
    user_ref.set(
        {
            "wishlist": ArrayRemove([symbol]),
            "updatedAt": SERVER_TIMESTAMP,
        },
        merge=True,
    )

    doc = user_ref.get()
    wishlist = doc.to_dict().get("wishlist", [])

    return jsonify({"userID": uid, "wishlist": wishlist}), 200

# ===================== BSE SUMMARIES ROUTE =====================

@app.route("/summaries", methods=["POST"])
@verify_firebase_token
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

# ================== CHART PATTERN ROUTE ========================

@app.route("/chart-patterns", methods=["POST"])
@verify_firebase_token
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


@app.route("/ratios", methods=["POST"])
@verify_firebase_token
def get_ratios():
    """
    Calculate financial ratios for a list of ticker symbols using Yahoo Finance.

    Expected JSON body:

    {
      "symbols": ["RELIANCE.NS", "TCS.NS"]
    }

    Response:

    {
      "RELIANCE.NS": {
        "ticker": "RELIANCE.NS",
        "source": "Yahoo Finance",
        "ratios": {
          "Debt/Equity": 0.44,
          "Debt/Assets": 0.19,
          "Interest Coverage": 5.79,
          "EBITDA Margin": 18.79,
          ...
        },
        "error": null
      },
      "TCS.NS": {
        ...
      }
    }
    """
    data = request.get_json(silent=True) or {}
    symbols = data.get("symbols")

    if not isinstance(symbols, list) or not symbols:
        return jsonify({"error": "Field 'symbols' must be a non-empty list"}), 400

    response_payload = {}

    for sym in symbols:
        if not isinstance(sym, str):
            continue

        sym_clean = sym.strip().upper()
        result = analyze_stock_ratios(sym_clean)
        response_payload[sym_clean] = result

    return jsonify(response_payload), 200

@app.route("/prediction", methods=["POST"])
@verify_firebase_token
def prediction():
    """
    Agentic prediction endpoint using:
    - Deterministic math in Python (financial ratios via yfinance)
    - Agno agent + DuckDuckGo for one web search
    - Groq model for reasoning

    Expected JSON body:
    {
      "symbols": ["RELIANCE.NS", "TCS.NS"]
    }

    Response:
    {
      "RELIANCE.NS": {
        "ticker": "RELIANCE.NS",
        "bias": "bullish",
        "confidence": 78,
        "reasons": [...],
        "risks": [...],
        "latest_headlines": [...],
        "note": "This is an educational analytical view..."
      },
      "TCS.NS": { ... }
    }
    """
    data = request.get_json(silent=True) or {}
    symbols = data.get("symbols")

    if not isinstance(symbols, list) or not symbols:
        return jsonify({"error": "Field 'symbols' must be a non-empty list"}), 400

    result = {}

    for sym in symbols:
        if not isinstance(sym, str):
            continue

        ticker = sym.strip().upper()

        # 1) Deterministic math: compute ratios in Python
        ratios = get_ratios_for_ticker(ticker)
        if ratios is None:
            result[ticker] = {
                "error": "Could not fetch financial data for this ticker."
            }
            continue

        # 2) Build StockSignalInput for the agent
        ctx = StockSignalInput(
            ticker=ticker,
            ratios=ratios,
        )

        try:
            # 3) Run the Agno agent (with DuckDuckGo tool)
            signal = run_stock_signal(ctx)
            result[ticker] = signal.model_dump()
        except Exception as e:
            result[ticker] = {
                "error": f"Agent error: {str(e)}"
            }

    return jsonify(result), 200

@app.route("/me/cache", methods=["GET"])
@verify_firebase_token
def get_my_cached_stocks():
    """
    Returns all cached stock data for the logged-in user.
    Dashboard can use this endpoint directly.

    Response example:
    {
      "userID": "...",
      "stocks": {
        "RELIANCE.NS": {
          "symbol": "RELIANCE.NS",
          "bse_summaries": {...},
          "chart_pattern": {...},
          "ratios": {...},
          "signal": {...},
          "updatedAt": ...
        },
        "TCS.NS": { ... }
      }
    }
    """
    uid = request.user["uid"]
    user_ref = db.collection("users").document(uid)
    doc = user_ref.get()

    if not doc.exists:
        return jsonify({"error": "User not found"}), 404

    wishlist = doc.to_dict().get("wishlist", [])

    cache_col = user_ref.collection("stock_cache")
    cached_docs = cache_col.stream()

    stocks = {}
    for d in cached_docs:
        data = d.to_dict() or {}
        symbol = data.get("symbol") or d.id
        stocks[symbol] = data

    return jsonify({"userID": uid, "wishlist": wishlist, "stocks": stocks}), 200

@app.route("/me/refresh-cache", methods=["POST"])
@verify_firebase_token
def refresh_my_cache():
    """
    Recompute and overwrite cached data for all stocks in user's wishlist.
    Useful when user clicks 'Refresh' on dashboard.
    """
    uid = request.user["uid"]
    user_ref = db.collection("users").document(uid)
    doc = user_ref.get()

    if not doc.exists:
        return jsonify({"error": "User not found"}), 404

    data = doc.to_dict() or {}
    wishlist = data.get("wishlist", [])

    if not wishlist:
        return jsonify({"userID": uid, "refreshed": [], "message": "Wishlist is empty"}), 200

    refreshed = []
    errors = {}

    for symbol in wishlist:
        try:
            compute_and_cache_stock_for_user(uid, symbol)
            refreshed.append(symbol)
        except Exception as e:
            errors[symbol] = str(e)

    return jsonify(
        {
            "userID": uid,
            "refreshed": refreshed,
            "errors": errors,
        }
    ), 200



def compute_and_cache_stock_for_user(uid: str, symbol: str):
    """
    For a given user + stock symbol:
    - compute BSE summaries
    - compute chart pattern (TradingView + Groq vision)
    - compute financial ratios
    - run agentic prediction
    - save everything into users/{uid}/stock_cache/{symbol}
    """
    symbol = symbol.strip().upper()
    user_ref = db.collection("users").document(uid)
    cache_ref = user_ref.collection("stock_cache").document(symbol)

    cache_data = {
        "symbol": symbol,
        "updatedAt": SERVER_TIMESTAMP,
    }

    # --- 1) BSE Summaries (news) ---
    try:
        bse_result = summarize_announcements_for_stock(
            stock_identifier=symbol,
            days=60,
            max_news=3,
        )
        cache_data["bse_summaries"] = bse_result
    except Exception as e:
        cache_data["bse_error"] = f"{e}"

    # --- 2) Chart pattern (TradingView + Groq vision) ---
    try:
        charts_dir = "./charts"
        os.makedirs(charts_dir, exist_ok=True)

        safe_symbol = symbol.replace(":", "_").replace("/", "_")
        output_path = os.path.join(charts_dir, f"{safe_symbol}_D.png")

        screenshot_path = get_tradingview_chart_screenshot(
            tv_symbol=symbol,
            interval="D",
            output_path=output_path,
        )

        raw_pattern = detect_chart_pattern(screenshot_path)

        # detect_chart_pattern currently returns JSON string; try to parse
        try:
            pattern_info = json.loads(raw_pattern)
        except Exception:
            pattern_info = {"raw": raw_pattern}

        cache_data["chart_pattern"] = pattern_info
    except Exception as e:
        cache_data["chart_error"] = f"{e}"

    # --- 3) Financial ratios ---
    try:
        ratios = get_ratios_for_ticker(symbol)
        if ratios is not None:
            cache_data["ratios"] = ratios
        else:
            cache_data["ratios_error"] = "No ratio data available"
    except Exception as e:
        cache_data["ratios_error"] = f"{e}"
        ratios = None

    # --- 4) Agentic prediction (only if ratios available) ---
    try:
        if "ratios" in cache_data:
            ctx = StockSignalInput(
                ticker=symbol,
                ratios=cache_data["ratios"],
            )
            signal = run_stock_signal(ctx)
            cache_data["signal"] = signal.model_dump()
    except Exception as e:
        cache_data["signal_error"] = f"{e}"

    # --- 5) Save to Firestore ---
    cache_ref.set(cache_data, merge=True)

# ======================== MAIN ================================

if __name__ == "__main__":
    # Dev only
    app.run(host="0.0.0.0", port=5000, debug=True)

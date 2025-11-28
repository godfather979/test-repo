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

    doc = user_ref.get()
    wishlist = doc.to_dict().get("wishlist", [])

    return jsonify({"userID": uid, "wishlist": wishlist}), 200


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

# ======================== MAIN ================================

if __name__ == "__main__":
    # Dev only
    app.run(host="0.0.0.0", port=5000, debug=True)

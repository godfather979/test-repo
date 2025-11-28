# functions/chart_prediction.py

import base64
import json
import os
import re
from typing import Dict, Any

from groq import Groq
from dotenv import load_dotenv

# Load env vars
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv(
    "GROQ_VISION_MODEL",
    "meta-llama/llama-4-maverick-17b-128e-instruct"
)

if not API_KEY:
    raise RuntimeError("GROQ_API_KEY not found in environment (.env)")


def encode_image(path: str) -> str:
    """
    Read image and return base64-encoded string.
    """
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def detect_chart_pattern(image_path: str) -> Dict[str, Any]:
    """
    Call Groq vision model on the given candlestick chart image.
    Returns a Python dict:
    {
      "pattern_found": bool,
      "pattern_name": str,
      "confidence": str,
      "explanation": str
    }
    """
    b64 = encode_image(image_path)

    client = Groq(api_key=API_KEY)

    prompt = """
You are an expert stock market technical analyst.
You look at a candlestick chart image and identify if any classical chart pattern
is clearly visible, such as:
- Head and Shoulders
- Inverse Head and Shoulders
- Double Top / Double Bottom
- Cup and Handle
- Ascending / Descending Triangle
- Symmetrical Triangle
- Bullish / Bearish Flag
- Wedge patterns (Rising/Falling)
- Rounding Bottom
- Trend reversal / breakout setup

Respond only in JSON like this example:

{
  "pattern_found": true,
  "pattern_name": "Double Bottom",
  "confidence": "moderate",
  "explanation": "two clear lows forming W-shape near same level, strong bounce after second low"
}

If no clear pattern appears, return:

{
  "pattern_found": false,
  "pattern_name": "None",
  "confidence": "low",
  "explanation": "No reliable or identifiable classical chart pattern present"
}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{b64}"
                        }
                    }
                ]
            }
        ],
        temperature=0,
        max_tokens=700,
    )

    raw = response.choices[0].message.content.strip()

    # Clean markdown fences if any
    clean = re.sub(r"^```(?:json)?", "", raw).strip()
    clean = re.sub(r"```$", "", clean).strip()

    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        # Fallback basic structure if LLM output is slightly off
        data = {
            "pattern_found": False,
            "pattern_name": "ParseError",
            "confidence": "low",
            "explanation": f"Could not parse model JSON. Raw output: {clean}",
        }

    return data

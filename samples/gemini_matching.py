"""Gemini API を使った画像比較サンプルスクリプト

環境変数 GEMINI_API_KEY に Google AI Studio で取得した API キーを設定してから実行してください。
"""

import json
import os
import sys
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

# 画像パス設定
image1_path = Path("sample_images/roten01.jpg")
image2_path = Path("sample_images/roten03.jpg")

if not image1_path.exists() or not image2_path.exists():
    print(
        "サンプル画像が見つかりません。sample_images/ ディレクトリを確認してください。",
        file=sys.stderr,
    )
    sys.exit(1)

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("環境変数 GEMINI_API_KEY が設定されていません。", file=sys.stderr)
    sys.exit(1)

genai.configure(api_key=api_key)
model_name = os.getenv("GEMINI_MODEL")
model = genai.GenerativeModel(model_name)

prompt = (
    "Compare these two hotel photos and respond ONLY with a JSON object exactly in this format: "
    '{"score": <float 0-1>, "decision": "<same|different|uncertain>", "reason": "<short explanation in Japanese>"} '
    "where score indicates visual similarity (1.0 = identical). "
    "Choose 'same' only if you are confident they show the same hotel, 'different' if clearly not, otherwise use 'uncertain'. "
    "Do not add any text outside the JSON and do not use Markdown code fences."
)

with Image.open(image1_path) as img:
    image1 = img.convert("RGB")

with Image.open(image2_path) as img:
    image2 = img.convert("RGB")

try:
    response = model.generate_content([image1, image2, prompt])
except Exception as exc:
    print(f"Gemini API 呼び出しに失敗しました: {exc}", file=sys.stderr)
    sys.exit(1)

text = response.text if hasattr(response, "text") else None
if not text:
    print("Gemini API からテキスト応答が得られませんでした。", file=sys.stderr)
    sys.exit(1)

try:
    result = json.loads(text)
except json.JSONDecodeError:
    print("Gemini 応答を JSON として解釈できませんでした:\n")
    print(text)
    sys.exit(1)

score = result.get("score")
decision = result.get("decision")
reason = result.get("reason")

print("比較対象:")
print(f"  画像1: {image1_path}")
print(f"  画像2: {image2_path}")
print("Gemini 応答:")
print(f"  判定: {decision}")
print(f"  類似度スコア: {score}")
print(f"  コメント: {reason}")

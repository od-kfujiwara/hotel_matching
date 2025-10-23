"""Gemini を利用した AI 画像マッチング"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, List

import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

METHOD_NAME = "gemini"
_DEFAULT_MODEL = "gemini-2.5-flash"
_DEFAULT_TOP_N = 3

load_dotenv()

_MODEL_NAME = os.getenv("GEMINI_MODEL", _DEFAULT_MODEL)
_API_KEY = os.getenv("GEMINI_API_KEY")
try:
    _TOP_N_IMAGES = int(os.getenv("GEMINI_TOP_N", str(_DEFAULT_TOP_N)))
except ValueError:
    _TOP_N_IMAGES = _DEFAULT_TOP_N
_TOP_N_IMAGES = max(1, _TOP_N_IMAGES)

_MODEL: genai.GenerativeModel | None = None


def compare_gemini(
    images1: Iterable[str],
    images2: Iterable[str],
    threshold: float,
    *,
    top_n: int = _TOP_N_IMAGES,
) -> List[dict]:
    """Gemini API を使ってホテル画像のマッチングを判定する"""
    model = _get_model()

    tour_selected = _select_images(images1, top_n)
    airtrip_selected = _select_images(images2, top_n)

    pair_paths = list(zip(tour_selected, airtrip_selected))
    if not pair_paths:
        return []

    prompt = (
        "Compare these hotel photos from two sources and respond ONLY with a JSON object exactly in this format: "
        '{"score": <float 0-1>, "decision": "<same|different|uncertain>", "reason": "<short explanation in Japanese>"} '
        "where score indicates visual similarity (1.0 = identical). "
        "Choose 'same' only if you are confident they show the same hotel, 'different' if clearly not, otherwise use 'uncertain'. "
        "Do not add any text outside the JSON and do not use Markdown code fences."
    )

    matches: List[dict] = []
    for index, (tour_path, airtrip_path) in enumerate(pair_paths, start=1):
        tour_image = _load_image(tour_path)
        airtrip_image = _load_image(airtrip_path)

        if tour_image is None or airtrip_image is None:
            continue

        parts: List[object] = [
            f"tour.ne.jp image #{index}: {Path(tour_path).name}",
            tour_image,
            f"airtrip.jp image #{index}: {Path(airtrip_path).name}",
            airtrip_image,
            prompt,
        ]

        try:
            response = model.generate_content(parts)
        except Exception as exc:
            raise RuntimeError(f"Gemini API 呼び出しに失敗しました: {exc}") from exc

        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini API からテキスト応答が得られませんでした。")

        try:
            result = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Gemini 応答を JSON として解釈できませんでした: {text}"
            ) from exc

        score = _to_float(result.get("score"))
        decision = str(result.get("decision", "")).strip().lower()
        if decision not in {"same", "different", "uncertain"}:
            decision = "uncertain"
        reason = str(result.get("reason", "")).strip()

        similarity = score if score is not None else 0.0
        passed_threshold = score is not None and score >= threshold

        matches.append(
            {
                "image1": Path(tour_path).name,
                "image2": Path(airtrip_path).name,
                "tour_images": [Path(tour_path).name],
                "airtrip_images": [Path(airtrip_path).name],
                "similarity": float(similarity),
                "decision": decision,
                "reason": reason,
                "passed_threshold": passed_threshold,
                "method": METHOD_NAME,
            }
        )

    return matches


def _get_model() -> genai.GenerativeModel:
    global _MODEL
    if _MODEL is None:
        if not _API_KEY:
            raise RuntimeError("環境変数 GEMINI_API_KEY が設定されていません。")
        genai.configure(api_key=_API_KEY)
        _MODEL = genai.GenerativeModel(_MODEL_NAME)
    return _MODEL


def _select_images(images: Iterable[str], top_n: int) -> List[str]:
    return [p for _, p in zip(range(top_n), images)]


def _load_image(path: str) -> Image.Image | None:
    try:
        with Image.open(path) as img:
            return img.convert("RGB")
    except Exception as exc:
        print(f"Gemini 用画像読み込みに失敗: {path}: {exc}")
        return None


def _to_float(value) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None

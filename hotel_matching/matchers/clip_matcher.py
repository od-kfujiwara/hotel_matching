"""CLIP による画像マッチング関数"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List

import clip
import torch
from PIL import Image

METHOD_NAME = "clip"
_DEFAULT_MODEL_NAME = "ViT-B/32"

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_MODEL = None
_PREPROCESS = None


def compare_clip(
    images1: Iterable[str],
    images2: Iterable[str],
    threshold: float,
    *,
    model_name: str = _DEFAULT_MODEL_NAME,
) -> List[dict]:
    """CLIP を用いて 2 つの画像群の類似度を評価する"""
    model, preprocess = _get_model(model_name)

    embeddings1 = _encode_images(images1, model, preprocess)
    embeddings2 = _encode_images(images2, model, preprocess)

    matches = []
    for img1_path, emb1 in embeddings1.items():
        for img2_path, emb2 in embeddings2.items():
            similarity = _cosine_similarity(emb1, emb2)

            if similarity >= threshold:
                matches.append(
                    {
                        "image1": os.path.basename(img1_path),
                        "image2": os.path.basename(img2_path),
                        "similarity": float(similarity),
                        "method": METHOD_NAME,
                        "clip_model": model_name,
                    }
                )

    matches.sort(key=lambda x: x["similarity"], reverse=True)
    return matches


def _get_model(model_name: str):
    global _MODEL, _PREPROCESS

    if _MODEL is None or _PREPROCESS is None:
        model, preprocess = clip.load(model_name, device=_DEVICE)
        model.eval()
        _MODEL = model
        _PREPROCESS = preprocess

    return _MODEL, _PREPROCESS


def _encode_images(image_paths: Iterable[str], model, preprocess):
    embeddings = {}
    for img_path in image_paths:
        try:
            image = preprocess(Image.open(Path(img_path))).unsqueeze(0).to(_DEVICE)
            with torch.no_grad():
                features = model.encode_image(image)
            normalized = torch.nn.functional.normalize(features, dim=-1).cpu()
            embeddings[img_path] = normalized
        except Exception as exc:
            print(f"CLIP処理エラー {img_path}: {exc}")
    return embeddings


def _cosine_similarity(embedding1: torch.Tensor, embedding2: torch.Tensor) -> float:
    # 特徴量を正規化しているので内積がそのままコサイン類似度になる
    similarity = torch.matmul(embedding1, embedding2.T).item()
    return similarity

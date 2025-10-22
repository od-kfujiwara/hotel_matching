"""平均ハッシュを利用したマッチング関数"""

from __future__ import annotations

import os
from typing import Iterable, List

import imagehash
from PIL import Image


METHOD_NAME = "hash"


def compare_hash(
    images1: Iterable[str],
    images2: Iterable[str],
    threshold: float,
) -> List[dict]:
    hashes1 = _compute_hashes(images1)
    hashes2 = _compute_hashes(images2)

    matches = []
    for img1_path, hash1 in hashes1.items():
        for img2_path, hash2 in hashes2.items():
            diff = hash1 - hash2
            similarity = 1 - diff / len(hash1.hash) ** 2

            if similarity >= threshold:
                matches.append(
                    {
                        "image1": os.path.basename(img1_path),
                        "image2": os.path.basename(img2_path),
                        "similarity": float(similarity),
                        "hash_distance": int(diff),
                        "method": METHOD_NAME,
                    }
                )

    matches.sort(key=lambda x: x["similarity"], reverse=True)
    return matches


def _compute_hashes(image_paths: Iterable[str]):
    hashes = {}
    for img_path in image_paths:
        try:
            img = Image.open(img_path)
            hashes[img_path] = imagehash.average_hash(img)
        except Exception as exc:
            print(f"画像処理エラー {img_path}: {exc}")
    return hashes

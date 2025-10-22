"""pHash を利用したマッチング関数"""

from __future__ import annotations

import os
from typing import Iterable, List

import imagehash
from PIL import Image

METHOD_NAME = "phash"


def compare_phash(
    images1: Iterable[str],
    images2: Iterable[str],
    threshold: float,
) -> List[dict]:
    hashes1 = _compute_hashes(images1)
    hashes2 = _compute_hashes(images2)

    matches: List[dict] = []
    for img1_path, hash1 in hashes1.items():
        for img2_path, hash2 in hashes2.items():
            diff = hash1 - hash2
            hash_size = len(hash1.hash) ** 2
            similarity = 1 - diff / hash_size

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
            with Image.open(img_path) as img:
                hashes[img_path] = imagehash.phash(img)
        except Exception as exc:
            print(f"pHash処理エラー {img_path}: {exc}")
    return hashes

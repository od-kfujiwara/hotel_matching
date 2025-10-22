"""ORB + RANSAC による特徴点マッチング関数"""

from __future__ import annotations

import os
from typing import Iterable, List

import cv2
import numpy as np


METHOD_NAME = "feature"


def compare_feature(
    images1: Iterable[str],
    images2: Iterable[str],
    threshold: float,
    *,
    orb_nfeatures: int = 1000,
    ratio_test: float = 0.75,
    ransac_reproj_threshold: float = 5.0,
) -> List[dict]:
    matches = []

    orb = cv2.ORB_create(nfeatures=orb_nfeatures)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    for img1_path in images1:
        for img2_path in images2:
            try:
                img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
                img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)

                if img1 is None or img2 is None:
                    print(f"画像読み込みエラー: {img1_path} or {img2_path}")
                    continue

                img1_resized, img2_resized = _resize_pair(img1, img2)

                kp1, des1 = orb.detectAndCompute(img1_resized, None)
                kp2, des2 = orb.detectAndCompute(img2_resized, None)

                if des1 is None or des2 is None or len(des1) < 2 or len(des2) < 2:
                    continue

                knn_matches = bf.knnMatch(des1, des2, k=2)
                good_matches = _apply_ratio_test(knn_matches, ratio_test)

                if len(good_matches) < 4:
                    continue

                similarity, stats = _evaluate_matches(
                    good_matches, kp1, kp2, ransac_reproj_threshold
                )

                if similarity >= threshold:
                    matches.append(
                        {
                            "image1": os.path.basename(img1_path),
                            "image2": os.path.basename(img2_path),
                            "similarity": float(similarity),
                            **stats,
                            "method": METHOD_NAME,
                        }
                    )

            except Exception as exc:
                print(f"特徴点マッチングエラー {img1_path} vs {img2_path}: {exc}")

    matches.sort(key=lambda x: x["similarity"], reverse=True)
    return matches


def _resize_pair(img1, img2):
    h1, _ = img1.shape[:2]
    h2, _ = img2.shape[:2]
    target_height = min(h1, h2)
    return (
        _resize_with_aspect_ratio(img1, target_height),
        _resize_with_aspect_ratio(img2, target_height),
    )


def _resize_with_aspect_ratio(img, target_height):
    h, w = img.shape[:2]
    aspect_ratio = w / h
    new_width = int(target_height * aspect_ratio)
    return cv2.resize(img, (new_width, target_height), interpolation=cv2.INTER_AREA)


def _apply_ratio_test(knn_matches, ratio_test):
    good_matches = []
    for match_pair in knn_matches:
        if len(match_pair) == 2:
            m, n = match_pair
            if m.distance < ratio_test * n.distance:
                good_matches.append(m)
    return good_matches


def _evaluate_matches(good_matches, kp1, kp2, ransac_reproj_threshold):
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, ransac_reproj_threshold)

    if mask is None:
        return 0.0, {}

    inliers = [good_matches[i] for i in range(len(good_matches)) if mask[i]]

    if len(inliers) == 0:
        return 0.0, {}

    avg_distance = sum(m.distance for m in inliers) / len(inliers)
    similarity = 1 / (1 + avg_distance)
    inlier_ratio = len(inliers) / len(good_matches)

    return similarity, {
        "inlier_count": len(inliers),
        "total_matches": len(good_matches),
        "inlier_ratio": float(inlier_ratio),
        "avg_distance": float(avg_distance),
    }

"""
画像マッチング手法を提供するモジュール

このモジュールは複数の画像マッチング手法を提供します:
- 平均ハッシュ法 (Average Hash)
- 特徴点マッチング (ORB + RANSAC)
"""

import os
import cv2
import numpy as np
from PIL import Image
import imagehash


def compare_with_hash(images1, images2, threshold=0.9):
    """
    平均ハッシュ法で画像を比較

    Args:
        images1 (list): 1つ目の画像パスのリスト
        images2 (list): 2つ目の画像パスのリスト
        threshold (float): 類似度閾値 (0-1)

    Returns:
        list: マッチ結果のリスト
            [{'image1': str, 'image2': str, 'similarity': float, 'hash_distance': int}]
    """
    # 1つ目のセットのハッシュを計算
    hashes1 = {}
    for img_path in images1:
        try:
            img = Image.open(img_path)
            hash_val = imagehash.average_hash(img)
            hashes1[img_path] = hash_val
        except Exception as e:
            print(f"画像処理エラー {img_path}: {e}")

    # 2つ目のセットのハッシュを計算
    hashes2 = {}
    for img_path in images2:
        try:
            img = Image.open(img_path)
            hash_val = imagehash.average_hash(img)
            hashes2[img_path] = hash_val
        except Exception as e:
            print(f"画像処理エラー {img_path}: {e}")

    # すべてのペアを比較
    matches = []
    for img1_path, hash1 in hashes1.items():
        for img2_path, hash2 in hashes2.items():
            # ハッシュ距離を計算
            diff = hash1 - hash2
            # 類似度に変換（0-1スケール）
            similarity = 1 - diff / len(hash1.hash) ** 2

            if similarity >= threshold:
                matches.append({
                    'image1': os.path.basename(img1_path),
                    'image2': os.path.basename(img2_path),
                    'similarity': float(similarity),
                    'hash_distance': int(diff),
                    'method': 'hash'
                })

    # 類似度順にソート（高い順）
    matches.sort(key=lambda x: x['similarity'], reverse=True)

    return matches


def _resize_with_aspect_ratio(img, target_height):
    """
    アスペクト比を保ったまま画像をリサイズ

    Args:
        img: 入力画像
        target_height: 目標の高さ

    Returns:
        リサイズされた画像
    """
    h, w = img.shape[:2]
    aspect_ratio = w / h
    new_width = int(target_height * aspect_ratio)
    return cv2.resize(img, (new_width, target_height), interpolation=cv2.INTER_AREA)


def compare_with_feature_matching(images1, images2, threshold=0.9):
    """
    特徴点マッチング（ORB + Lowe's ratio test + RANSAC）で画像を比較

    Args:
        images1 (list): 1つ目の画像パスのリスト
        images2 (list): 2つ目の画像パスのリスト
        threshold (float): 類似度閾値 (0-1)

    Returns:
        list: マッチ結果のリスト
            [{'image1': str, 'image2': str, 'similarity': float,
              'inlier_count': int, 'inlier_ratio': float}]
    """
    matches = []

    # ORB検出器を作成
    orb = cv2.ORB_create(nfeatures=1000)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    for img1_path in images1:
        for img2_path in images2:
            try:
                # 画像を読み込み
                img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
                img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)

                if img1 is None or img2 is None:
                    print(f"画像読み込みエラー: {img1_path} or {img2_path}")
                    continue

                # 画像サイズを統一（比率を保ったまま）
                h1, w1 = img1.shape[:2]
                h2, w2 = img2.shape[:2]
                target_height = min(h1, h2)

                img1_resized = _resize_with_aspect_ratio(img1, target_height)
                img2_resized = _resize_with_aspect_ratio(img2, target_height)

                # 特徴点検出
                kp1, des1 = orb.detectAndCompute(img1_resized, None)
                kp2, des2 = orb.detectAndCompute(img2_resized, None)

                if des1 is None or des2 is None or len(des1) < 2 or len(des2) < 2:
                    # 特徴点が検出されない場合はスキップ
                    continue

                # knnMatchで上位2件を取得
                knn_matches = bf.knnMatch(des1, des2, k=2)

                # 比率テスト（Lowe's ratio test）
                good_matches = []
                for match_pair in knn_matches:
                    if len(match_pair) == 2:
                        m, n = match_pair
                        if m.distance < 0.75 * n.distance:
                            good_matches.append(m)

                if len(good_matches) < 4:
                    # RANSAC適用に必要な最小マッチ数に満たない場合はスキップ
                    continue

                # RANSACでホモグラフィ推定
                src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

                M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

                if mask is None:
                    continue

                # インライア（正しいマッチ）のみ抽出
                inliers = [good_matches[i] for i in range(len(good_matches)) if mask[i]]

                if len(inliers) == 0:
                    continue

                # 類似度スコア計算
                avg_distance = sum([m.distance for m in inliers]) / len(inliers)
                similarity = 1 / (1 + avg_distance)
                inlier_ratio = len(inliers) / len(good_matches)

                if similarity >= threshold:
                    matches.append({
                        'image1': os.path.basename(img1_path),
                        'image2': os.path.basename(img2_path),
                        'similarity': float(similarity),
                        'inlier_count': len(inliers),
                        'total_matches': len(good_matches),
                        'inlier_ratio': float(inlier_ratio),
                        'avg_distance': float(avg_distance),
                        'method': 'feature'
                    })

            except Exception as e:
                print(f"特徴点マッチングエラー {img1_path} vs {img2_path}: {e}")

    # 類似度順にソート（高い順）
    matches.sort(key=lambda x: x['similarity'], reverse=True)

    return matches

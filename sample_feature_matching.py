import cv2
import matplotlib.pyplot as plt
import numpy as np

# ====== 1. 画像読み込み ======
# imagesフォルダ内の既存画像を使用
img1 = cv2.imread('sample_images/day01.jpg', cv2.IMREAD_GRAYSCALE)
img2 = cv2.imread('sample_images/day02.jpg', cv2.IMREAD_GRAYSCALE)

if img1 is None or img2 is None:
    raise ValueError("画像が読み込めません。パスを確認してください。")

# ====== 2. 画像サイズを統一（比率を保ったままリサイズ） ======
def resize_with_aspect_ratio(img, target_height):
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

# 両画像の高さを取得
h1, w1 = img1.shape[:2]
h2, w2 = img2.shape[:2]

# 短い方の高さに合わせる
target_height = min(h1, h2)

# 画像をリサイズ
img1_resized = resize_with_aspect_ratio(img1, target_height)
img2_resized = resize_with_aspect_ratio(img2, target_height)

print(f"元の画像サイズ: img1={img1.shape}, img2={img2.shape}")
print(f"リサイズ後: img1={img1_resized.shape}, img2={img2_resized.shape}")

# ====== 3. 特徴点検出（ORBを使用） ======
orb = cv2.ORB_create(nfeatures=1000)

kp1, des1 = orb.detectAndCompute(img1_resized, None)
kp2, des2 = orb.detectAndCompute(img2_resized, None)

# ====== 4. マッチング（knnMatchで上位2件を取得） ======
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
matches = bf.knnMatch(des1, des2, k=2)

# ====== 5. 比率テストで良いマッチのみ抽出（Lowe's ratio test） ======
good_matches = []
for match_pair in matches:
    if len(match_pair) == 2:
        m, n = match_pair
        # 最も近い距離が2番目に近い距離の75%以下なら採用
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)

print(f"比率テスト後のマッチ数: {len(good_matches)}")

# ====== 6. RANSACでホモグラフィ推定（誤マッチ除去） ======
if len(good_matches) >= 4:
    # マッチした特徴点の座標を取得
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    # RANSACでホモグラフィ行列を推定
    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    # インライア（正しいマッチ）のみ抽出
    inliers = [good_matches[i] for i in range(len(good_matches)) if mask[i]]

    print(f"RANSAC後のインライア数: {len(inliers)}/{len(good_matches)}")
    print(f"インライア率: {len(inliers)/len(good_matches)*100:.1f}%")

    # ====== 7. インライアの平均距離で類似度スコア化 ======
    if len(inliers) > 0:
        avg_distance = sum([m.distance for m in inliers]) / len(inliers)
        similarity_score = 1 / (1 + avg_distance)
        ransac_matches = inliers
    else:
        print("警告: インライアが0件でした")
        avg_distance = float('inf')
        similarity_score = 0.0
        ransac_matches = []
else:
    print(f"警告: マッチ数が不足しています（{len(good_matches)}件）。RANSAC適用不可")
    avg_distance = sum([m.distance for m in good_matches]) / len(good_matches) if good_matches else float('inf')
    similarity_score = 1 / (1 + avg_distance) if good_matches else 0.0
    ransac_matches = good_matches

print(f"平均距離: {avg_distance:.2f}")
print(f"類似度スコア: {similarity_score:.4f}")

# ====== 8. 結果可視化（RANSAC後のマッチを表示） ======
matched_img = cv2.drawMatches(img1_resized, kp1, img2_resized, kp2, ransac_matches, None, flags=2)

# 画像をファイルとして保存（WSL環境でGUIが使えない場合の対応）
plt.figure(figsize=(15, 8))
plt.imshow(matched_img, cmap='gray')
plt.title(f"Feature Matching (Similarity Score = {similarity_score:.4f})")
plt.axis('off')

# 結果を画像ファイルとして保存
output_path = 'matched_result.png'
plt.savefig(output_path, bbox_inches='tight', dpi=150)
print(f"\n結果画像を保存しました: {output_path}")

# GUIが使える環境では表示も試みる
try:
    plt.show()
except:
    print("注: GUI表示はスキップされました（画像ファイルを確認してください）")

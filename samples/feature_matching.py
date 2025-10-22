import cv2
import matplotlib.pyplot as plt

# ====== 1. 画像読み込み ======
# imagesフォルダ内の既存画像を使用
img1 = cv2.imread("./sample_images/day01.jpg", cv2.IMREAD_GRAYSCALE)
img2 = cv2.imread("./sample_images/day02.jpg", cv2.IMREAD_GRAYSCALE)

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

# ====== 3. マッチング（Brute-Force with Hamming距離） ======
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
matches = bf.match(des1, des2)

# 類似度を上げるために距離でソート
matches = sorted(matches, key=lambda x: x.distance)

# ====== 4. 上位マッチの平均距離を指標に類似度スコア化 ======
good_matches = matches[:50]  # 上位50件のみ採用
avg_distance = sum([m.distance for m in good_matches]) / len(good_matches)
similarity_score = 1 / (1 + avg_distance)  # 距離の逆数をスコアに

print(f"平均距離: {avg_distance:.2f}")
print(f"類似度スコア: {similarity_score:.4f}")

# ====== 5. 結果可視化 ======
matched_img = cv2.drawMatches(
    img1_resized, kp1, img2_resized, kp2, good_matches, None, flags=2
)

# 画像をファイルとして保存（WSL環境でGUIが使えない場合の対応）
plt.figure(figsize=(15, 8))
plt.imshow(matched_img, cmap="gray")
plt.title(f"Feature Matching (Similarity Score = {similarity_score:.4f})")
plt.axis("off")

# 結果を画像ファイルとして保存
output_path = "matched_result.png"
plt.savefig(output_path, bbox_inches="tight", dpi=150)
print(f"\n結果画像を保存しました: {output_path}")

# GUIが使える環境では表示も試みる
try:
    plt.show()
except:
    print("注: GUI表示はスキップされました（画像ファイルを確認してください）")

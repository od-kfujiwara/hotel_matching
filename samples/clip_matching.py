import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="clip")

import clip
import torch
from PIL import Image

# 画像パス設定
image1_path = "./sample_images/day01.jpg"
image2_path = "./sample_images/day02.jpg"

# モデル読み込み
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# 画像読み込みと前処理
image1 = preprocess(Image.open(image1_path)).unsqueeze(0).to(device)
image2 = preprocess(Image.open(image2_path)).unsqueeze(0).to(device)

# 埋め込み（特徴ベクトル）を取得
with torch.no_grad():
    features1 = model.encode_image(image1)
    features2 = model.encode_image(image2)

# 正規化してコサイン類似度を計算
similarity = torch.nn.functional.cosine_similarity(features1, features2)
print("比較対象:")
print(f"  画像1: {image1_path}")
print(f"  画像2: {image2_path}")
print(f"類似度: {similarity.item():.4f}")

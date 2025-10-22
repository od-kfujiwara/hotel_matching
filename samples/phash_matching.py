import imagehash
from PIL import Image

# 画像パス設定
img1 = Image.open("./sample_images/day01.jpg")
img2 = Image.open("./sample_images/day02.jpg")

phash1 = imagehash.phash(img1)
phash2 = imagehash.phash(img2)

print(f"Image 1 hash: {phash1}")
print(f"Image 2 hash: {phash2}")

print("pHash差:", phash1 - phash2)

diff = phash1 - phash2
similarity = 1 - diff / len(phash1.hash) ** 2

print(f"Hash距離: {diff}")
print(f"類似度（0〜1）: {similarity:.2f}")

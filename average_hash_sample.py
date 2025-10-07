from PIL import Image
import imagehash

img1 = Image.open("images/tour_64586_8.jpg")
img2 = Image.open("images/airtrip_39204H282_29.jpg")

hash1 = imagehash.average_hash(img1)
hash2 = imagehash.average_hash(img2)

print(f"Image 1 hash: {hash1}")
print(f"Image 2 hash: {hash2}")

diff = hash1 - hash2
similarity = 1 - diff / len(hash1.hash) ** 2

print(f"Hash距離: {diff}")
print(f"類似度（0〜1）: {similarity:.2f}")

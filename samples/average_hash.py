"""
平均ハッシュマッチャーで2枚の画像を比較するサンプルスクリプト。
"""

from hotel_matching.matcher import compare


def main():
    images1 = ["images/tour_64586_8.jpg"]
    images2 = ["images/airtrip_39204H282_29.jpg"]

    threshold = 0.9
    matches = compare("hash", images1, images2, threshold)

    if not matches:
        print(f"しきい値 {threshold} では一致が見つかりませんでした。")
        return

    for match in matches:
        print("一致しました！")
        print(f"  画像1: {match['image1']}")
        print(f"  画像2: {match['image2']}")
        print(f"  類似度: {match['similarity']:.4f}")
        print(f"  ハッシュ距離: {match['hash_distance']}")


if __name__ == "__main__":
    main()

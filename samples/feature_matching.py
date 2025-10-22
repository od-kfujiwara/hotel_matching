"""
ORB + RANSAC 特徴点マッチャーをサンプル画像で実行するスクリプト。
"""

from hotel_matching.matcher import compare


def main():
    images1 = ["sample_images/day01.jpg"]
    images2 = ["sample_images/day02.jpg"]

    threshold = 0.04
    matches = compare("feature", images1, images2, threshold)

    if not matches:
        print(f"しきい値 {threshold} では特徴点の一致が見つかりませんでした。")
        return

    for match in matches:
        print("一致しました！")
        print(f"  画像1: {match['image1']}")
        print(f"  画像2: {match['image2']}")
        print(f"  類似度: {match['similarity']:.4f}")
        print(f"  インライア数: {match['inlier_count']}/{match['total_matches']}")
        print(f"  インライア率: {match['inlier_ratio']:.2f}")
        print(f"  平均距離: {match['avg_distance']:.2f}")


if __name__ == "__main__":
    main()

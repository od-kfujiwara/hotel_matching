import glob
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

from hotel_matching.matcher import compare
from hotel_matching.scraper import (
    extract_hotel_images_airtrip,
    extract_hotel_images_tour,
)

BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

# 画像フォルダの設定
IMAGES_FOLDER = BASE_DIR / "images"
IMAGES_FOLDER.mkdir(parents=True, exist_ok=True)


def cleanup_images(pattern):
    """
    指定されたパターンに一致する画像を削除

    引数:
        pattern (str): 削除する画像のGlobパターン (例: "tour_12345_*")
    """
    files = glob.glob(str(IMAGES_FOLDER / pattern))
    for file in files:
        try:
            os.remove(file)
            print(f"削除しました: {file}")
        except Exception as e:
            print(f"削除に失敗しました {file}: {e}")


@app.route("/")
def index():
    """メインページを表示"""
    return render_template("index.html")


@app.route("/api/scrape_and_compare", methods=["POST"])
def scrape_and_compare():
    """
    両サイトから画像をスクレイピングして比較
    期待されるJSON: {"tour_id": "...", "airtrip_id": "...", "threshold": 0.9, "method": "hash"}
    """
    try:
        data = request.get_json() or {}
        tour_id = data.get("tour_id", "").strip()
        airtrip_id = data.get("airtrip_id", "").strip()
        raw_threshold = data.get("threshold")
        method = data.get("method")

        if not tour_id or not airtrip_id:
            return jsonify({"error": "tour_idとairtrip_idの両方が必要です"}), 400

        if not method:
            return jsonify({"error": "マッチング手法が指定されていません"}), 400

        if raw_threshold is None:
            return jsonify({"error": "閾値が指定されていません"}), 400

        try:
            threshold = float(raw_threshold)
        except (TypeError, ValueError):
            return jsonify({"error": "閾値は数値で指定してください"}), 400

        # ステップ1: 既存の画像をすべて削除
        cleanup_images("*.jpg")
        cleanup_images("*.png")
        cleanup_images("*.webp")

        # ステップ2: tour.ne.jpからスクレイピング
        tour_images = extract_hotel_images_tour(tour_id)
        if not tour_images:
            return (
                jsonify({"error": "tour.ne.jpからの画像ダウンロードに失敗しました"}),
                500,
            )

        # ステップ3: airtrip.jpからスクレイピング
        airtrip_images = extract_hotel_images_airtrip(airtrip_id)
        if not airtrip_images:
            return (
                jsonify({"error": "airtrip.jpからの画像ダウンロードに失敗しました"}),
                500,
            )

        # ステップ4: 選択されたマッチング方法で比較
        try:
            matches = compare(method, tour_images, airtrip_images, threshold)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 500

        match_count = sum(1 for match in matches if match.get("passed_threshold", True))
        return jsonify(
            {
                "success": True,
                "tour_count": len(tour_images),
                "airtrip_count": len(airtrip_images),
                "total_comparisons": len(tour_images) * len(airtrip_images),
                "matches": matches,
                "match_count": match_count,
                "threshold": threshold,
                "method": method,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/images/<filename>")
def serve_image(filename):
    """imagesフォルダから画像を配信"""
    return send_from_directory(str(IMAGES_FOLDER), filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

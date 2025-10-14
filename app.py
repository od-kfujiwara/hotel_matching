from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import glob
from scraper import extract_hotel_images_tour, extract_hotel_images_airtrip
from matcher import compare_with_hash, compare_with_feature_matching

app = Flask(__name__)

# 画像フォルダの設定
IMAGES_FOLDER = 'images'
os.makedirs(IMAGES_FOLDER, exist_ok=True)


def cleanup_images(pattern):
    """
    指定されたパターンに一致する画像を削除

    Args:
        pattern (str): 削除する画像のGlobパターン (例: "tour_12345_*")
    """
    files = glob.glob(os.path.join(IMAGES_FOLDER, pattern))
    for file in files:
        try:
            os.remove(file)
            print(f"削除しました: {file}")
        except Exception as e:
            print(f"削除に失敗しました {file}: {e}")


@app.route('/')
def index():
    """メインページを表示"""
    return render_template('index.html')


@app.route('/api/scrape', methods=['POST'])
def scrape_images():
    """
    指定されたサイトからホテル画像をスクレイピング
    期待されるJSON: {"site": "tour" or "airtrip", "hotel_id": "..."}
    """
    try:
        data = request.get_json()
        site = data.get('site')
        hotel_id = data.get('hotel_id')

        if not site or not hotel_id:
            return jsonify({'error': 'siteまたはhotel_idが指定されていません'}), 400

        # 適切なスクレイパー関数を呼び出し
        if site == 'tour':
            downloaded = extract_hotel_images_tour(hotel_id)
        elif site == 'airtrip':
            downloaded = extract_hotel_images_airtrip(hotel_id)
        else:
            return jsonify({'error': '無効なサイト'}), 400

        # ダウンロードしたファイルのリストを返す（ファイル名のみ）
        filenames = [os.path.basename(f) for f in downloaded]

        return jsonify({
            'success': True,
            'count': len(filenames),
            'images': filenames,
            'pattern': f"{site}_{hotel_id}_*"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compare', methods=['POST'])
def compare_images():
    """
    2つのパターンの画像を比較
    期待されるJSON: {"pattern1": "...", "pattern2": "...", "threshold": 0.9, "method": "hash"}
    """
    try:
        data = request.get_json()
        pattern1 = data.get('pattern1', '')
        pattern2 = data.get('pattern2', '')
        threshold = float(data.get('threshold', 0.9))
        method = data.get('method', 'hash')  # デフォルトは平均ハッシュ法

        # 画像ファイルを取得
        images1 = sorted(glob.glob(os.path.join(IMAGES_FOLDER, pattern1)))
        images2 = sorted(glob.glob(os.path.join(IMAGES_FOLDER, pattern2)))

        if not images1:
            return jsonify({'error': f'パターンに一致する画像が見つかりません: {pattern1}'}), 400
        if not images2:
            return jsonify({'error': f'パターンに一致する画像が見つかりません: {pattern2}'}), 400

        if method not in ['hash', 'feature']:
            return jsonify({'error': '無効なマッチング方法です'}), 400

        # 選択されたマッチング方法で比較
        if method == 'hash':
            matches = compare_with_hash(images1, images2, threshold)
        else:  # method == 'feature'
            matches = compare_with_feature_matching(images1, images2, threshold)

        return jsonify({
            'success': True,
            'total_images1': len(images1),
            'total_images2': len(images2),
            'total_comparisons': len(images1) * len(images2),
            'matches': matches,
            'match_count': len(matches),
            'threshold': threshold,
            'method': method
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scrape_and_compare', methods=['POST'])
def scrape_and_compare():
    """
    両サイトから画像をスクレイピングして比較
    期待されるJSON: {"tour_id": "...", "airtrip_id": "...", "threshold": 0.9, "method": "hash"}
    """
    try:
        data = request.get_json()
        tour_id = data.get('tour_id', '').strip()
        airtrip_id = data.get('airtrip_id', '').strip()
        threshold = float(data.get('threshold', 0.9))
        method = data.get('method', 'hash')  # デフォルトは平均ハッシュ法

        if not tour_id or not airtrip_id:
            return jsonify({'error': 'tour_idとairtrip_idの両方が必要です'}), 400

        if method not in ['hash', 'feature']:
            return jsonify({'error': '無効なマッチング方法です'}), 400

        # ステップ1: 既存の画像をすべて削除
        cleanup_images('*.jpg')
        cleanup_images('*.png')
        cleanup_images('*.webp')

        # ステップ2: tour.ne.jpからスクレイピング
        tour_images = extract_hotel_images_tour(tour_id)
        if not tour_images:
            return jsonify({'error': 'tour.ne.jpからの画像ダウンロードに失敗しました'}), 500

        # ステップ3: airtrip.jpからスクレイピング
        airtrip_images = extract_hotel_images_airtrip(airtrip_id)
        if not airtrip_images:
            return jsonify({'error': 'airtrip.jpからの画像ダウンロードに失敗しました'}), 500

        # ステップ4: 選択されたマッチング方法で比較
        if method == 'hash':
            matches = compare_with_hash(tour_images, airtrip_images, threshold)
        else:  # method == 'feature'
            matches = compare_with_feature_matching(tour_images, airtrip_images, threshold)

        return jsonify({
            'success': True,
            'tour_count': len(tour_images),
            'airtrip_count': len(airtrip_images),
            'total_comparisons': len(tour_images) * len(airtrip_images),
            'matches': matches,
            'match_count': len(matches),
            'threshold': threshold,
            'method': method
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/images/<filename>')
def serve_image(filename):
    """imagesフォルダから画像を配信"""
    return send_from_directory(IMAGES_FOLDER, filename)


@app.route('/api/images', methods=['GET'])
def list_images():
    """imagesフォルダ内のすべての画像をリスト表示"""
    try:
        all_images = glob.glob(os.path.join(IMAGES_FOLDER, '*.*'))
        # 画像ファイルのみフィルタ
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        images = [
            os.path.basename(f) for f in all_images
            if os.path.splitext(f)[1].lower() in image_extensions
        ]
        return jsonify({
            'success': True,
            'images': sorted(images)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

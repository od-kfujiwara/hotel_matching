import requests
from bs4 import BeautifulSoup
import os
import re


def extract_hotel_images_tour(hotel_id):
    """
    tour.ne.jpからホテル画像を抽出してダウンロード

    Args:
        hotel_id (str): tour.ne.jpのホテルID

    Returns:
        list: ダウンロードした画像ファイルパスのリスト
    """
    url = f"https://www.tour.ne.jp/j_hotel/{hotel_id}/"

    try:
        # ページを取得
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # HTMLをパース
        soup = BeautifulSoup(response.content, 'html.parser')

        # 「Area_hotel_photo_box」内を取得
        photo_box = soup.find(id="Area_hotel_photo_box")
        if not photo_box:
            print("id='Area_hotel_photo_box'の要素が見つかりませんでした")
            return []

        # photo_box中のすべての <img> タグを抽出
        hotel_images = photo_box.find_all('img')
        if not hotel_images:
            print("#Area_hotel_photo_box内に画像が見つかりませんでした")
            return []

        # 先頭の1枚（Area_photo_detail内）を除外
        hotel_images = hotel_images[1:]

        # imagesディレクトリが存在しない場合は作成
        os.makedirs('images', exist_ok=True)

        # 画像をダウンロード
        downloaded_files = []
        for idx, img_tag in enumerate(hotel_images, 1):
            try:
                img_url = img_tag.get('src', '')
                if not img_url:
                    continue

                # URLに適切なプロトコルを確保
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif not img_url.startswith('http'):
                    img_url = 'https://' + img_url

                # 画像をダウンロード
                img_response = requests.get(img_url, timeout=10)
                img_response.raise_for_status()

                # ファイル拡張子を判定
                ext = 'jpg'
                if '.png' in img_url.lower():
                    ext = 'png'
                elif '.webp' in img_url.lower():
                    ext = 'webp'

                # 画像を保存
                filename = f"images/tour_{hotel_id}_{idx}.{ext}"
                with open(filename, 'wb') as f:
                    f.write(img_response.content)

                downloaded_files.append(filename)
                print(f"ダウンロード完了: {filename}")

            except Exception as e:
                print(f"画像{idx}のダウンロードに失敗: {e}")

        return downloaded_files

    except requests.RequestException as e:
        print(f"ページ取得エラー: {e}")
        return []


def extract_hotel_images_airtrip(hotel_id):
    """
    airtrip.jpからホテル画像を抽出してダウンロード

    Args:
        hotel_id (str): airtrip.jpのホテルID

    Returns:
        list: ダウンロードした画像ファイルパスのリスト
    """
    url = f"https://domhotel.airtrip.jp/hotel/detail/{hotel_id}"

    try:
        # ページを取得
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # HTMLをパース
        soup = BeautifulSoup(response.content, 'html.parser')

        # すべての画像タグを検索
        img_tags = soup.find_all('img')

        # airtrip CDNのホテル画像のみを抽出
        hotel_images = []
        for img in img_tags:
            src = img.get('src', '')
            if 'cdn-domhotel.airtrip.jp' in src and '/hotel/img' in src:
                # 完全なURLを確保
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://cdn-domhotel.airtrip.jp' + src

                if src not in hotel_images:
                    hotel_images.append(src)

        # imagesディレクトリが存在しない場合は作成
        os.makedirs('images', exist_ok=True)

        # 画像をダウンロード
        downloaded_files = []
        for idx, img_url in enumerate(hotel_images, 1):
            try:
                # 画像をダウンロード
                img_response = requests.get(img_url, timeout=10)
                img_response.raise_for_status()

                # ファイル拡張子を判定
                ext = 'jpg'
                if '.png' in img_url.lower():
                    ext = 'png'
                elif '.webp' in img_url.lower():
                    ext = 'webp'

                # 画像を保存
                filename = f"images/airtrip_{hotel_id}_{idx}.{ext}"
                with open(filename, 'wb') as f:
                    f.write(img_response.content)

                downloaded_files.append(filename)
                print(f"ダウンロード完了: {filename}")

            except Exception as e:
                print(f"画像{idx}のダウンロードに失敗: {e}")

        return downloaded_files

    except requests.RequestException as e:
        print(f"ページ取得エラー: {e}")
        return []


def main():
    """スクレイパーを実行するメイン関数"""
    print("ホテル画像スクレイパー")
    print("=" * 40)
    print("サイトを選択:")
    print("1. tour.ne.jp")
    print("2. airtrip.jp")
    print("-" * 40)

    site_choice = input("選択してください (1 または 2): ").strip()

    if site_choice == '1':
        hotel_id = input("ホテルIDを入力 (例: 64586): ").strip()
        if not hotel_id:
            print("エラー: ホテルIDは空にできません")
            return

        print(f"\ntour.ne.jpからホテルID: {hotel_id} の画像を取得中")
        print("-" * 40)
        downloaded = extract_hotel_images_tour(hotel_id)

    elif site_choice == '2':
        hotel_id = input("ホテルIDを入力 (例: 39204H282): ").strip()
        if not hotel_id:
            print("エラー: ホテルIDは空にできません")
            return

        print(f"\nairtrip.jpからホテルID: {hotel_id} の画像を取得中")
        print("-" * 40)
        downloaded = extract_hotel_images_airtrip(hotel_id)

    else:
        print("エラー: 無効な選択です")
        return

    print("-" * 40)
    print(f"\n合計ダウンロード数: {len(downloaded)}枚")

    if downloaded:
        print("\nダウンロードしたファイル:")
        for file in downloaded:
            print(f"  - {file}")


if __name__ == "__main__":
    main()

"""
ホテル画像をスクレイピングしてダウンロードする
"""

import os
from typing import List

import requests
from bs4 import BeautifulSoup


def extract_hotel_images_tour(hotel_id: str) -> List[str]:
    """
    tour.ne.jp からホテル画像を取得して保存する

    引数:
        hotel_id: tour.ne.jp のホテルID

    戻り値:
        ダウンロードした画像ファイルパスのリスト
    """
    url = f"https://www.tour.ne.jp/j_hotel/{hotel_id}/"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        photo_box = soup.find(id="Area_hotel_photo_box")
        if not photo_box:
            print("id='Area_hotel_photo_box' の要素が見つかりませんでした")
            return []

        hotel_images = list(photo_box.find_all("img"))
        if not hotel_images:
            print("#Area_hotel_photo_box 内に画像が見つかりませんでした")
            return []

        hotel_images = hotel_images[1:]  # 先頭の1枚を除外

        os.makedirs("images", exist_ok=True)

        downloaded_files = []
        for idx, img_tag in enumerate(hotel_images, 1):
            try:
                src_attr = img_tag.get("src")
                if not isinstance(src_attr, str):
                    continue
                img_url = src_attr

                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif not img_url.startswith("http"):
                    img_url = "https://" + img_url

                img_response = requests.get(img_url, timeout=10)
                img_response.raise_for_status()

                ext = "jpg"
                lower_url = img_url.lower()
                if ".png" in lower_url:
                    ext = "png"
                elif ".webp" in lower_url:
                    ext = "webp"

                filename = f"images/tour_{hotel_id}_{idx}.{ext}"
                with open(filename, "wb") as f:
                    f.write(img_response.content)

                downloaded_files.append(filename)
                print(f"ダウンロード完了: {filename}")

            except Exception as exc:
                print(f"画像{idx}のダウンロードに失敗: {exc}")

        return downloaded_files

    except requests.RequestException as exc:
        print(f"ページ取得エラー: {exc}")
        return []


def extract_hotel_images_airtrip(hotel_id: str) -> List[str]:
    """
    airtrip.jp からホテル画像を取得して保存する

    引数:
        hotel_id: airtrip.jp のホテルID

    戻り値:
        ダウンロードした画像ファイルパスのリスト
    """
    url = f"https://domhotel.airtrip.jp/hotel/detail/{hotel_id}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        img_tags = soup.find_all("img")

        hotel_images: List[str] = []
        for img in img_tags:
            src_attr = img.get("src")
            if not isinstance(src_attr, str):
                continue
            src = src_attr

            if "cdn-domhotel.airtrip.jp" in src and "/hotel/img" in src:
                if src.startswith("//"):
                    src = "https:" + src
                elif src.startswith("/"):
                    src = "https://cdn-domhotel.airtrip.jp" + src

                if src not in hotel_images:
                    hotel_images.append(src)

        os.makedirs("images", exist_ok=True)

        downloaded_files = []
        for idx, img_url in enumerate(hotel_images, 1):
            try:
                img_response = requests.get(img_url, timeout=10)
                img_response.raise_for_status()

                ext = "jpg"
                lower_url = img_url.lower()
                if ".png" in lower_url:
                    ext = "png"
                elif ".webp" in lower_url:
                    ext = "webp"

                filename = f"images/airtrip_{hotel_id}_{idx}.{ext}"
                with open(filename, "wb") as f:
                    f.write(img_response.content)

                downloaded_files.append(filename)
                print(f"ダウンロード完了: {filename}")

            except Exception as exc:
                print(f"画像{idx}のダウンロードに失敗: {exc}")

        return downloaded_files

    except requests.RequestException as exc:
        print(f"ページ取得エラー: {exc}")
        return []

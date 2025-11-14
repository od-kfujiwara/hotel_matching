"""
ホテル画像をスクレイピングしてダウンロードする
"""

import os
from datetime import datetime, timedelta
from typing import List
from urllib.parse import urlparse, parse_qs

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
    Skygate (airtrip.jp) からホテル画像を取得して保存する

    引数:
        hotel_id: Skygate のホテルID

    戻り値:
        ダウンロードした画像ファイルパスのリスト
    """
    url = "https://www.skygate.co.jp/kokunai/tour/list/hotel_detail"

    # リトライ用のホテルコードリスト（動作しなくなったら検索可能な「札幌のホテル」に修正してください）
    retry_hotel_codes = ["3072939", "3228052", "1340731"]

    # 今日から1ヶ月後の日付を計算
    today = datetime.now()
    checkin_date = today + timedelta(days=30)
    checkout_date = checkin_date + timedelta(days=1)
    checkin_str = checkin_date.strftime("%Y%m%d")
    checkout_str = checkout_date.strftime("%Y%m%d")

    # Step 1: selectedItemKeyの取得
    selected_item_key = None
    for retry_code in retry_hotel_codes:
        params = {
            "rooms": "1",
            "checkinDate": checkin_str,
            "checkoutDate": checkout_str,
            "outwardDate": checkin_str,
            "homewardDate": checkout_str,
            "hotelCode": retry_code,
            "subAreaCode": "0101",
            "outwardDeparturePort": "TYO",
            "homewardArrivalPort": "TYO",
            "homewardDeparturePort": "CTS",
            "outwardArrivalPort": "CTS",
            "prefectureCode": "01",
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            selected_item_key = parse_qs(urlparse(response.url).query).get(
                "selectedItemKey", [None]
            )[0]

            if selected_item_key:
                break

        except requests.RequestException as exc:
            print(f"selectedItemKey取得エラー (ホテルコード: {retry_code}): {exc}")
            continue

    if not selected_item_key:
        print("selectedItemKeyの取得に失敗しました")
        return []

    # Step 2: ターゲットホテルで再検索
    params["hotelCode"] = hotel_id
    params["selectedItemKey"] = selected_item_key

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"再検索URL: {response.url}")
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        gallery_section = soup.find(attrs={"data-name": "hotel_detail_img_resource"})

        if not gallery_section:
            print("ホテル画像が見つかりませんでした")
            return []

        image_urls = []
        for img in gallery_section.find_all("img"):
            src = img.get("src")
            if src and ("i.travelapi.com" in src or "agoda.net" in src):
                image_urls.append(src)

        image_urls = list(dict.fromkeys(image_urls))  # 重複排除

        if not image_urls:
            print("ギャラリー画像が見つかりませんでした")
            return []

        os.makedirs("images", exist_ok=True)

        downloaded_files = []
        for idx, img_url in enumerate(image_urls, 1):
            try:
                img_response = requests.get(img_url, timeout=10)
                img_response.raise_for_status()

                url_lower = img_url.lower()
                ext = (
                    "png"
                    if ".png" in url_lower
                    else "webp" if ".webp" in url_lower else "jpg"
                )
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

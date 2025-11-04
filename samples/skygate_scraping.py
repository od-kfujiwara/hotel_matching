import os
import requests
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup


def test_skygate_access():
    """Skygate URLにアクセスしてホテル画像を取得"""
    url = "https://www.skygate.co.jp/kokunai/tour/list/hotel_detail"

    # リトライ用のホテルコードリスト（動作しなくなったら検索可能な「札幌のホテル」に修正してください）
    hotel_codes = ["3072939", "3228052", "1340731"]

    # 今日から1ヶ月後の日付を計算
    today = datetime.now()
    checkin_date = today + timedelta(days=30)
    checkout_date = checkin_date + timedelta(days=1)
    checkin_str = checkin_date.strftime("%Y%m%d")
    checkout_str = checkout_date.strftime("%Y%m%d")

    for hotel_code in hotel_codes:
        print(f"\n--- ホテルコード {hotel_code} で試行 ---")

        params = {
            "rooms": "1",
            "checkinDate": checkin_str,
            "checkoutDate": checkout_str,
            "outwardDate": checkin_str,
            "homewardDate": checkout_str,
            "hotelCode": hotel_code,
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
                print(f"✓ selectedItemKeyを取得できました: {selected_item_key}")

                target_hotel_code = input(
                    "\n検索したいホテルコードを入力してください: "
                )
                print(
                    f"\n--- ホテルコード {target_hotel_code} でselectedItemKeyを使って再検索 ---"
                )

                params["hotelCode"] = target_hotel_code
                params["selectedItemKey"] = selected_item_key

                try:
                    response2 = requests.get(url, params=params, timeout=10)
                    soup = BeautifulSoup(response2.content, "html.parser")
                    gallery_section = soup.find(
                        attrs={"data-name": "hotel_detail_img_resource"}
                    )

                    if not gallery_section:
                        print("✗ ギャラリーセクションが見つかりませんでした")
                    else:
                        image_urls = []
                        for img in gallery_section.find_all("img"):
                            src = img.get("src")

                            if src and "i.travelapi.com" in src:
                                image_urls.append(src)

                        image_urls = list(dict.fromkeys(image_urls))

                        os.makedirs("samples/images", exist_ok=True)
                        print(f"\n{len(image_urls)}枚の画像をダウンロード中...")
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
                                filename = f"samples/images/skygate_{target_hotel_code}_{idx}.{ext}"
                                with open(filename, "wb") as f:
                                    f.write(img_response.content)

                                print(f"  [{idx}/{len(image_urls)}] {filename}")

                            except Exception as exc:
                                print(f"  [{idx}/{len(image_urls)}] 失敗: {exc}")

                        print("\n✓ ダウンロード完了")

                except requests.RequestException as e:
                    print(f"再検索エラー: {e}")

                break
            else:
                print("✗ selectedItemKeyが見つかりませんでした")

        except requests.RequestException as e:
            print(f"エラー: {e}")


if __name__ == "__main__":
    test_skygate_access()

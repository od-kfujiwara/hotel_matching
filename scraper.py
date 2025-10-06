import requests
from bs4 import BeautifulSoup
import os
import re


def extract_hotel_images_tour(hotel_id):
    """
    Extract and download hotel images from tour.ne.jp

    Args:
        hotel_id (str): Hotel ID from tour.ne.jp URL

    Returns:
        list: List of downloaded image file paths
    """
    url = f"https://www.tour.ne.jp/j_hotel/{hotel_id}/"

    try:
        # Fetch the page
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # 「Area_hotel_photo_box」内を取得
        photo_box = soup.find(id="Area_hotel_photo_box")
        if not photo_box:
            print("No element with id='Area_hotel_photo_box' found.")
            return []

        # photo_box中のすべての <img> タグを抽出
        hotel_images = photo_box.find_all('img')
        if not hotel_images:
            print("No images found inside #Area_hotel_photo_box.")
            return []

        # 先頭の1枚（Area_photo_detail内）を除外
        hotel_images = hotel_images[1:]

        # Create images directory if it doesn't exist
        os.makedirs('images', exist_ok=True)

        # Download images
        downloaded_files = []
        for idx, img_tag in enumerate(hotel_images, 1):
            try:
                img_url = img_tag.get('src', '')
                if not img_url:
                    continue

                # Ensure URL has proper protocol
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif not img_url.startswith('http'):
                    img_url = 'https://' + img_url

                # Download image
                img_response = requests.get(img_url, timeout=10)
                img_response.raise_for_status()

                # Determine file extension
                ext = 'jpg'
                if '.png' in img_url.lower():
                    ext = 'png'
                elif '.webp' in img_url.lower():
                    ext = 'webp'

                # Save image
                filename = f"images/tour_{hotel_id}_{idx}.{ext}"
                with open(filename, 'wb') as f:
                    f.write(img_response.content)

                downloaded_files.append(filename)
                print(f"Downloaded: {filename}")

            except Exception as e:
                print(f"Failed to download image {idx}: {e}")

        return downloaded_files

    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return []


def extract_hotel_images_airtrip(hotel_id):
    """
    Extract and download hotel images from airtrip.jp

    Args:
        hotel_id (str): Hotel ID from airtrip.jp URL

    Returns:
        list: List of downloaded image file paths
    """
    url = f"https://domhotel.airtrip.jp/hotel/detail/{hotel_id}"

    try:
        # Fetch the page
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all image tags
        img_tags = soup.find_all('img')

        # Extract airtrip CDN hotel images only
        hotel_images = []
        for img in img_tags:
            src = img.get('src', '')
            if 'cdn-domhotel.airtrip.jp' in src and '/hotel/img' in src:
                # Ensure full URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://cdn-domhotel.airtrip.jp' + src

                if src not in hotel_images:
                    hotel_images.append(src)

        # Create images directory if it doesn't exist
        os.makedirs('images', exist_ok=True)

        # Download images
        downloaded_files = []
        for idx, img_url in enumerate(hotel_images, 1):
            try:
                # Download image
                img_response = requests.get(img_url, timeout=10)
                img_response.raise_for_status()

                # Determine file extension
                ext = 'jpg'
                if '.png' in img_url.lower():
                    ext = 'png'
                elif '.webp' in img_url.lower():
                    ext = 'webp'

                # Save image
                filename = f"images/airtrip_{hotel_id}_{idx}.{ext}"
                with open(filename, 'wb') as f:
                    f.write(img_response.content)

                downloaded_files.append(filename)
                print(f"Downloaded: {filename}")

            except Exception as e:
                print(f"Failed to download image {idx}: {e}")

        return downloaded_files

    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return []


def main():
    """Main function to run the scraper"""
    print("Hotel Image Scraper")
    print("=" * 40)
    print("Select site:")
    print("1. tour.ne.jp")
    print("2. airtrip.jp")
    print("-" * 40)

    site_choice = input("Enter choice (1 or 2): ").strip()

    if site_choice == '1':
        hotel_id = input("Enter hotel ID (e.g., 64586): ").strip()
        if not hotel_id:
            print("Error: Hotel ID cannot be empty")
            return

        print(f"\nFetching images from tour.ne.jp for hotel ID: {hotel_id}")
        print("-" * 40)
        downloaded = extract_hotel_images_tour(hotel_id)

    elif site_choice == '2':
        hotel_id = input("Enter hotel ID (e.g., 39204H282): ").strip()
        if not hotel_id:
            print("Error: Hotel ID cannot be empty")
            return

        print(f"\nFetching images from airtrip.jp for hotel ID: {hotel_id}")
        print("-" * 40)
        downloaded = extract_hotel_images_airtrip(hotel_id)

    else:
        print("Error: Invalid choice")
        return

    print("-" * 40)
    print(f"\nTotal images downloaded: {len(downloaded)}")

    if downloaded:
        print("\nDownloaded files:")
        for file in downloaded:
            print(f"  - {file}")


if __name__ == "__main__":
    main()

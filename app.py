from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import glob
from scraper import extract_hotel_images_tour, extract_hotel_images_airtrip
from PIL import Image
import imagehash

app = Flask(__name__)

# Configure upload folder
IMAGES_FOLDER = 'images'
os.makedirs(IMAGES_FOLDER, exist_ok=True)


def cleanup_images(pattern):
    """
    Delete images matching the given pattern

    Args:
        pattern (str): Glob pattern for images to delete (e.g., "tour_12345_*")
    """
    files = glob.glob(os.path.join(IMAGES_FOLDER, pattern))
    for file in files:
        try:
            os.remove(file)
            print(f"Deleted: {file}")
        except Exception as e:
            print(f"Failed to delete {file}: {e}")


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/api/scrape', methods=['POST'])
def scrape_images():
    """
    Scrape hotel images from specified site
    Expected JSON: {"site": "tour" or "airtrip", "hotel_id": "..."}
    """
    try:
        data = request.get_json()
        site = data.get('site')
        hotel_id = data.get('hotel_id')

        if not site or not hotel_id:
            return jsonify({'error': 'Missing site or hotel_id'}), 400

        # Call appropriate scraper function
        if site == 'tour':
            downloaded = extract_hotel_images_tour(hotel_id)
        elif site == 'airtrip':
            downloaded = extract_hotel_images_airtrip(hotel_id)
        else:
            return jsonify({'error': 'Invalid site'}), 400

        # Return list of downloaded files (just filenames)
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
    Compare images from two patterns
    Expected JSON: {"pattern1": "...", "pattern2": "...", "threshold": 0.9}
    """
    try:
        data = request.get_json()
        pattern1 = data.get('pattern1', '')
        pattern2 = data.get('pattern2', '')
        threshold = float(data.get('threshold', 0.9))

        # Get image files
        images1 = sorted(glob.glob(os.path.join(IMAGES_FOLDER, pattern1)))
        images2 = sorted(glob.glob(os.path.join(IMAGES_FOLDER, pattern2)))

        if not images1:
            return jsonify({'error': f'No images found for pattern: {pattern1}'}), 400
        if not images2:
            return jsonify({'error': f'No images found for pattern: {pattern2}'}), 400

        # Compute hashes for first set
        hashes1 = {}
        for img_path in images1:
            try:
                img = Image.open(img_path)
                hash_val = imagehash.average_hash(img)
                hashes1[img_path] = hash_val
            except Exception as e:
                print(f"Error processing {img_path}: {e}")

        # Compute hashes for second set
        hashes2 = {}
        for img_path in images2:
            try:
                img = Image.open(img_path)
                hash_val = imagehash.average_hash(img)
                hashes2[img_path] = hash_val
            except Exception as e:
                print(f"Error processing {img_path}: {e}")

        # Compare all pairs
        matches = []
        for img1_path, hash1 in hashes1.items():
            for img2_path, hash2 in hashes2.items():
                # Calculate hash distance
                diff = hash1 - hash2
                # Convert to similarity (0-1 scale)
                similarity = 1 - diff / len(hash1.hash) ** 2

                if similarity >= threshold:
                    matches.append({
                        'image1': os.path.basename(img1_path),
                        'image2': os.path.basename(img2_path),
                        'similarity': float(similarity),
                        'hash_distance': int(diff)
                    })

        # Sort matches by similarity (highest first)
        matches.sort(key=lambda x: x['similarity'], reverse=True)

        return jsonify({
            'success': True,
            'total_images1': len(images1),
            'total_images2': len(images2),
            'total_comparisons': len(images1) * len(images2),
            'matches': matches,
            'match_count': len(matches),
            'threshold': threshold
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scrape_and_compare', methods=['POST'])
def scrape_and_compare():
    """
    Scrape images from both sites and compare them
    Expected JSON: {"tour_id": "...", "airtrip_id": "...", "threshold": 0.9}
    """
    try:
        data = request.get_json()
        tour_id = data.get('tour_id', '').strip()
        airtrip_id = data.get('airtrip_id', '').strip()
        threshold = float(data.get('threshold', 0.9))

        if not tour_id or not airtrip_id:
            return jsonify({'error': 'Both tour_id and airtrip_id are required'}), 400

        # Step 1: Cleanup existing images for these hotel IDs
        cleanup_images(f'tour_{tour_id}_*')
        cleanup_images(f'airtrip_{airtrip_id}_*')

        # Step 2: Scrape from tour.ne.jp
        tour_images = extract_hotel_images_tour(tour_id)
        if not tour_images:
            return jsonify({'error': 'Failed to download images from tour.ne.jp'}), 500

        # Step 3: Scrape from airtrip.jp
        airtrip_images = extract_hotel_images_airtrip(airtrip_id)
        if not airtrip_images:
            return jsonify({'error': 'Failed to download images from airtrip.jp'}), 500

        # Step 4: Compute hashes for tour images
        hashes_tour = {}
        for img_path in tour_images:
            try:
                img = Image.open(img_path)
                hash_val = imagehash.average_hash(img)
                hashes_tour[img_path] = hash_val
            except Exception as e:
                print(f"Error processing {img_path}: {e}")

        # Step 5: Compute hashes for airtrip images
        hashes_airtrip = {}
        for img_path in airtrip_images:
            try:
                img = Image.open(img_path)
                hash_val = imagehash.average_hash(img)
                hashes_airtrip[img_path] = hash_val
            except Exception as e:
                print(f"Error processing {img_path}: {e}")

        # Step 6: Compare all pairs
        matches = []
        for img1_path, hash1 in hashes_tour.items():
            for img2_path, hash2 in hashes_airtrip.items():
                # Calculate hash distance
                diff = hash1 - hash2
                # Convert to similarity (0-1 scale)
                similarity = 1 - diff / len(hash1.hash) ** 2

                if similarity >= threshold:
                    matches.append({
                        'image1': os.path.basename(img1_path),
                        'image2': os.path.basename(img2_path),
                        'similarity': float(similarity),
                        'hash_distance': int(diff)
                    })

        # Sort matches by similarity (highest first)
        matches.sort(key=lambda x: x['similarity'], reverse=True)

        return jsonify({
            'success': True,
            'tour_count': len(tour_images),
            'airtrip_count': len(airtrip_images),
            'total_comparisons': len(tour_images) * len(airtrip_images),
            'matches': matches,
            'match_count': len(matches),
            'threshold': threshold
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/images/<filename>')
def serve_image(filename):
    """Serve images from the images folder"""
    return send_from_directory(IMAGES_FOLDER, filename)


@app.route('/api/images', methods=['GET'])
def list_images():
    """List all images in the images folder"""
    try:
        all_images = glob.glob(os.path.join(IMAGES_FOLDER, '*.*'))
        # Filter for image files
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

from PIL import Image
import imagehash
import os
import glob


def compare_hotel_images(pattern1, pattern2, threshold=0.9):
    """
    Compare hotel images from two different sources

    Args:
        pattern1 (str): Glob pattern for first set of images (e.g., "images/tour_*.jpg")
        pattern2 (str): Glob pattern for second set of images (e.g., "images/airtrip_*.jpg")
        threshold (float): Similarity threshold (0-1), default 0.9

    Returns:
        dict: Comparison results with matched pairs and statistics
    """
    # Get image files
    images1 = sorted(glob.glob(pattern1))
    images2 = sorted(glob.glob(pattern2))

    if not images1:
        print(f"No images found matching pattern: {pattern1}")
        return None

    if not images2:
        print(f"No images found matching pattern: {pattern2}")
        return None

    print(f"Found {len(images1)} images in first set")
    print(f"Found {len(images2)} images in second set")
    print("-" * 60)

    # Compute hashes for first set
    print("Computing hashes for first set...")
    hashes1 = {}
    for img_path in images1:
        try:
            img = Image.open(img_path)
            hash_val = imagehash.average_hash(img)
            hashes1[img_path] = hash_val
        except Exception as e:
            print(f"Error processing {img_path}: {e}")

    # Compute hashes for second set
    print("Computing hashes for second set...")
    hashes2 = {}
    for img_path in images2:
        try:
            img = Image.open(img_path)
            hash_val = imagehash.average_hash(img)
            hashes2[img_path] = hash_val
        except Exception as e:
            print(f"Error processing {img_path}: {e}")

    # Compare all pairs
    print("\nComparing images...")
    print("-" * 60)

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
                    'similarity': similarity,
                    'hash_distance': diff
                })

    # Sort matches by similarity (highest first)
    matches.sort(key=lambda x: x['similarity'], reverse=True)

    return {
        'total_images1': len(images1),
        'total_images2': len(images2),
        'total_comparisons': len(images1) * len(images2),
        'matches': matches,
        'match_count': len(matches),
        'threshold': threshold
    }


def print_results(results):
    """Print comparison results in a readable format"""
    if not results:
        return

    print("\n" + "=" * 60)
    print("COMPARISON RESULTS")
    print("=" * 60)
    print(f"First set: {results['total_images1']} images")
    print(f"Second set: {results['total_images2']} images")
    print(f"Total comparisons: {results['total_comparisons']}")
    print(f"Similarity threshold: {results['threshold']}")
    print(f"\nMatches found: {results['match_count']}")
    print("=" * 60)

    if results['matches']:
        print("\nMatched pairs:")
        print("-" * 60)
        for i, match in enumerate(results['matches'], 1):
            print(f"\n{i}. Similarity: {match['similarity']:.4f} (distance: {match['hash_distance']})")
            print(f"   Image 1: {match['image1']}")
            print(f"   Image 2: {match['image2']}")
    else:
        print("\nNo matches found above the threshold.")


def main():
    """Main function to run image comparison"""
    print("Hotel Image Comparison Tool")
    print("=" * 60)

    # Get patterns from user
    print("\nEnter image patterns to compare:")
    print("Examples:")
    print("  - images/tour_64586_*.jpg")
    print("  - images/airtrip_39204H282_*.jpg")
    print("-" * 60)

    pattern1 = input("First image pattern: ").strip()
    pattern2 = input("Second image pattern: ").strip()

    if not pattern1 or not pattern2:
        print("Error: Both patterns are required")
        return

    # Get threshold
    threshold_input = input("Similarity threshold (0-1, default 0.9): ").strip()
    threshold = 0.9
    if threshold_input:
        try:
            threshold = float(threshold_input)
            if not 0 <= threshold <= 1:
                print("Warning: Threshold should be between 0 and 1. Using default 0.9")
                threshold = 0.9
        except ValueError:
            print("Warning: Invalid threshold value. Using default 0.9")

    # Run comparison
    results = compare_hotel_images(pattern1, pattern2, threshold)

    # Print results
    if results:
        print_results(results)


if __name__ == "__main__":
    main()

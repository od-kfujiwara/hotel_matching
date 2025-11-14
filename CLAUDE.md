# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

tour.ne.jp と airtrip.jp からホテル画像をスクレイピングし、複数の画像類似度アルゴリズムで比較するツール。Flask バックエンドとバニラ JavaScript フロントエンドで構成。

## 開発コマンド

### セットアップ
```bash
uv sync
```

### アプリケーション起動
```bash
uv run python -m apps.web
```
サーバーは http://localhost:5000/ で起動

### サンプルスクリプト実行
各マッチャーの検証用スクリプト:
```bash
uv run python samples/ahash_matching.py
uv run python samples/phash_matching.py
uv run python samples/feature_matching.py
uv run python samples/clip_matching.py
uv run python samples/gemini_matching.py
```

## アーキテクチャ

### マッチャーのレジストリパターン
`hotel_matching/matchers/` 配下でレジストリパターンを使用:

1. 各マッチャーは `compare_*()` 関数を実装（引数: `images1, images2, threshold`、戻り値: マッチ結果のリスト）
2. 各マッチャーは `METHOD_NAME` 定数を定義（例: "hash", "phash", "feature", "clip", "gemini"）
3. 全マッチャーは `hotel_matching/matchers/registry.py` の `_MATCHERS` 辞書に登録
4. エントリーポイント `hotel_matching/matcher.py:compare()` が `get_matcher(method)` を呼び出して適切な実装にディスパッチ

**新しいマッチャーの追加方法:**
- `hotel_matching/matchers/` に新ファイルを作成し、`compare_<name>()` と `METHOD_NAME` を定義
- `registry.py` でインポートして登録
- web.py や matcher.py の変更は不要

### API フロー
`apps/web.py:/api/scrape_and_compare` エンドポイント:
1. `images/` ディレクトリの既存画像を削除（*.jpg, *.png, *.webp）
2. `extract_hotel_images_tour(tour_id)` を呼び出し → `images/tour_{id}_{n}.{ext}` として保存
3. `extract_hotel_images_airtrip(airtrip_id)` を呼び出し → `images/airtrip_{id}_{n}.{ext}` として保存
4. `hotel_matching.matcher` の `compare(method, tour_images, airtrip_images, threshold)` を呼び出し
5. 類似度スコアと手法固有のメタデータを含む JSON を返却

### スクレイパーのアーキテクチャ
`hotel_matching/scraper/__init__.py` に配置:

- `extract_hotel_images_tour(hotel_id)`: `id="Area_hotel_photo_box"` を解析、先頭画像をスキップ、プロトコル相対 URL を処理
- `extract_hotel_images_airtrip(hotel_id)`: `cdn-domhotel.airtrip.jp/.../hotel/img` でフィルタリング、URL を重複排除

両方とも 10 秒タイムアウト、`images/` ディレクトリにサイト別プレフィックスで保存。

### マッチャー実装詳細

**hash_matcher.py（平均ハッシュ法）**
- imagehash ライブラリで 8×8 ハッシュを使用
- 類似度: `1 - hamming距離 / 64`
- 戻り値: `similarity`, `hash_diff`
- 推奨閾値: 0.90

**phash_matcher.py（Perceptual Hash）**
- DCT ベースの知覚的ハッシュ
- 平均ハッシュより画像の軽微な変更に強い
- 戻り値: `similarity`, `hash_diff`

**feature_matcher.py（ORB + RANSAC）**
- ORB 特徴点検出（1000 特徴点）
- アスペクト比を保ちながら高さを揃えてリサイズ
- BFMatcher（Hamming 距離）+ Lowe の比率テスト（0.75）
- RANSAC でホモグラフィ推定（≥4 マッチが必要）
- 類似度: インライアの `1 / (1 + 平均距離)`
- 戻り値: `inlier_count`, `total_matches`, `inlier_ratio`, `avg_distance`
- 推奨閾値: 0.04

**clip_matcher.py（CLIP 類似度）**
- OpenAI CLIP モデルで意味的画像比較
- 画像を前処理し、埋め込みベクトル間のコサイン類似度を計算
- 戻り値: `similarity`
- 推奨閾値: 可変（通常 0.8-0.95）

**gemini_matcher.py（Gemini AI）**
- Google Gemini API で AI ベース画像比較
- `.env` に `GEMINI_API_KEY` と `GEMINI_MODEL` が必要
- 画像ペアを Gemini に送信し、同一画像か判定
- 戻り値: `passed_threshold`（真偽値）, `reason`（説明）
- 注意: API レート制限回避のため現在は 2 枚のみに制限

### フロントエンドのアーキテクチャ
`static/js/main.js` のバニラ JavaScript:
- 入力検証（tour_id, airtrip_id）
- 選択された手法に応じて閾値スライダーのデフォルト値を調整（hash: 0.90, feature: 0.04）
- API 呼び出し中に段階的なステータスメッセージを表示
- マッチカードを画像の並列比較で描画

## 環境設定

### Gemini マッチャー使用時に必要
プロジェクトルートに `.env` ファイルを作成:
```
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

## 重要な実装メモ

- `/api/scrape_and_compare` 呼び出しごとに `images/` ディレクトリは完全にクリーンアップされる
- 全マッチャーは類似度降順にソートされた辞書のリストを返す
- フロントエンドは `passed_threshold` フィールドを期待（未指定時はデフォルト true）
- スクレイパーはプロトコル相対 URL を処理（`//` → `https://`）
- 特徴点マッチャーは RANSAC に最低 4 つの良質なマッチが必要
- Web サーバーはデフォルトで debug=True、ポート 5000 で起動

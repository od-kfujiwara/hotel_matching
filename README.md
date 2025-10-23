# hotel_matching

## セットアップ

1. Python 仮想環境を作成し有効化します（必要バージョンは `pyproject.toml` を参照）。
2. 依存関係を同期します:
   ```bash
   uv sync
   ```

## マッチャー

実装済みのマッチング手法は以下の通りです。

- 平均ハッシュ法 (`hash`): `hotel_matching/matchers/hash_matcher.py`
- pHash（離散コサイン変換）(`phash`): `hotel_matching/matchers/phash_matcher.py`
- 特徴点マッチング（ORB + RANSAC） (`feature`): `hotel_matching/matchers/feature_matcher.py`
- CLIP 類似度 (`clip`): `hotel_matching/matchers/clip_matcher.py`
- Gemini AI 判定 (`gemini`): `hotel_matching/matchers/gemini_matcher.py`

マッチング手法は `hotel_matching/matchers/` に配置されています。コードから利用する例:

```python
from hotel_matching.matcher import compare

matches = compare("hash", images1, images2, 0.9)
```

新しい手法を追加する場合は `ImageMatcher` を実装し、`hotel_matching/matchers/registry.py` で登録します。

### Gemini マッチャーの設定

Gemini を利用するには Google AI Studio で取得した API キーを `.env` 等で設定してください。

```
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.5-flash
```

## サーバー起動方法

Flask サーバーは次のコマンドで起動できます:

```bash
uv run python -m apps.web
```

起動後はブラウザから `http://localhost:5000/` にアクセスしてください。

## サンプルスクリプト

`samples/` 以下に各手法の検証用スクリプトを用意しています。

- `samples/ahash_matching.py`
- `samples/phash_matching.py`
- `samples/feature_matching.py`
- `samples/clip_matching.py`
- `samples/gemini_matching.py`

いずれも `uv run python samples/<name>.py` で動作します。

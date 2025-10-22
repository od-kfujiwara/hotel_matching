# hotel_matching

## セットアップ

1. Python 仮想環境を作成し有効化します（必要バージョンは `pyproject.toml` を参照）。
2. 依存関係を同期します:
   ```bash
   uv sync
   ```

## マッチャー

実装済みのマッチング手法は以下の2種類です。

- 平均ハッシュ法 (`hash`): `hotel_matching/matchers/hash_matcher.py`
- 特徴点マッチング（ORB + RANSAC） (`feature`): `hotel_matching/matchers/feature_matcher.py`

マッチング手法は `hotel_matching/matchers/` に配置されています。コードから利用する例:

```python
from hotel_matching.matcher import compare

matches = compare("hash", images1, images2, 0.9)
```

新しい手法を追加する場合は `ImageMatcher` を実装し、`hotel_matching/matchers/registry.py` で登録します。

## サンプル

サンプルスクリプトは `samples/` ディレクトリにあり、共通のマッチャーAPIを利用しています。

- `samples/average_hash.py`
- `samples/feature_matching.py`
- `samples/clip_matching.py`

## サーバー起動方法

Flask サーバーは次のコマンドで起動できます:

```bash
uv run python -m apps.web
```

起動後はブラウザから `http://localhost:5000/` にアクセスしてください。

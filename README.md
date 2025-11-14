# hotel_matching

## セットアップ

1. Python 仮想環境を作成し有効化します（必要バージョンは `pyproject.toml` を参照）。
2. 依存関係を同期します:
   ```bash
   uv sync
   ```

## マッチャー

実装済みのマッチング手法は以下の通りです。

- 平均ハッシュ法 (`ahash`): 小さくリサイズ→グレースケール化→明るさのハミング距離で比較
- pHash（離散コサイン変換）(`phash`): 小さくリサイズ→グレースケール化→離散コサイン変換→周波数成分（模様・輪郭）で比較
- 特徴点マッチング（ORB + RANSAC） (`feature`): ORBで特徴点（模様・輪郭）検出＋ベクトル化→マッチング→RANSACで外れ値除去して最終比較
- CLIP 類似度 (`clip`): 意味的にベクトル化して、コサイン類似度（意味の近さ）で比較
- Gemini AI 判定 (`gemini`): 自然言語で同一ホテルかどうかを質問

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

## サンプルホテルコード
ホテルカーゴ心斎橋
- トラベルコ 42685
- エアトリ 2100589

ホテルランタナ大阪
- トラベルコ 46144
- エアトリ 2161331

## サンプルスクリプト

`samples/` 以下に各手法の検証用スクリプトを用意しています。

- `samples/ahash_matching.py`
- `samples/phash_matching.py`
- `samples/feature_matching.py`
- `samples/clip_matching.py`
- `samples/gemini_matching.py`

いずれも `uv run python samples/<name>.py` で動作します。

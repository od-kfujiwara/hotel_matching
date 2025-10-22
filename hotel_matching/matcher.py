"""
対応するマッチング関数を実行するラッパーモジュール
"""

from typing import Iterable, List

from .matchers.registry import get_matcher


def compare(
    method: str,
    images1: Iterable[str],
    images2: Iterable[str],
    threshold: float,
) -> List[dict]:
    """
    指定されたマッチング手法で画像を比較します

    引数:
        method: 使用するマッチング手法名
        images1: 1つ目の画像パスのイテラブル
        images2: 2つ目の画像パスのイテラブル
        threshold: 類似度の閾値 (0〜1)

    戻り値:
        list[dict]: マッチ結果のリスト
    """
    matcher = get_matcher(method)
    return matcher(images1, images2, threshold)

"""手法名ごとのマッチング関数を管理するレジストリモジュール"""

from __future__ import annotations

from typing import Callable, Dict, Iterable, List

from .clip_matcher import METHOD_NAME as CLIP_NAME
from .clip_matcher import compare_clip
from .feature_matcher import METHOD_NAME as FEATURE_NAME
from .feature_matcher import compare_feature
from .hash_matcher import METHOD_NAME as HASH_NAME
from .hash_matcher import compare_hash

MatcherFunc = Callable[[Iterable[str], Iterable[str], float], List[dict]]

_MATCHERS: Dict[str, MatcherFunc] = {
    HASH_NAME: compare_hash,
    FEATURE_NAME: compare_feature,
    CLIP_NAME: compare_clip,
}


def get_matcher(method: str) -> MatcherFunc:
    """指定された手法名に対応するマッチャー関数を返す"""
    try:
        return _MATCHERS[method]
    except KeyError as exc:
        raise ValueError(f"不明なマッチャー '{method}'") from exc

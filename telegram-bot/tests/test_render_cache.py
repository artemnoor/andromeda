from __future__ import annotations

from andromeda_telegram.render.cache import RenderCache


def test_render_cache_is_bounded_and_expires() -> None:
    now = [0.0]
    cache = RenderCache(max_items=1, ttl_seconds=5, clock=lambda: now[0])
    cache.put("a", b"a")
    cache.put("b", b"b")

    assert cache.get("a") is None
    assert cache.get("b") == b"b"
    now[0] = 6
    assert cache.get("b") is None

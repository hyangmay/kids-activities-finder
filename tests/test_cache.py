import time

from kids_activities_finder.cache import TTLCache


def test_set_and_get():
    cache: TTLCache[str, int] = TTLCache(ttl_seconds=10)
    cache.set("a", 1)
    assert cache.get("a") == 1
    assert cache.get("missing") is None


def test_expiry():
    cache: TTLCache[str, int] = TTLCache(ttl_seconds=0.05)
    cache.set("a", 1)
    assert cache.get("a") == 1
    time.sleep(0.06)
    assert cache.get("a") is None


def test_get_or_compute_caches_and_avoids_recompute():
    cache: TTLCache[str, int] = TTLCache(ttl_seconds=10)
    calls = []

    def compute():
        calls.append(1)
        return 42

    assert cache.get_or_compute("k", compute) == 42
    assert cache.get_or_compute("k", compute) == 42
    assert len(calls) == 1  # computed once, then served from cache


def test_clear():
    cache: TTLCache[str, int] = TTLCache(ttl_seconds=10)
    cache.set("a", 1)
    cache.clear()
    assert cache.get("a") is None

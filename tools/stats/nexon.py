"""넥슨 오버워치 공식 영웅 통계(https://overwatch.nexon.com/hero/rate) 읽기.

페이지는 Nuxt 서버 렌더링이라 주소의 쿼리(role, rq, rank, map, input, region)에 맞는
통계가 __NUXT_DATA__ 스크립트 안에 devalue 형식으로 들어 있다. 그걸 풀어서 쓴다.
"""
import json
import re
import time
import urllib.parse
import urllib.request

BASE_URL = "https://overwatch.nexon.com/hero/rate"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ow-map-picker/1.0 (personal use)"

_NUXT_DATA_RE = re.compile(
    r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', re.S
)

# devalue 특수 값: -1 undefined, -2 hole, -3 NaN, -4 +Inf, -5 -Inf, -6 -0
_SPECIAL = {-1: None, -2: None, -3: float("nan"), -4: float("inf"), -5: float("-inf"), -6: -0.0}
_WRAPPERS = {"Reactive", "ShallowReactive", "Ref", "ShallowRef", "EmptyRef", "EmptyShallowRef"}


def _decode(flat):
    cache = {}

    def hydrate(i):
        if isinstance(i, int) and i < 0:
            return _SPECIAL.get(i)
        if i in cache:
            return cache[i]
        v = flat[i]
        if isinstance(v, list):
            if v and isinstance(v[0], str) and len(v) >= 1 and (v[0] in _WRAPPERS or v[0] in ("Set", "Map", "Date", "BigInt", "null")):
                tag = v[0]
                if tag in ("EmptyRef", "EmptyShallowRef"):
                    out = None
                elif tag in _WRAPPERS:
                    out = hydrate(v[1])
                elif tag == "Set":
                    out = [hydrate(x) for x in v[1:]]
                elif tag == "Map":
                    out = {str(hydrate(v[k])): hydrate(v[k + 1]) for k in range(1, len(v), 2)}
                elif tag == "Date":
                    out = v[1]
                elif tag == "BigInt":
                    out = int(v[1])
                else:  # null-prototype object
                    out = {v[k]: hydrate(v[k + 1]) for k in range(1, len(v), 2)}
                cache[i] = out
                return out
            out = []
            cache[i] = out
            out.extend(hydrate(x) for x in v)
            return out
        if isinstance(v, dict):
            out = {}
            cache[i] = out
            for k, x in v.items():
                out[k] = hydrate(x)
            return out
        cache[i] = v
        return v

    return hydrate(0)


def fetch_page(params=None, retries=3):
    url = BASE_URL
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "ko-KR"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                html = r.read().decode("utf-8")
            break
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))
    m = _NUXT_DATA_RE.search(html)
    if not m:
        raise RuntimeError("__NUXT_DATA__를 찾지 못함 (페이지 구조가 바뀌었을 수 있음)")
    return _decode(json.loads(m.group(1)))


def _find_key(obj, key):
    """중첩 구조에서 key를 가진 첫 dict 값을 찾는다."""
    stack = [obj]
    seen = set()
    while stack:
        o = stack.pop()
        if id(o) in seen:
            continue
        seen.add(id(o))
        if isinstance(o, dict):
            if key in o:
                return o[key]
            stack.extend(o.values())
        elif isinstance(o, list):
            stack.extend(o)
    return None


def get_filters_and_list(params=None):
    data = fetch_page(params)
    payload = data.get("data", {}) if isinstance(data, dict) else {}
    filters = _find_key(payload, "hero-rate-filters")
    rate = _find_key(payload, "hero-rate-list")
    filters = (filters or {}).get("data", filters) or {}
    heroes = ((rate or {}).get("data") or {}).get("list") or []
    return filters, heroes

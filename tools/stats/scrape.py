"""넥슨 공식 통계에서 경쟁전 기준 [티어 × 맵] 전체 조합을 받아 data.js로 저장.

사용: python scrape.py [--region korea] [--input pc] [--ranks diamond,master] [--delay 0.4] [--first grandmaster]
      python scrape.py --shared      공개 저장소의 공유 통계(GitHub가 하루 한 번 받아 둔 것)만 받기 (몇 초)
패치 직후 새 통계의 판 수가 지금 통계보다 훨씬 적으면 지금 통계를 그대로 둔다 (HOLD_RATIO, data.js의 held)
"""
import argparse
import json
import math
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nexon  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "data.js")
QP_PATH = os.path.join(os.path.dirname(OUT_PATH), "data-qp.js")  # 빠른 대전 통계
IMG_DIR = os.path.join(HERE, "img")
KST = timezone(timedelta(hours=9))
# 공유 통계: 공개 저장소 stats 가지에 GitHub가 하루 한 번 넥슨에서 받아 올려 둔 data.js · data-qp.js
# (사람마다 넥슨에 576쪽씩 요청하던 것을 한 번으로. 받는 쪽은 파일 두 개 = 몇 초)
SHARED_BASE = "https://raw.githubusercontent.com/no2thingmore/ow-map-picker-release/stats/"
SHARED_MAX_AGE_H = 54   # 이보다 오래된 공유 통계는 안 씀 (GitHub 작업이 멈췄을 때는 직접 받게). 하루 1번이라 한 번 놓친 것(48시간 + GitHub 지연)까지는 공유 통계로
DELAY_MAX = 5.0         # 막히면(실패하면) 요청 사이 대기를 이만큼까지 늘림
# 이전 통계 유지 (2026-11-05 사용자 결정): 넥슨 통계는 패치마다 0부터 다시 쌓여서, 패치 직후 새 통계는 판 수가 아주 적다
# (5시즌 중간 패치 다음 날 실측: 이전의 약 1/100, 마스터 칸의 53%가 승률 0%·100%). 그동안은 지금 통계를 그대로 쓴다.
# 기준: 새 통계 판 수(추정)가 지금 통계의 1/6 미만. 시뮬레이션에서 실제 1/8일 때 추정이 약 1/6이고,
#       판 수 1/8이면 추천 1~3순위가 평균 73% 겹침 (1/64면 48%)
HOLD_RATIO = 1 / 6
HOLD_MAX_DAYS = 7       # 그래도 이만큼 지나면 새 통계로 (밸런스가 바뀐 뒤라 이전 통계를 너무 오래 쓰지 않게)
HOLD_TIERS = ("gold", "platinum", "emerald", "diamond")  # 판 수 비교에 쓰는 티어 (판이 많아 추정이 안정)


THUMB = 96  # 화면에는 40~44px로 보이니 2배 크기면 충분 (원본 256px ≈ 170KB → 약 15KB)


def _shrink(path):
    try:
        from PIL import Image
    except ImportError:  # Pillow 없이 실행하면 원본 그대로 둔다
        return
    with Image.open(path) as im:
        if max(im.size) <= THUMB:
            return
        im = im.convert("RGBA")
        im.thumbnail((THUMB, THUMB), Image.LANCZOS)
        im.save(path, optimize=True)


def cache_images(heroes):
    """영웅 사진을 img/에 한 번만 받아 작게 줄여 두고 heroes[id]['local']에 상대 경로를 적는다."""
    import urllib.request
    os.makedirs(IMG_DIR, exist_ok=True)
    got = 0
    for hid, h in heroes.items():
        url = h.get("img")
        if not url:
            continue
        name = f"{hid}.png"
        path = os.path.join(IMG_DIR, name)
        if not os.path.exists(path):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": nexon.USER_AGENT})
                with urllib.request.urlopen(req, timeout=20) as r:
                    body = r.read()
                with open(path, "wb") as f:
                    f.write(body)
                got += 1
                time.sleep(0.1)
            except Exception as e:
                print(f"  사진 실패 {hid}: {e}")
                continue
        _shrink(path)
        h["local"] = f"img/{name}"
    print(f"영웅 사진: 새로 {got}장, 전체 {sum(1 for h in heroes.values() if 'local' in h)}장")


_SKILL_RE = re.compile(r'hero-skill__tab__icon[^>]*>\s*<img[^>]*alt="([^"]+)"')


def fetch_skills(heroes, delay=0.3):
    """넥슨 영웅 상세 페이지(overwatch.nexon.com/hero/<값>)의 기술 이름을 heroes[id]['skills']에 넣는다.

    점수판 오른쪽 패널의 기록 항목('충격 지뢰로 처치' 등)과 맞춰 내 영웅을 알려주지 않아도 알아보는 데 쓴다.
    """
    import html
    import urllib.request
    got = 0
    for hid, h in heroes.items():
        try:
            req = urllib.request.Request(f"https://overwatch.nexon.com/hero/{hid}", headers={"User-Agent": nexon.USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as r:
                page = r.read().decode("utf-8")
            skills = list(dict.fromkeys(html.unescape(s).strip() for s in _SKILL_RE.findall(page)))
            if skills:
                h["skills"] = skills
                got += 1
        except Exception as e:
            print(f"  기술 이름 실패 {hid}: {e}")
        time.sleep(delay)
    print(f"영웅 기술 이름: {got}/{len(heroes)}명")


def write_data(data):
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("window.OW_DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    os.replace(tmp, OUT_PATH)


def write_qp(data):
    """빠른 대전 통계는 따로 (data-qp.js, 화면이 빠른 대전일 때 씀). 영웅·맵 목록은 data.js 것을 같이 쓴다."""
    tmp = QP_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("window.OW_DATA_QP = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    os.replace(tmp, QP_PATH)


def collect(rq, ranks, map_keys, args, heroes, label, on_rank=None):
    """티어 × 맵 전체 조합 → stats[티어][맵][영웅] = [픽률, 승률, 밴률], 실패 목록. heroes에 처음 본 영웅을 채운다.
    ranks는 받을 순서대로. '전체'가 맨 앞이면 '전체'에서 빈 맵(지금 통계가 없는 맵)은 다른 티어에서 건너뛴다.
    on_rank(stats)는 티어 하나를 다 받을 때마다 (먼저 받은 티어를 바로 저장하려고)."""
    stats, failed = {}, []
    total = len(ranks) * len(map_keys)
    done = 0
    started = time.time()
    delay, ok_run = args.delay, 0
    empty = set()  # '전체' 티어에서 비어 있던 맵
    for r in ranks:
        stats[r["value"]] = {}
        for mk in map_keys:
            if mk in empty and r["value"] != "all":
                stats[r["value"]][mk] = {}
                done += 1
                continue
            params = dict(role="all", rq=rq, rank=r["value"], map=mk, input=args.input, region=args.region)
            try:
                _, rows = nexon.get_filters_and_list(params)
                ok_run += 1
                if ok_run >= 20 and delay > args.delay:  # 한동안 잘 되면 다시 빠르게
                    delay, ok_run = max(args.delay, delay / 2), 0
                if r["value"] == "all" and not rows:
                    empty.add(mk)
            except Exception as e:  # 한 조합 실패해도 나머지는 계속. 막힌 것일 수 있어 천천히
                failed.append(f"{r['value']}/{mk}: {e}")
                rows = []
                delay, ok_run = min(DELAY_MAX, max(delay * 2, 1.0)), 0
            entry = {}
            for h in rows:
                hid = h["heroId"]
                if hid not in heroes:
                    heroes[hid] = dict(name=h["name"], role=h["role"], subrole=h.get("subrole"),
                                       color=h.get("colorCode"), img=h.get("thumbnailUrl"))
                entry[hid] = [h.get("pickRate", 0), h.get("winRate", 0), h.get("banRate", 0)]
            stats[r["value"]][mk] = entry
            done += 1
            eta = (time.time() - started) / done * (total - done)
            print(f"\r[{label} {done}/{total}] {r['value']:<12} {mk:<22} 남은 시간 약 {eta:4.0f}초", end="", flush=True)
            time.sleep(delay)
        if on_rank:
            on_rank(stats, failed)
    print()
    if empty:
        print(f"{label}: 지금 통계가 없는 맵은 티어별로 안 받음 ({', '.join(sorted(empty))})")
    if failed:
        print(f"{label} 실패 {len(failed)}건:")
        for x in failed[:10]:
            print("  ", x)
    return stats, failed


def read_data(path=None):
    with open(path or OUT_PATH, encoding="utf-8") as f:  # 기본값은 부를 때의 OUT_PATH (시험이 임시 폴더로 바꿀 수 있게)
        text = f.read()
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def _age_hours(updated):
    """data.js의 updated('2026-11-03 21:33', 한국 시각) → 지금부터 몇 시간 전 (못 읽으면 아주 오래된 것으로)."""
    try:
        t = datetime.strptime(updated, "%Y-%m-%d %H:%M").replace(tzinfo=KST)
    except (TypeError, ValueError):
        return 1e9
    return (datetime.now(KST) - t).total_seconds() / 3600


def _filled(stats):
    return sum(1 for maps in (stats or {}).values() for v in maps.values() if v)


# ---- 판 수 추정: shrink.js의 fitNoise와 같은 계산 (selftest가 node로 두 쪽 값을 비교) ----
# 넥슨 통계엔 경기 수가 없다. 맵 승률 − 평소 승률의 흩어짐 = 진짜 차이 + 노이즈(A × 4q(1-q) / 픽률)이고,
# A ∝ 1 / 그 맵 경기 수. 맵마다 A를 최대우도로 맞춘 뒤 중간값을 쓴다 → 두 통계의 A 비율 = 판 수 비율
_NU, _P_FLOOR, _MIN_HEROES = 4, 0.05, 10
_LOG_LO, _LOG_HI, _TAU_LO, _TAU_HI = math.log(0.01), math.log(1e5), math.log(1e-3), math.log(400)


def _g(q):
    q = min(max(q / 100, 0.02), 0.98)
    return 4 * q * (1 - q)


def _tll(d, v):
    return -0.5 * math.log(v) - (_NU + 1) / 2 * math.log1p(d * d / (_NU * v))


def _nested(fine, coarse):
    return max(fine - coarse, 0.25 * fine) + 0.01


def _golden(f, lo, hi, it=50):
    r = (math.sqrt(5) - 1) / 2
    a, b = lo, hi
    c, d = b - r * (b - a), a + r * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(it):
        if fc > fd:
            b, d, fd = d, c, fc
            c = b - r * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + r * (b - a)
            fd = f(d)
    return (a + b) / 2


def noise_level(stats, rank):
    """그 티어의 맵 노이즈 A 중간값 (shrink.js noiseOf(rank).Amed와 같은 값, 클수록 판이 적음). 맵이 없으면 None."""
    st = (stats or {}).get(rank) or {}
    base = st.get("all") or {}
    groups = {}
    for m, e in st.items():
        if m == "all":
            continue
        its = []
        for h, x in e.items():
            b = base.get(h)
            if not b or x[0] <= 0 or b[0] <= 0:
                continue
            gq = _g(b[1])
            its.append((x[1] - b[1], gq / max(x[0], _P_FLOOR), gq / max(b[0], _P_FLOOR)))
        if len(its) >= _MIN_HEROES:
            groups[m] = its
    if not groups:
        return None
    A, tau2 = {k: 50.0 for k in groups}, 4.0

    def ll(its, t2, a, ab):
        return sum(_tll(d, t2 + _nested(a * gp, ab * gb)) for d, gp, gb in its)

    def harm(vals):
        return 1 / sum(1 / v for v in vals)

    def near(x, lo, hi, w):
        return (max(lo, x - w), min(hi, x + w)) if w else (lo, hi)
    # 맵별 A와 tau2를 번갈아 맞춘다 (첫 라운드는 전체 범위, 그 뒤엔 이전 값 주변. 둘 다 1% 안쪽으로만 움직이면 멈춤)
    for rnd in range(40):
        w, it, prev_t = (1.5, 16, tau2) if rnd else (0, 40, tau2)
        ab, moved = harm(A.values()), 0.0
        for k, its in groups.items():
            c = math.log(A[k])
            A[k] = math.exp(_golden(lambda la: ll(its, tau2, math.exp(la), ab), *near(c, _LOG_LO, _LOG_HI, w), it))
            moved = max(moved, abs(math.log(A[k]) - c))
        ab = harm(A.values())
        tau2 = math.exp(_golden(lambda lt: sum(ll(its, math.exp(lt), A[k], ab) for k, its in groups.items()),
                                *near(math.log(tau2), _TAU_LO, _TAU_HI, w), it))
        if rnd and moved < 0.01 and abs(math.log(tau2 / prev_t)) < 0.01:
            break
    vals = sorted(A.values())
    return vals[len(vals) >> 1]


def games_ratio(new_stats, old_stats, tiers=HOLD_TIERS):
    """새 통계의 판 수 / 지금 통계의 판 수 (추정, 티어별 비율의 중간값). 못 재면 None."""
    rs = []
    for t in tiers:
        a_old, a_new = noise_level(old_stats, t), noise_level(new_stats, t)
        if a_old and a_new:
            rs.append(a_old / a_new)
    return sorted(rs)[len(rs) >> 1] if rs else None


def should_hold(new_stats, old):
    """새 통계 대신 지금 통계(old, data.js 내용)를 계속 쓸지 → (유지?, 판 수 비율 또는 None).
    유지 = 새 통계 판 수가 지금 통계의 HOLD_RATIO 미만 + 지금 통계가 HOLD_MAX_DAYS 안의 것(유지 중이면 유지 시작부터)."""
    if not old or not old.get("stats"):
        return False, None
    held = old.get("held") or {}
    if _age_hours(held.get("since") or old.get("updated")) > HOLD_MAX_DAYS * 24:
        return False, None
    ratio = games_ratio(new_stats, old["stats"])
    return (ratio is not None and ratio < HOLD_RATIO), ratio


def fill_empty_maps(old_stats, new_stats, filled=()):
    """이전 통계에 통째로('전체' 티어까지) 비어 있는 맵만 새 통계로 채운 것 → (통계, 채운 맵 목록).
    예: 2026-11 패치 전 0판이던 할리우드. 판이 적어도 추천 계산(shrink.js)이 그 맵 효과를 작게 줄여서 쓴다.
    이미 채운 맵(filled)은 더 쌓인 새 통계로 바꾸고, 새 통계에서 빈 칸은 지금 값 그대로 (받기 실패와 구분이 안 되니까)."""
    old_all = (old_stats or {}).get("all") or {}
    new_all = (new_stats or {}).get("all") or {}
    maps = [m for m, e in old_all.items() if new_all.get(m) and (m in filled or not e)]
    stats = old_stats
    if maps:
        stats = {t: {**e, **{m: (new_stats.get(t) or {}).get(m) or e.get(m, {}) for m in maps}} for t, e in old_stats.items()}
    return stats, sorted({*filled, *maps})


def held_copy(old, ratio, when, new_stats=None):
    """지금 통계를 두고 확인 시각(updated)과 '이전 통계 유지' 표시(held)를 바꾼 것. 통째로 빈 맵만 새 통계로 채운다(fill_empty_maps).
    held = {from: 이 통계를 실제로 받은 시각, since: 유지를 시작한 시각, ratio: 새 통계 판 수 / 이 통계 판 수(추정), filled: 새 통계로 채운 맵(있을 때만)}.
    updated를 지금으로 두는 건, 공유 통계를 받는 예전 버전 앱도 '새 파일'로 보고 이 통계를 그대로 받게 하려고."""
    h = old.get("held") or {}
    stats, filled = fill_empty_maps(old.get("stats"), new_stats, h.get("filled") or ())
    held = {"from": h.get("from") or old.get("updated"), "since": h.get("since") or when, "ratio": round(ratio, 4)}
    if filled:
        held["filled"] = filled
    return {**old, "updated": when, "stats": stats, "held": held}


def fetch_shared(base=SHARED_BASE):
    """공유 통계(data.js · data-qp.js)를 받아 쓸 만하면 저장 → 0, 아직 지금 파일과 그대로면 그냥 → 0, 못 쓰면 1 (그땐 넥슨에서 직접 받는다).
    쓸 만함 = 둘 다 SHARED_MAX_AGE_H 안에 받은 것 + 지금 파일보다 새것 + 채워진 칸이 지금 파일의 90% 이상 (반쯤 실패한 파일을 막으려고)."""
    import urllib.request
    got, not_newer = {}, []
    for name, var in (("data.js", "OW_DATA"), ("data-qp.js", "OW_DATA_QP")):
        try:
            req = urllib.request.Request(base + name, headers={"User-Agent": nexon.USER_AGENT, "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=30) as r:
                text = r.read().decode("utf-8")
            if not text.startswith(f"window.{var} = "):
                raise ValueError("모양이 다름")
            got[name] = json.loads(text[text.index("{"): text.rindex("}") + 1])
        except Exception as e:
            print(f"공유 통계 {name} 못 받음: {e}")
            return 1
    for name, local in (("data.js", OUT_PATH), ("data-qp.js", QP_PATH)):
        d = got[name]
        age = _age_hours(d.get("updated"))
        if age > SHARED_MAX_AGE_H:
            print(f"공유 통계 {name}가 {age:.0f}시간 전 것이라 직접 받음")
            return 1
        old = read_data(local) if os.path.exists(local) else {}
        if old and _age_hours(old.get("updated")) <= age + 0.01:  # 같은 시각에 받은 것도 새것이 아님 (두 번 재는 사이 시간 차 빼고)
            not_newer.append(name)
            continue
        if old and _filled(d.get("stats")) < _filled(old.get("stats")) * 0.9:
            print(f"공유 통계 {name}에 빈 칸이 많아 직접 받음")
            return 1
        # 공유 통계가 패치 직후의 적은 통계이고(GitHub 작업이 아직 유지로 바꾸기 전) 지금 파일이 그 전 것이면 지금 파일을 유지
        # (공유 쪽이 이미 '유지' 표시를 달고 온 것은 그대로 받는다 — 거기서 같은 판단을 했음)
        if old and not d.get("held"):
            hold, ratio = should_hold(d.get("stats"), old)
            if hold:
                got[name] = held_copy(old, ratio, datetime.now(KST).strftime("%Y-%m-%d %H:%M"), d.get("stats"))
                print(f"공유 통계 {name}: 새 통계 판 수가 지금 통계의 약 1/{1 / ratio:.0f} (패치 직후로 보임) → {got[name]['held']['from']} 통계 유지")
    if len(not_newer) == 2:
        # 공유 통계는 하루 1번 올라오고 앱은 20시간마다 확인한다. 아직 그대로면 넥슨에 직접 받으러 가지 않고 다음 확인까지 둔다
        print("공유 통계가 아직 그대로라 지금 통계를 씀")
        return 0
    if not_newer:
        print(f"공유 통계 {not_newer[0]}가 지금 파일보다 새것이 아니라 직접 받음")
        return 1
    data, qp = got["data.js"], got["data-qp.js"]
    if not data.get("heroes") or not data.get("maps"):
        print("공유 통계에 영웅·맵 목록이 없어 직접 받음")
        return 1
    cache_images(data["heroes"])  # 새 영웅 사진만 넥슨에서 한 번
    write_qp(qp)
    write_data(data)
    held = (data.get("held") or {}).get("from")
    print(f"공유 통계 저장 완료 ({data.get('updated')}에 받은 것, {len(data['heroes'])}명"
          + (f", 패치 직후라 {held} 통계 유지 중)" if held else ")"))
    return 0


SKILLS_EVERY_H = 7 * 24  # 영웅 기술 이름은 잘 안 바뀌어서 일주일에 한 번 (새 영웅은 바로)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="korea")
    ap.add_argument("--input", default="pc")
    ap.add_argument("--ranks", default="", help="쉼표로 구분 (비우면 전체 티어)")
    ap.add_argument("--delay", type=float, default=0.4, help="요청 사이 대기(초). 실패하면 저절로 늘림")
    ap.add_argument("--first", default="", help="먼저 받아 바로 저장할 티어 (쉼표로 구분, 예: grandmaster). '전체'는 늘 맨 먼저")
    ap.add_argument("--shared", action="store_true", help="공유 통계만 받기 (못 쓰면 1로 끝남)")
    ap.add_argument("--images-only", action="store_true", help="통계는 그대로 두고 영웅 사진만 받기")
    ap.add_argument("--skills-only", action="store_true", help="통계는 그대로 두고 영웅 기술 이름만 받기")
    ap.add_argument("--queue", choices=["both", "comp", "quick"], default="both",
                    help="경쟁전(comp)·빠른 대전(quick) 중 받을 것 (기본: 둘 다)")
    args = ap.parse_args(argv)

    if args.shared:
        return fetch_shared()
    if args.images_only or args.skills_only:
        data = read_data()
        if args.images_only:
            cache_images(data["heroes"])
        if args.skills_only:
            fetch_skills(data["heroes"])
            data["skillsAt"] = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
        write_data(data)
        return 0

    filters, _ = nexon.get_filters_and_list()
    ranks = [r for r in filters.get("ranks", []) if r.get("value")]
    if args.ranks:
        wanted = set(args.ranks.split(","))
        ranks = [r for r in ranks if r["value"] in wanted or r["value"] == "all"]
    # 받는 순서: '전체' → --first 티어 → 나머지 (화면에 쓰는 티어부터 새것이 되게). 저장하는 티어 목록 순서는 그대로
    first = [t for t in args.first.split(",") if t and t != "all"]
    order = sorted(ranks, key=lambda r: (r["value"] != "all", r["value"] not in first, ranks.index(r)))
    n_first = sum(1 for r in order if r["value"] == "all" or r["value"] in first)
    # parentValue == 'battlefield' 는 모드 묶음(쟁탈/호위...)이고, 그 외가 실제 맵
    modes = [m for m in filters.get("maps", []) if m.get("parentValue") == "battlefield"]
    maps = [m for m in filters.get("maps", []) if m.get("parentValue") not in ("", "battlefield", None)]
    map_keys = ["all"] + [m["value"] for m in maps]
    old = read_data() if os.path.exists(OUT_PATH) else {}

    heroes = {}
    total = len(ranks) * len(map_keys)
    status = 0
    now = lambda: datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    ordered = lambda st: {r["value"]: st[r["value"]] for r in ranks if r["value"] in st}  # 받은 순서가 아니라 티어 순서로 저장

    def build(stats):
        # 예전에 받아 둔 영웅 사진 자리·기술 이름은 그대로 이어 쓴다
        known = old.get("heroes") or {}
        hs = {hid: {**h, **{k: v for k, v in known.get(hid, {}).items() if k in ("local", "skills")}} for hid, h in heroes.items()}
        return dict(
            updated=now(), source="https://overwatch.nexon.com/hero/rate",
            region=args.region, input=args.input, queue="경쟁전 - 역할 고정",
            ranks=[dict(value=r["value"], name=r["name"]) for r in ranks],
            modes=[dict(value=m["value"], name=m["name"]) for m in modes],
            maps=[dict(value=m["value"], name=m["name"], mode=m["parentValue"]) for m in maps],
            roles=[dict(value=x["value"], name=x["name"], parent=x.get("parentValue"))
                   for x in filters.get("roles", [])],
            heroes=hs, skillsAt=old.get("skillsAt"),
            stats=ordered(stats),  # stats[rank][map][heroId] = [픽률, 승률, 밴률]
        )

    def early(stats, failed):
        # '전체'와 --first 티어를 다 받은 순간 나머지 티어는 예전 값으로 채워 한 번 저장 → 화면이 바로 새 통계
        if len(stats) != n_first or n_first == len(ranks) or not old.get("stats") or len(failed) > n_first * len(map_keys) * 0.1:
            return
        # 이전 통계를 유지하는 중이거나 '전체' 티어부터 판 수가 확 줄었으면(패치 직후) 섞어 저장하지 않고 끝에서 정한다
        quick = games_ratio(stats, old["stats"], ("all",))
        if old.get("held") or (quick is not None and quick < HOLD_RATIO):
            return
        write_data(build({**old["stats"], **stats}))
        print(f"\n먼저 받은 티어({', '.join(stats)}) 저장. 나머지 티어는 계속 받는 중")

    def save_comp(stats):
        data = build(stats)
        cache_images(data["heroes"])
        if _age_hours(data.get("skillsAt")) > SKILLS_EVERY_H:
            fetch_skills(data["heroes"])
            data["skillsAt"] = now()
        else:
            fresh = {hid: h for hid, h in data["heroes"].items() if not h.get("skills")}
            if fresh:
                fetch_skills(fresh)
        write_data(data)
        print(f"저장 완료: {OUT_PATH} ({len(heroes)}명, {total}개 조합)")

    # 경쟁전 먼저 (밴이 있고 더 많이 씀)
    if args.queue in ("both", "comp"):
        stats, failed = collect("2", order, map_keys, args, heroes, "경쟁전", on_rank=early)
        # 네트워크 문제 등으로 많이 실패했으면 기존의 멀쩡한 데이터를 덮어쓰지 않는다
        if len(failed) > total * 0.1 and os.path.exists(OUT_PATH):
            print("실패가 많아 기존 data.js 유지. 잠시 후 다시 시도")
            return 1
        hold, ratio = should_hold(stats, old)
        if hold:
            kept = held_copy(old, ratio, now(), stats)
            write_data(kept)
            print(f"경쟁전: 새 통계 판 수가 지금 통계의 약 1/{1 / ratio:.0f} (패치 직후로 보임) → {kept['held']['from']} 통계 유지")
        else:
            if old.get("held"):
                print("경쟁전: 새 통계가 충분히 쌓여 (또는 유지 기간이 지나) 새 통계로 바꿈")
            save_comp(stats)
    # 빠른 대전 - 역할 고정 (rq=0): 밴이 없어서 밴률은 0. 실패가 많으면 기존 파일 유지
    if args.queue in ("both", "quick"):
        qstats, qfailed = collect("0", order, map_keys, args, heroes, "빠른 대전")
        old_qp = read_data(QP_PATH) if os.path.exists(QP_PATH) else {}
        qhold, qratio = should_hold(qstats, old_qp)
        if len(qfailed) > total * 0.1 and os.path.exists(QP_PATH):
            print("빠른 대전: 실패가 많아 기존 data-qp.js 유지")
            status = 1
        elif qhold:
            kept = held_copy(old_qp, qratio, now(), qstats)
            write_qp(kept)
            print(f"빠른 대전: 새 통계 판 수가 지금 통계의 약 1/{1 / qratio:.0f} → {kept['held']['from']} 통계 유지")
        else:
            write_qp(dict(updated=now(), source="https://overwatch.nexon.com/hero/rate",
                          region=args.region, input=args.input, queue="빠른 대전 - 역할 고정", stats=ordered(qstats)))
            print(f"저장 완료: {QP_PATH}")
    return status


if __name__ == "__main__":
    sys.exit(main())

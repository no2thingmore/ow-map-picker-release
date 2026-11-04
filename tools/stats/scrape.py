"""넥슨 공식 통계에서 경쟁전 기준 [티어 × 맵] 전체 조합을 받아 data.js로 저장.

사용: python scrape.py [--region korea] [--input pc] [--ranks diamond,master] [--delay 0.4] [--first grandmaster]
      python scrape.py --shared      공개 저장소의 공유 통계(GitHub가 하루 두 번 받아 둔 것)만 받기 (몇 초)
"""
import argparse
import json
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
# 공유 통계: 공개 저장소 stats 가지에 GitHub가 하루 두 번 넥슨에서 받아 올려 둔 data.js · data-qp.js
# (사람마다 넥슨에 576쪽씩 요청하던 것을 한 번으로. 받는 쪽은 파일 두 개 = 몇 초)
SHARED_BASE = "https://raw.githubusercontent.com/no2thingmore/ow-map-picker-release/stats/"
SHARED_MAX_AGE_H = 30   # 이보다 오래된 공유 통계는 안 씀 (GitHub 작업이 멈췄을 때는 직접 받게)
DELAY_MAX = 5.0         # 막히면(실패하면) 요청 사이 대기를 이만큼까지 늘림


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


def read_data(path=OUT_PATH):
    with open(path, encoding="utf-8") as f:
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


def fetch_shared(base=SHARED_BASE):
    """공유 통계(data.js · data-qp.js)를 받아 쓸 만하면 저장 → 0, 못 쓰면 1 (그땐 넥슨에서 직접 받는다).
    쓸 만함 = 둘 다 SHARED_MAX_AGE_H 안에 받은 것 + 지금 파일보다 새것 + 채워진 칸이 지금 파일의 90% 이상 (반쯤 실패한 파일을 막으려고)."""
    import urllib.request
    got = {}
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
    data, qp = got["data.js"], got["data-qp.js"]
    for name, d, local in (("data.js", data, OUT_PATH), ("data-qp.js", qp, QP_PATH)):
        age = _age_hours(d.get("updated"))
        if age > SHARED_MAX_AGE_H:
            print(f"공유 통계 {name}가 {age:.0f}시간 전 것이라 직접 받음")
            return 1
        old = read_data(local) if os.path.exists(local) else {}
        if old and _age_hours(old.get("updated")) <= age + 0.01:  # 같은 시각에 받은 것도 새것이 아님 (두 번 재는 사이 시간 차 빼고)
            print(f"공유 통계 {name}가 지금 파일보다 새것이 아니라 직접 받음")
            return 1
        if old and _filled(d.get("stats")) < _filled(old.get("stats")) * 0.9:
            print(f"공유 통계 {name}에 빈 칸이 많아 직접 받음")
            return 1
    if not data.get("heroes") or not data.get("maps"):
        print("공유 통계에 영웅·맵 목록이 없어 직접 받음")
        return 1
    cache_images(data["heroes"])  # 새 영웅 사진만 넥슨에서 한 번
    write_qp(qp)
    write_data(data)
    print(f"공유 통계 저장 완료 ({data.get('updated')}에 받은 것, {len(data['heroes'])}명)")
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
        write_data(build({**old["stats"], **stats}))
        print(f"\n먼저 받은 티어({', '.join(stats)}) 저장. 나머지 티어는 계속 받는 중")

    # 경쟁전 먼저 (밴이 있고 더 많이 씀)
    if args.queue in ("both", "comp"):
        stats, failed = collect("2", order, map_keys, args, heroes, "경쟁전", on_rank=early)
        # 네트워크 문제 등으로 많이 실패했으면 기존의 멀쩡한 데이터를 덮어쓰지 않는다
        if len(failed) > total * 0.1 and os.path.exists(OUT_PATH):
            print("실패가 많아 기존 data.js 유지. 잠시 후 다시 시도")
            return 1
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
    # 빠른 대전 - 역할 고정 (rq=0): 밴이 없어서 밴률은 0. 실패가 많으면 기존 파일 유지
    if args.queue in ("both", "quick"):
        qstats, qfailed = collect("0", order, map_keys, args, heroes, "빠른 대전")
        if len(qfailed) > total * 0.1 and os.path.exists(QP_PATH):
            print("빠른 대전: 실패가 많아 기존 data-qp.js 유지")
            status = 1
        else:
            write_qp(dict(updated=now(), source="https://overwatch.nexon.com/hero/rate",
                          region=args.region, input=args.input, queue="빠른 대전 - 역할 고정", stats=ordered(qstats)))
            print(f"저장 완료: {QP_PATH}")
    return status


if __name__ == "__main__":
    sys.exit(main())

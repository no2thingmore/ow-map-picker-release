"""소개 페이지의 '업데이트 내역'(docs/releases.html)을 개발 저장소의 changes.json으로 만든다.

사용: python tools/site/build_releases.py <개발 저장소의 changes.json>
- 버전마다 날짜 · 바뀐 점 · 사진(changes.json의 media)을 넣고, 사진 그림은 docs/site/img/changes/로 복사한다.
- 제목은 changes.json의 summary(요약 한 줄), 없으면 docs/releases/v<버전>.md 첫 줄. 그 파일이 있으면 '사진으로 자세히' 링크를 단다.
- 바뀐 점 앞 [추가]/[개선]/[고침]은 색 표시로 (프로그램 '업데이트 내역' 화면과 같은 모양).
- 화면 규칙: 최신 버전을 맨 위에 크게, 바뀐 점이 많으면 5개만 보이고 나머지는 펼쳐 보기, 0.8.0 전 버전은 한 묶음으로 접어 둠.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCS = os.path.join(ROOT, "docs")
REPO = "https://github.com/no2thingmore/ow-map-picker-release"
SITE = "https://no2thingmore.github.io/ow-map-picker-release/"
SHOW = 5          # 버전마다 처음 보이는 바뀐 점 개수
OPEN_FROM = (0, 8, 0)  # 이 버전부터는 펼친 채로, 그 전은 '이전 버전' 묶음
esc = html.escape
TAGS = None  # GitHub에 실제로 있는 릴리스 (없는 버전은 '받기' 링크를 안 단다)


def has_release(v):
    return TAGS is None or f"v{v}" in TAGS


def ver_tuple(v):
    return tuple(int(x) for x in v.split("."))


def title_of(v):
    p = os.path.join(DOCS, "releases", f"v{v}.md")
    if not os.path.exists(p):
        return None, False
    first = open(p, encoding="utf-8").readline().strip()
    # 새 형식 '# v0.8.3 통계 받기가 7분에서 1초로' → 버전 뒤 글자, 예전 형식 '# v0.8.2 · 사진으로 … (제목)' → 괄호 안
    m = re.match(r"#\s*v[\d.]+\s+(?!·)(.+)$", first) or re.search(r"\(([^)]+)\)\s*$", first)
    return (m.group(1).strip() if m else None), True


TAG = re.compile(r"^\[(추가|개선|고침)\]\s*")
TAG_CLS = {"추가": "add", "개선": "imp", "고침": "fix"}


def li(t):
    m = TAG.match(t)
    if not m:
        return f"<li>{esc(t)}</li>"
    return f"<li><span class=\"it-tag {TAG_CLS[m.group(1)]}\">{m.group(1)}</span><span>{esc(t[m.end():])}</span></li>"


def ul(items):
    tagged = any(TAG.match(t) for t in items)
    return f"<ul class=\"rel-items{' tg' if tagged else ''}\">{''.join(li(t) for t in items)}</ul>"


def items_html(items):
    if len(items) <= SHOW + 1:
        return ul(items)
    return (ul(items[:SHOW])
            + f"<details class=\"more\"><summary>바뀐 점 {len(items) - SHOW}개 더 보기</summary>{ul(items[SHOW:])}</details>")


def media_html(media, src_root):
    if not media:
        return ""
    out_dir = os.path.join(DOCS, "site", "img", "changes")
    os.makedirs(out_dir, exist_ok=True)
    figs = []
    for m in media:
        src = os.path.join(src_root, m["src"])
        name = os.path.basename(m["src"])
        shutil.copyfile(src, os.path.join(out_dir, name))
        with Image.open(src) as im:
            w, h = im.size
        figs.append(f"<figure class=\"pic\"><img src=\"site/img/changes/{esc(name)}\" width=\"{w}\" height=\"{h}\" alt=\"{esc(m.get('alt', ''))}\" loading=\"lazy\">"
                    + (f"<figcaption>{esc(m['caption'])}</figcaption>" if m.get("caption") else "") + "</figure>")
    return f"<div class=\"rel-media\">{''.join(figs)}</div>"


def links_html(v, has_md):
    a = [f"<a class=\"btn ghost sm\" href=\"{REPO}/releases/tag/v{v}\">이 버전 받기</a>"] if has_release(v) else []
    if has_md:
        a.append(f"<a class=\"btn ghost sm\" href=\"{REPO}/blob/main/docs/releases/v{v}.md\">사진으로 자세히</a>")
    return f"<div class=\"rel-links\">{''.join(a)}</div>" if a else ""


def article(e, src_root, latest=False):
    v, date = e["version"], e.get("date", "")
    title, has_md = title_of(v)
    title = e.get("summary") or title
    head = (f"<header class=\"rel-head\"><h2 class=\"rel-ver disp\" id=\"v{v}\">v{esc(v)}</h2>"
            + (f"<span class=\"rel-badge\">최신</span>" if latest else "")
            + f"<time datetime=\"{esc(date)}\">{esc(date.replace('-', '. '))}.</time>"
            + (f"<p class=\"rel-title\">{esc(title)}</p>" if title else "") + "</header>")
    return (f"<article class=\"rel{' latest' if latest else ''}\" aria-labelledby=\"v{v}\">{head}"
            f"{items_html(e['items'])}{media_html(e.get('media'), src_root)}{links_html(v, has_md)}</article>")


def old_row(e):
    v, date = e["version"], e.get("date", "")
    title, has_md = title_of(v)
    title = e.get("summary") or title
    get = f"<a href=\"{REPO}/releases/tag/v{v}\">이 버전 받기</a>" if has_release(v) else "GitHub 릴리스 없음"
    extra = f" · <a href=\"{REPO}/blob/main/docs/releases/v{v}.md\">사진으로 자세히</a>" if has_md else ""
    return (f"<details class=\"more old\" id=\"v{v}\"><summary><span class=\"rel-ver-sm\">v{esc(v)}</span>"
            f"<span class=\"old-meta\">{esc(date.replace('-', '. '))}.{(' · ' + esc(title)) if title else ''} · 바뀐 점 {len(e['items'])}개</span></summary>"
            f"{ul(e['items'])}"
            f"<p class=\"old-links\">{get}{extra}</p></details>")


def main(changes_path):
    global TAGS
    try:
        out = subprocess.run(["gh", "release", "list", "-R", "no2thingmore/ow-map-picker-release", "-L", "200", "--json", "tagName", "--jq", ".[].tagName"],
                             capture_output=True, text=True, timeout=30, check=True).stdout.split()
        TAGS = set(out) or None
    except (OSError, subprocess.SubprocessError):
        TAGS = None  # gh가 없으면 모든 버전에 링크
    src_root = os.path.dirname(os.path.abspath(changes_path))
    data = json.load(open(changes_path, encoding="utf-8"))
    data.sort(key=lambda e: ver_tuple(e["version"]), reverse=True)
    new = [e for e in data if ver_tuple(e["version"]) >= OPEN_FROM]
    old = [e for e in data if ver_tuple(e["version"]) < OPEN_FROM]
    top = new[0]
    toc = "".join(f"<li><a href=\"#v{e['version']}\">v{esc(e['version'])}</a></li>" for e in new) + f"<li><a href=\"#older\">이전 버전 {len(old)}개</a></li>"
    body = "".join(article(e, src_root, latest=(e is top)) for e in new)
    page = TEMPLATE.format(latest=esc(top["version"]), date=esc(top.get("date", "")), toc=toc, body=body,
                           older="".join(old_row(e) for e in old), n_old=len(old), first_old=esc(old[0]["version"]) if old else "",
                           last_old=esc(old[-1]["version"]) if old else "", site=SITE, repo=REPO)
    out = os.path.join(DOCS, "releases.html")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print(out, len(page) // 1024, "KB,", len(new), "버전 펼침 +", len(old), "버전 묶음")


TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="google-site-verification" content="iW7dX4CgawFbVuh55kqrlvdH8QZOWC4l0NRZZ0WInyc" />
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>업데이트 내역 · 버전별 바뀐 점 | 오버워치 영웅 선택 가이드</title>
<meta name="description" content="오버워치 영웅 선택 가이드의 버전별 바뀐 점. 최신 v{latest}({date})부터 처음 버전까지, 사진과 내려받기 링크.">
<link rel="canonical" href="{site}releases.html">
<meta name="theme-color" content="#101318">
<link rel="icon" href="site/icon.svg" type="image/svg+xml">
<meta property="og:type" content="article">
<meta property="og:locale" content="ko_KR">
<meta property="og:site_name" content="오버워치 영웅 선택 가이드">
<meta property="og:title" content="업데이트 내역 · 최신 v{latest} | 오버워치 영웅 선택 가이드">
<meta property="og:description" content="버전마다 바뀐 점과 사진.">
<meta property="og:url" content="{site}releases.html">
<meta property="og:image" content="{site}og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="preload" href="site/fonts/ow-site-kr.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="site/site.css">
</head>
<body>
<a class="skip" href="#main">본문으로 건너뛰기</a>
<header class="top">
  <div class="wrap">
    <a class="brand disp" href="./"><img src="site/icon.svg" alt="" width="30" height="30"><span>오버워치 <b>영웅 선택 가이드</b></span></a>
    <nav class="nav" aria-label="사이트">
      <a href="./#features">기능</a><a href="guide.html">사용법</a><a href="releases.html" aria-current="page">업데이트 내역</a><a href="./#faq">자주 묻는 질문</a>
    </nav>
    <a class="btn go" href="{repo}/releases/latest/download/OW-MapPicker.bat">무료로 받기</a>
  </div>
</header>

<main id="main" class="doc">
  <div class="wrap">
    <h1 class="disp">업데이트 내역</h1>
    <p class="lead">버전마다 바뀐 점. 새 버전이 나오면 프로그램이 알림, 업데이트해도 전적과 설정은 그대로.</p>
    <nav aria-label="버전 목차"><ul class="toc">{toc}</ul></nav>
    <div class="rel-list">{body}</div>
    <section id="older" class="older" aria-labelledby="older-h">
      <h2 id="older-h" class="disp">이전 버전</h2>
      <p>v{first_old}부터 v{last_old}까지 {n_old}개. 버전을 누르면 바뀐 점이 펼쳐짐.</p>
      {older}
    </section>
  </div>

  <div class="cta">
    <div class="wrap">
      <div><h2 class="disp">최신 버전 받기</h2><p>v{latest} · 파일 하나 받아 더블클릭하면 끝.</p></div>
      <a class="btn go" href="{repo}/releases/latest/download/OW-MapPicker.bat"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"/></svg>무료로 받기</a>
    </div>
  </div>
</main>

<footer class="foot">
  <div class="wrap">
    <p>개인이 만든 <b>비공식</b> 팬 제작 도구. Blizzard Entertainment, 넥슨과 관련 없음. Overwatch는 Blizzard Entertainment, Inc.의 상표.</p>
    <p>프로그램 안 '업데이트 내역'과 같은 내용.</p>
    <p><a href="./">처음으로</a> · <a href="guide.html">사용법</a> · <a href="{repo}/releases">GitHub 전체 버전</a></p>
  </div>
</footer>
</body>
</html>
"""

if __name__ == "__main__":
    main(sys.argv[1])

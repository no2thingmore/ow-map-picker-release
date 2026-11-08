"""소개 페이지의 '업데이트 내역'(docs/releases.html)을 개발 저장소의 changes.json으로 만든다.

사용: python tools/site/build_releases.py <개발 저장소의 changes.json>
- 버전마다 날짜 · 요약 한 줄 · 바뀐 점 · 사진(changes.json의 media)을 넣고, 사진 그림은 docs/site/img/changes/로 복사한다.
- 요약은 changes.json의 summary, 없으면 docs/releases/v<버전>.md 첫 줄. 그 파일이 있으면 '사진으로 자세히' 링크를 단다.
- 모양은 프로그램 안 '업데이트 내역' 화면(개발 저장소 changes.html)과 같게 (2026-11-08 사용자 요청):
  왼쪽 버전 목록 + 오른쪽 마름모 시간줄, 바뀐 점은 모두 보이게, [추가]/[개선]/[고침]은 색 표시, 개선 전/후 사진 나란히, 누르면 크게.
  프로그램 화면 위쪽의 업데이트 방식 칸은 넣지 않는다.
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


def item_list(items):
    if not items:
        return ""
    if not any(TAG.match(t) for t in items):
        return f"<ul>{''.join(f'<li>{esc(t)}</li>' for t in items)}</ul>"

    def li(t):
        m = TAG.match(t)
        if not m:
            return f"<li><span></span><span>{esc(t)}</span></li>"
        return f"<li><span class=\"it-tag {TAG_CLS[m.group(1)]}\">{m.group(1)}</span><span>{esc(t[m.end():])}</span></li>"
    return f"<ul class=\"tg\">{''.join(li(t) for t in items)}</ul>"


def copy_img(src_root, rel):
    """개발 저장소의 사진을 docs/site/img/changes/로 복사하고 (사이트 주소, 폭, 높이)를 돌려준다"""
    out_dir = os.path.join(DOCS, "site", "img", "changes")
    os.makedirs(out_dir, exist_ok=True)
    src, name = os.path.join(src_root, rel), os.path.basename(rel)
    shutil.copyfile(src, os.path.join(out_dir, name))
    with Image.open(src) as im:
        w, h = im.size
    return f"site/img/changes/{esc(name)}", w, h


def zoom_img(src_root, rel, alt):
    url, w, h = copy_img(src_root, rel)
    return (f"<button type=\"button\" class=\"zoom\" data-zoom aria-label=\"사진 크게 보기\">"
            f"<img src=\"{url}\" width=\"{w}\" height=\"{h}\" alt=\"{esc(alt)}\" loading=\"lazy\" decoding=\"async\"></button>")


def media_html(media, src_root, version, prev):
    """{before, after} 쌍은 왼쪽 '개선 전 v이전'(회색) · 오른쪽 '개선 후 v이번'(주황) 나란히, {src} 한 장은 폭 전체"""
    if not media:
        return ""
    figs = []
    for m in media:
        cap = f"<figcaption>{esc(m['caption'])}</figcaption>" if m.get("caption") else ""
        alt = m.get("alt", "")
        if m.get("src"):
            figs.append(f"<figure class=\"rel-fig one\">{zoom_img(src_root, m['src'], alt)}{cap}</figure>")
            continue
        frm = m.get("from") or prev
        figs.append("<figure class=\"rel-fig pair\"><div class=\"cmp\">"
                    f"<div><div class=\"cmp-lab before\">개선 전{(' <b>v' + esc(frm) + '</b>') if frm else ''}</div>{zoom_img(src_root, m['before'], (alt + ' (개선 전)').strip())}</div>"
                    f"<div><div class=\"cmp-lab after\">개선 후 <b>v{esc(version)}</b></div>{zoom_img(src_root, m['after'], (alt + ' (개선 후)').strip())}</div>"
                    f"</div>{cap}</figure>")
    return f"<div class=\"rel-media\">{''.join(figs)}</div>"


def links_html(v, has_md):
    a = [f"<a href=\"{REPO}/releases/tag/v{v}\">이 버전 받기</a>"] if has_release(v) else []
    if has_md:
        a.append(f"<a href=\"{REPO}/blob/main/docs/releases/v{v}.md\">사진으로 자세히</a>")
    return f"<p class=\"rel-links\">{''.join(a)}</p>" if a else ""


def entry(e, src_root, latest, prev):
    v, date = e["version"], e.get("date", "")
    title, has_md = title_of(v)
    title = e.get("summary") or title
    head = (f"<div class=\"rel-head\"><h2 class=\"rel-ver\">v{esc(v)}</h2>"
            + ("<span class=\"rel-badge\">최신</span>" if latest else "")
            + (f"<time datetime=\"{esc(date)}\">{esc(date)}</time>" if date else "") + "</div>")
    return (f"<li class=\"rel {'now' if latest else 'old'}\" id=\"v{esc(v)}\">{head}"
            + (f"<p class=\"rel-sum\">{esc(title)}</p>" if title else "")
            + item_list(e["items"]) + media_html(e.get("media"), src_root, v, prev) + links_html(v, has_md) + "</li>")


def vers_link(e, latest):
    v, date = e["version"], e.get("date", "")
    cls, mark = (' class="now"', " <small>최신</small>") if latest else ("", "")
    return (f"<a href=\"#v{esc(v)}\" data-ver=\"{esc(v)}\"{cls}><span>v{esc(v)}{mark}</span>"
            + (f"<span class=\"d\">{esc(date)}</span>" if date else "") + "</a>")


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
    top = data[0]
    vers = "".join(vers_link(e, e is top) for e in data)
    log = "".join(entry(e, src_root, e is top, data[i + 1]["version"] if i + 1 < len(data) else None) for i, e in enumerate(data))
    page = TEMPLATE.format(latest=esc(top["version"]), date=esc(top.get("date", "")), vers=vers, log=log, site=SITE, repo=REPO, script=SCRIPT)
    out = os.path.join(DOCS, "releases.html")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print(out, len(page) // 1024, "KB,", len(data), "버전")


# 버전 목록: 보고 있는 버전 강조. 사진: 누르면 확대 창(쌍은 나란히), 바깥·✕·Esc로 닫고 눌렀던 사진으로 포커스. 프로그램 changes.html과 같은 동작
SCRIPT = """(() => {
  const $ = (s) => document.querySelector(s);
  if ("IntersectionObserver" in window) {
    const seen = new Map(), links = [...document.querySelectorAll("#vers a")];
    const io = new IntersectionObserver((ents) => {
      for (const x of ents) seen.set(x.target, x.isIntersecting ? x.boundingClientRect.top : null);
      const top = [...seen].filter(([, t]) => t != null).sort((a, b) => a[1] - b[1])[0];
      links.forEach((a) => a.classList.toggle("cur", !!top && top[0].id === "v" + a.dataset.ver));
    }, { rootMargin: "-10% 0px -60% 0px" });
    document.querySelectorAll(".rel").forEach((el) => io.observe(el));
  }
  const lb = $("#lb"), body = $("#lbBody");
  let from = null;
  const open = (btn) => {
    const fig = btn.closest("figure"), imgs = [...fig.querySelectorAll(".zoom img")], labs = [...fig.querySelectorAll(".cmp-lab")], cap = fig.querySelector("figcaption");
    body.textContent = "";
    const grid = document.createElement("div");
    grid.className = "lb-grid" + (imgs.length > 1 ? " pair" : "");
    imgs.forEach((im, i) => {
      const item = document.createElement("div");
      item.className = "lb-item";
      if (labs[i]) item.appendChild(labs[i].cloneNode(true));
      const big = document.createElement("img");
      big.src = im.getAttribute("src"); big.alt = im.alt;
      item.appendChild(big); grid.appendChild(item);
    });
    body.appendChild(grid);
    if (cap) { const p = document.createElement("p"); p.className = "lb-cap"; p.textContent = cap.textContent; body.appendChild(p); }
    from = btn; lb.hidden = false; document.body.classList.add("lb-open");
    requestAnimationFrame(() => lb.classList.add("in"));
    $(".lb-x").focus();
  };
  const close = () => {
    lb.classList.remove("in"); lb.hidden = true; document.body.classList.remove("lb-open");
    if (from && from.isConnected) from.focus();
    from = null;
  };
  $("#log").addEventListener("click", (e) => { const b = e.target.closest("[data-zoom]"); if (b) open(b); });
  lb.addEventListener("click", (e) => { if (!e.target.closest(".lb-item, .lb-cap") || e.target.closest(".lb-x")) close(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !lb.hidden) { e.preventDefault(); close(); } });
})();"""

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
<link rel="icon" href="site/favicon.ico" sizes="any">
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

<main id="main" class="doc chg">
  <div class="wrap">
    <div class="chg-head">
      <h1 class="disp"><b>업데이트</b> 내역</h1>
      <a href="{repo}/releases">지난 버전 파일: GitHub 릴리스</a>
    </div>
    <div class="page">
      <nav class="vers" id="vers" aria-label="버전 목록"><div class="vers-lab">버전</div>{vers}</nav>
      <ol class="log" id="log" aria-label="버전별 바뀐 점">{log}</ol>
    </div>
  </div>

  <div class="cta">
    <div class="wrap">
      <div><h2 class="disp">최신 버전 받기</h2><p>v{latest} · 파일 하나 받아 더블클릭하면 끝.</p></div>
      <a class="btn go" href="{repo}/releases/latest/download/OW-MapPicker.bat"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"/></svg>무료로 받기</a>
    </div>
  </div>
</main>

<div class="lb" id="lb" role="dialog" aria-modal="true" aria-label="사진 크게 보기" hidden>
  <button type="button" class="lb-x" aria-label="닫기">✕</button>
  <div class="lb-body" id="lbBody"></div>
</div>

<footer class="foot">
  <div class="wrap">
    <p>개인이 만든 <b>비공식</b> 팬 제작 도구. Blizzard Entertainment, 넥슨과 관련 없음. Overwatch는 Blizzard Entertainment, Inc.의 상표.</p>
    <p>프로그램 안 '업데이트 내역'과 같은 내용.</p>
    <p><a href="./">처음으로</a> · <a href="guide.html">사용법</a> · <a href="{repo}/releases">GitHub 전체 버전</a></p>
  </div>
</footer>
<script>{script}</script>
</body>
</html>
"""

if __name__ == "__main__":
    main(sys.argv[1])

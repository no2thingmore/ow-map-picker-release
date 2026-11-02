"""README 꾸밈 이미지(SVG) 만들기: 배너·버튼·기능 카드·구간 제목.

PC(README 폭 약 830px)와 휴대폰(약 343px) 모두에서 글자가 읽히도록:
- 배너는 폭 900으로 그려 휴대폰에서도 본문 글자가 약 12px
- 기능 카드는 한 장씩 따로 (표시 폭 400) → PC는 두 장씩 나란히, 휴대폰은 한 장씩 아래로
- 구간 제목은 표시 폭 420 고정 → PC·휴대폰 크기가 거의 같음

글꼴은 Noto Sans KR(OFL)에서 쓰는 글자만 잘라 SVG 안에 넣는다 → 보는 PC에 글꼴이 없어도 똑같이 보임.
사용: python build.py <fonttools·Pillow 경로> <출력 폴더> <main.png 경로>
"""
import base64
import io
import sys

sys.path.insert(0, sys.argv[1])
from fontTools.ttLib import TTFont  # noqa: E402
from fontTools.varLib import instancer  # noqa: E402
from fontTools import subset  # noqa: E402
from PIL import Image  # noqa: E402

OUT = sys.argv[2]
SHOT = sys.argv[3]
FONT = "C:/Windows/Fonts/NotoSansKR-VF.ttf"

BG, PANEL, LINE = "#14161b", "#1b1e25", "#2a2f3a"
ORG, ORG2, TXT, MUTED = "#f99e1a", "#ffb546", "#eef1f6", "#9aa4b2"

_inst = {}


def font_face(family, weight, text):
    if weight not in _inst:
        tmp = io.BytesIO()
        instancer.instantiateVariableFont(TTFont(FONT), {"wght": weight}).save(tmp)
        _inst[weight] = tmp.getvalue()
    sub = TTFont(io.BytesIO(_inst[weight]))
    opts = subset.Options()
    opts.flavor = "woff"
    s = subset.Subsetter(opts)
    s.populate(text=text + " ")
    s.subset(sub)
    sub.flavor = "woff"
    buf = io.BytesIO()
    sub.save(buf)
    b = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'{family}';src:url(data:font/woff;base64,{b}) format('woff');}}"


def svg(w, h, body, texts, size=None):
    """texts: {'H': 제목 글자, 'B': 굵은 글자, 'R': 본문 글자}, size: 기본 표시 크기"""
    faces = "".join(font_face(fam, wt, texts[fam]) for fam, wt in (("H", 900), ("B", 700), ("R", 400)) if texts.get(fam))
    sw, sh = size or (w, h)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{sw}" height="{sh}">
<style>{faces}
.h{{font-family:'H';font-weight:900}} .b{{font-family:'B';font-weight:700}} .r{{font-family:'R';font-weight:400}}</style>
<defs>
<pattern id="grid" width="36" height="36" patternUnits="userSpaceOnUse"><path d="M36 0H0V36" fill="none" stroke="#ffffff" stroke-opacity=".04"/></pattern>
<linearGradient id="org" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{ORG2}"/><stop offset="1" stop-color="{ORG}"/></linearGradient>
<filter id="shadow" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="16" stdDeviation="16" flood-color="#000" flood-opacity=".55"/></filter>
</defs>
{body}
</svg>"""


def brackets(x, y, w, h, n=18, color=ORG):
    return (f'<path d="M{x} {y + n}V{y}H{x + n}" fill="none" stroke="{color}" stroke-width="3"/>'
            f'<path d="M{x + w - n} {y + h}H{x + w}V{y + h - n}" fill="none" stroke="{color}" stroke-width="3"/>')


def write(name, content):
    with open(f"{OUT}/{name}", "w", encoding="utf-8") as f:
        f.write(content)
    print(name, round(len(content.encode()) / 1024), "KB")


def skewed(x, y, cls, size, fill, text):
    return f'<g transform="translate({x} {y}) skewX(-10)"><text class="{cls}" font-size="{size}" fill="{fill}">{text}</text></g>'


# ---------- 배너 ----------
EYEBROW = "OVERWATCH 2 · 영웅 선택 가이드"
L1, L2 = "이번 판,", "고민 없이 픽."
P1 = "맵·밴·양 팀 조합을 화면에서 읽고"
P2 = "공식 통계와 상성으로 영웅을 추천합니다."
STATS = [("54", "영웅 상성"), ("31", "맵별 통계"), ("9", "티어별")]


def screenshot(width):
    im = Image.open(SHOT).convert("RGB")
    w, h = im.size
    im = im.crop((0, 0, w, int(w * 0.62)))
    im = im.resize((width, int(width * im.size[1] / im.size[0])), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=84, optimize=True)
    return base64.b64encode(buf.getvalue()).decode(), im.size[1]


def hero():
    SW = 560
    shot, sh = screenshot(SW)
    W, H = 900, 640
    stat_svg = ""
    for i, (n, lab) in enumerate(STATS):
        x = 56 + i * 182
        stat_svg += skewed(x, 556, "h", 46, ORG, n)
        stat_svg += f'<text x="{x + 12 + len(n) * 27}" y="553" class="r" font-size="24" fill="{MUTED}">{lab}</text>'
    body = f"""
<rect width="{W}" height="{H}" rx="20" fill="{BG}"/>
<rect width="{W}" height="{H}" rx="20" fill="url(#grid)"/>
<clipPath id="c"><rect width="{W}" height="{H}" rx="20"/></clipPath>
<g clip-path="url(#c)">
  <polygon points="810,0 {W},0 {W},{H} 610,{H}" fill="url(#org)"/>
  <polygon points="776,0 794,0 594,{H} 576,{H}" fill="{ORG}" fill-opacity=".35"/>
  <g transform="translate(612 478) rotate(-5)" filter="url(#shadow)">
    <rect x="-5" y="-5" width="{SW + 10}" height="{sh + 10}" rx="12" fill="#0d0f13"/>
    <image href="data:image/jpeg;base64,{shot}" width="{SW}" height="{sh}"/>
    <rect x="-5" y="-5" width="{SW + 10}" height="{sh + 10}" rx="12" fill="none" stroke="#ffffff" stroke-opacity=".14" stroke-width="2"/>
  </g>
</g>
<path d="M56 86H92" stroke="{ORG}" stroke-width="4"/>
<text x="106" y="95" class="b" font-size="25" letter-spacing="2" fill="{ORG}">{EYEBROW}</text>
{skewed(56, 214, "h", 104, TXT, L1)}
{skewed(56, 332, "h", 104, ORG, L2)}
<text x="58" y="404" class="r" font-size="30" fill="#c6cdd8">{P1}</text>
<text x="58" y="447" class="r" font-size="30" fill="#c6cdd8">{P2}</text>
{stat_svg}
"""
    texts = {"H": L1 + L2 + "".join(n for n, _ in STATS), "B": EYEBROW, "R": P1 + P2 + "".join(lab for _, lab in STATS)}
    write("hero.svg", svg(W, H, body, texts))


# ---------- 버튼 (표시 폭 240) ----------
def buttons():
    lab = "무료로 받기"
    body = f"""
<polygon points="14,0 380,0 366,84 0,84" fill="url(#org)"/>
<g transform="translate(52 26)" fill="none" stroke="#1a1308" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
  <path d="M16 0V22M6 13L16 23L26 13M2 32H30"/></g>
<text x="104" y="55" class="h" font-size="34" fill="#1a1308">{lab}</text>"""
    write("btn-download.svg", svg(380, 84, body, {"H": lab}, (240, 53)))
    lab2 = "사용 방법 보기 →"
    body = f"""
<polygon points="14,1.5 378.5,1.5 365,82.5 1.5,82.5" fill="{PANEL}" stroke="#3a404d" stroke-width="3"/>
<text x="190" y="55" text-anchor="middle" class="b" font-size="30" fill="{TXT}">{lab2}</text>"""
    write("btn-guide.svg", svg(380, 84, body, {"B": lab2}, (240, 53)))


# ---------- 기능 카드 (한 장씩, 표시 폭 400) ----------
ICONS = {
    "scan": '<path d="M4 14V4H14M34 4H44V14M44 34V44H34M14 44H4V34"/><circle cx="24" cy="24" r="8"/>',
    "rank": '<path d="M6 42V26M18 42V14M30 42V22M42 42V6"/>',
    "overlay": '<rect x="4" y="8" width="40" height="30" rx="3"/><rect x="24" y="14" width="14" height="10" rx="2"/>',
    "phone": '<rect x="13" y="3" width="22" height="42" rx="4"/><path d="M21 38H27"/>',
    "history": '<path d="M8 10H40M8 22H40M8 34H28"/><path d="M34 32L38 36L46 26"/>',
    "update": '<path d="M40 22A16 16 0 1 0 36 34M40 10V22H28"/>',
}
FEATURES = [
    ("scan", "자동 인식", "영웅 선택 화면과 점수판(Tab)에서", "맵·밴·아군·적군·등급을 읽습니다."),
    ("rank", "영웅 추천", "공식 통계·상성·시너지·팀 조합으로", "1~3순위를 근거와 함께 보여 줍니다."),
    ("overlay", "오버레이", "게임 위 작은 창에 추천 순위와", "조합 요령을 띄웁니다."),
    ("phone", "폰으로 보기", "같은 Wi-Fi의 휴대폰 브라우저에서", "같은 화면을 볼 수 있습니다."),
    ("history", "전적·통계", "판마다 결과를 저장하고", "맵·영웅·티어별 승률을 보여 줍니다."),
    ("update", "자동 업데이트", "새 버전이 나오면 알림을 띄우고", "버튼 한 번으로 교체합니다."),
]


def features():
    W, H = 620, 200
    for ic, t, d1, d2 in FEATURES:
        body = f"""
<rect x="1.5" y="1.5" width="{W - 3}" height="{H - 3}" fill="{PANEL}" stroke="{LINE}" stroke-width="3"/>
{brackets(1.5, 1.5, W - 3, H - 3, 22)}
<g transform="translate(38 36)" fill="none" stroke="{ORG}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">{ICONS[ic]}</g>
<text x="108" y="74" class="b" font-size="38" fill="{TXT}">{t}</text>
<text x="38" y="132" class="r" font-size="29" fill="{MUTED}">{d1}</text>
<text x="38" y="172" class="r" font-size="29" fill="{MUTED}">{d2}</text>"""
        write(f"card-{ic}.svg", svg(W, H, body, {"B": t, "R": d1 + d2}, (400, 129)))


# ---------- 구간 제목 (표시 폭 420) ----------
SECTIONS = [
    ("features", "FEATURES", "주요", "기능"),
    ("install", "QUICK START", "설치", "방법"),
    ("usage", "HOW TO USE", "사용", "방법"),
    ("screens", "SCREENS", "화면", "구성"),
    ("trouble", "TROUBLESHOOTING", "문제", "해결"),
    ("notice", "NOTICE", "안내", "사항"),
]


def sections():
    W, H = 720, 150
    for key, eb, a, b in SECTIONS:
        body = f"""
<path d="M0 36H44" stroke="{ORG}" stroke-width="5"/>
<text x="60" y="46" class="b" font-size="28" letter-spacing="6" fill="{ORG}">{eb}</text>
<g transform="translate(0 132) skewX(-10)">
  <text class="h" font-size="72" fill="{TXT}">{a} <tspan fill="{ORG}">{b}</tspan></text></g>"""
        write(f"sec-{key}.svg", svg(W, H, body, {"B": eb, "H": a + b}, (420, 88)))


hero()
buttons()
features()
sections()

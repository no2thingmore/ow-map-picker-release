"""README 꾸밈 이미지(SVG) 만들기: 배너·버튼·기능 카드·구간 제목.

PC(README 폭 약 830px)와 휴대폰(약 343px) 모두에서 글자가 읽히도록:
- 배너는 폭 900으로 그려 휴대폰에서도 본문 글자가 약 12px
- 기능 카드는 한 장씩 따로 (표시 폭 400) → PC는 두 장씩 나란히, 휴대폰은 한 장씩 아래로
- 구간 제목은 표시 폭 420 고정 → PC·휴대폰 크기가 거의 같음

글꼴은 Noto Sans KR(OFL)에서 쓰는 글자만 잘라 SVG 안에 넣는다 → 보는 PC에 글꼴이 없어도 똑같이 보임.
사용: python build.py <fonttools·Pillow 경로> <출력 폴더> <main.png 경로> [match.gif 경로 → slides.svg도 만듦] [숫자 글꼴 ow-num-bi.woff2]
모양은 앱 HUD 디자인(hud-base.css)과 같게: 육각 무늬 바탕, 왼쪽 위·오른쪽 아래를 깎은 칸, 주황 L자 꺾쇠
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

BG, PANEL, LINE = "#101318", "#151920", "#2a303a"  # 앱 hud-base.css의 --bg · --panel · --line
ORG, ORG2, TXT, MUTED = "#ff9c2a", "#ffb546", "#e8ebf0", "#8b93a3"  # --accent · 밝은 주황 · --text · --muted
NUM_FONT = None  # 숫자 글꼴 (Barlow Condensed Bold Italic, 앱 fonts/ow-num-bi.woff2) 경로: 5번째 인자

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


def num_face():
    with open(NUM_FONT, "rb") as f:
        b = base64.b64encode(f.read()).decode()
    return f"@font-face{{font-family:'N';src:url(data:font/woff2;base64,{b}) format('woff2');}}"


def svg(w, h, body, texts, size=None):
    """texts: {'H': 제목 글자, 'B': 굵은 글자, 'R': 본문 글자, 'N': 숫자(있으면 Barlow)}, size: 기본 표시 크기"""
    faces = "".join(font_face(fam, wt, texts[fam]) for fam, wt in (("H", 900), ("B", 700), ("R", 400)) if texts.get(fam))
    if texts.get("N") and NUM_FONT:
        faces += num_face()
    sw, sh = size or (w, h)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{sw}" height="{sh}">
<style>{faces}
.h{{font-family:'H';font-weight:900}} .n{{font-family:'N','H';font-weight:800;font-style:italic}} .b{{font-family:'B';font-weight:700}} .r{{font-family:'R';font-weight:400}}</style>
<defs>
<pattern id="hex" width="42" height="72" patternUnits="userSpaceOnUse"><path d="M21 2l18 10.5v21L21 44 3 33.5v-21z M21 44v26" fill="none" stroke="#ffffff" stroke-opacity=".05" stroke-width="1.2"/></pattern>
<linearGradient id="org" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{ORG2}"/><stop offset="1" stop-color="{ORG}"/></linearGradient>
<filter id="shadow" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="16" stdDeviation="16" flood-color="#000" flood-opacity=".55"/></filter>
</defs>
{body}
</svg>"""


def brackets(x, y, w, h, n=18, color=ORG):
    return (f'<path d="M{x} {y + n}V{y}H{x + n}" fill="none" stroke="{color}" stroke-width="3"/>'
            f'<path d="M{x + w - n} {y + h}H{x + w}V{y + h - n}" fill="none" stroke="{color}" stroke-width="3"/>')


def cut(w, h, c=24, x=0, y=0):
    """앱 --cut 모양: 왼쪽 위 · 오른쪽 아래 모서리를 깎은 칸"""
    return f"{x + c},{y} {x + w},{y} {x + w},{y + h - c} {x + w - c},{y + h} {x},{y + h} {x},{y + c}"


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
P2 = "공식 통계와 상성으로 영웅을 추천해요."
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
        stat_svg += f'<text x="{x}" y="558" class="n" font-size="58" fill="{ORG}">{n}</text>'
        stat_svg += f'<text x="{x + 10 + len(n) * 25}" y="553" class="r" font-size="24" fill="{MUTED}">{lab}</text>'
    body = f"""
<polygon points="{cut(W, H, 28)}" fill="{BG}"/>
<polygon points="{cut(W, H, 28)}" fill="url(#hex)"/>
<polygon points="{cut(W - 3, H - 3, 27, 1.5, 1.5)}" fill="none" stroke="{LINE}" stroke-width="3"/>
<clipPath id="c"><polygon points="{cut(W, H, 28)}"/></clipPath>
<g clip-path="url(#c)">
  <polygon points="810,0 {W},0 {W},{H} 610,{H}" fill="url(#org)"/>
  <polygon points="776,0 794,0 594,{H} 576,{H}" fill="{ORG}" fill-opacity=".35"/>
  <g transform="translate(612 478) rotate(-5)" filter="url(#shadow)">
    <rect x="-5" y="-5" width="{SW + 10}" height="{sh + 10}" fill="#0b0d11"/>
    <image href="data:image/jpeg;base64,{shot}" width="{SW}" height="{sh}"/>
    <rect x="-5" y="-5" width="{SW + 10}" height="{sh + 10}" fill="none" stroke="#ffffff" stroke-opacity=".14" stroke-width="2"/>
    {brackets(-13, -13, SW + 26, sh + 26, 26)}
  </g>
</g>
<path d="M14 44V14H44" fill="none" stroke="{ORG}" stroke-width="3"/>
<path d="M{W - 44} {H - 14}H{W - 14}V{H - 44}" fill="none" stroke="#1a1206" stroke-width="3"/>
<path d="M56 86H92" stroke="{ORG}" stroke-width="4"/>
<text x="106" y="95" class="b" font-size="25" letter-spacing="2" fill="{ORG}">{EYEBROW}</text>
{skewed(56, 214, "h", 104, TXT, L1)}
{skewed(56, 332, "h", 104, ORG, L2)}
<text x="58" y="404" class="r" font-size="30" fill="#c6cdd8">{P1}</text>
<text x="58" y="447" class="r" font-size="30" fill="#c6cdd8">{P2}</text>
{stat_svg}
"""
    texts = {"H": L1 + L2 + "".join(n for n, _ in STATS), "B": EYEBROW, "R": P1 + P2 + "".join(lab for _, lab in STATS), "N": "1"}
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
<polygon points="{cut(W - 3, H - 3, 16, 1.5, 1.5)}" fill="{PANEL}"/>
<polygon points="{cut(W - 3, H - 3, 16, 1.5, 1.5)}" fill="url(#hex)"/>
<polygon points="{cut(W - 3, H - 3, 16, 1.5, 1.5)}" fill="none" stroke="{LINE}" stroke-width="3"/>
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


# ---------- 장면 슬라이드 (match.gif의 장면을 옆으로 밀며 넘김) ----------
def slides(gif, hold=3.8, move=0.7):
    from PIL import ImageSequence
    frames = []
    for f in ImageSequence.Iterator(Image.open(gif)):
        buf = io.BytesIO()
        f.convert("RGB").quantize(256).save(buf, "PNG", optimize=True)
        frames.append(base64.b64encode(buf.getvalue()).decode())
    w, h = Image.open(gif).size
    n = len(frames)
    BAR = 64
    W, H = w, h + BAR
    T = n * hold
    # 장면 i를 보여 주다가 (i+1)*hold - move 부터 다음 장면으로 미끄러짐. 마지막엔 1장 복사본으로 넘어간 뒤 처음으로 순간 이동 → 끊김 없이 반복
    def keys(step):
        out = ["0%{transform:translateX(0)}"]
        for i in range(n):
            a = ((i + 1) * hold - move) / T * 100
            b = (i + 1) * hold / T * 100
            out.append(f"{a:.3f}%{{transform:translateX({-i * step}px);animation-timing-function:cubic-bezier(.65,0,.35,1)}}")
            out.append(f"{b:.3f}%{{transform:translateX({-(i + 1) * step}px)}}")
        return "".join(out)
    DOT, GAP = 14, 30
    dots_w = (n - 1) * GAP
    dx0 = W / 2 - dots_w / 2
    # 진행 점: 밝은 점이 다음 점으로 이동, 마지막엔 첫 점으로 돌아감
    dot_keys = ["0%{transform:translateX(0)}"]
    for i in range(n):
        a = ((i + 1) * hold - move) / T * 100
        b = (i + 1) * hold / T * 100
        nxt = (i + 1) % n
        dot_keys.append(f"{a:.3f}%{{transform:translateX({i * GAP}px);animation-timing-function:cubic-bezier(.65,0,.35,1)}}")
        dot_keys.append(f"{b:.3f}%{{transform:translateX({nxt * GAP}px)}}")
    images = "".join(f'<image href="data:image/png;base64,{d}" x="{i * w}" width="{w}" height="{h}"/>' for i, d in enumerate(frames))
    dots = "".join(f'<rect x="{dx0 + i * GAP - 5}" y="{h + BAR / 2 - 5}" width="10" height="10" fill="#3a414d"/>' for i in range(n))
    body = f"""
<style>
.track{{animation:slide {T}s infinite}} @keyframes slide{{{keys(w)}}}
.cur{{animation:dot {T}s infinite}} @keyframes dot{{{"".join(dot_keys)}}}
@media (prefers-reduced-motion: reduce){{.track,.cur{{animation:none}}}}
</style>
<polygon points="{cut(W, H, 24)}" fill="{BG}"/>
<polygon points="{cut(W, H, 24)}" fill="url(#hex)"/>
<clipPath id="frame"><polygon points="{cut(w, h, 24)}"/></clipPath>
<g clip-path="url(#frame)"><g class="track">{images}<image href="data:image/png;base64,{frames[0]}" x="{n * w}" width="{w}" height="{h}"/></g></g>
{dots}
<g class="cur"><rect x="{dx0 - 13}" y="{h + BAR / 2 - 6}" width="26" height="12" fill="{ORG}"/></g>
{brackets(1.5, 1.5, W - 3, H - 3, 34)}
"""
    write("slides.svg", svg(W, H, body, {}))


if len(sys.argv) > 5:
    NUM_FONT = sys.argv[5]
hero()
buttons()
features()
sections()
if len(sys.argv) > 4:
    slides(sys.argv[4])

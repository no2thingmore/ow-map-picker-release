"""README 사진 틀: 앱 HUD 디자인(hud-base.css)처럼 육각 무늬 바탕 + 왼쪽 위·오른쪽 아래를 깎은 칸 + 주황 L자 꺾쇠.

사진(png)이나 움짤(gif)을 받아 같은 틀을 씌운다. 움짤은 장면마다 같은 틀을 씌우고 장면 시간은 그대로 둔다.
사용: python frame.py <원본> <결과> [여백 px, 기본 24]
"""
import sys

from PIL import Image, ImageDraw, ImageSequence

BG = (16, 19, 24)          # --bg #101318
HEX = (29, 32, 37)         # 바탕 위 흰색 5% (README에선 작게 보여서 앱의 2.5%보다 조금 진하게)
LINE = (42, 48, 58)        # --line #2a303a
ORG = (255, 156, 42)       # --accent #ff9c2a


def hex_tile(draw, w, h):
    # 앱 바탕 무늬와 같은 칸(42×72): 육각형 하나 + 아래로 잇는 선
    for ty in range(-72, h + 72, 72):
        for tx in range(-42, w + 42, 42):
            pts = [(tx + 21, ty + 2), (tx + 39, ty + 12.5), (tx + 39, ty + 33.5), (tx + 21, ty + 44), (tx + 3, ty + 33.5), (tx + 3, ty + 12.5)]
            draw.line(pts + [pts[0]], fill=HEX, width=1)
            draw.line([(tx + 21, ty + 44), (tx + 21, ty + 70)], fill=HEX, width=1)


def cut_poly(x0, y0, x1, y1, c):
    return [(x0 + c, y0), (x1, y0), (x1, y1 - c), (x1 - c, y1), (x0, y1), (x0, y0 + c)]


def make_frame(w, h, pad):
    """사진 크기 w×h에 맞는 틀(RGBA)과 사진을 놓을 자리"""
    W, H = w + pad * 2, h + pad * 2
    c = max(10, pad // 2 + 6)  # 깎는 크기
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(cut_poly(0, 0, W - 1, H - 1, c), fill=255)
    bg = Image.new("RGBA", (W, H), BG + (255,))
    hex_tile(ImageDraw.Draw(bg), W, H)
    base.paste(bg, (0, 0), mask)
    d = ImageDraw.Draw(base)
    d.line(cut_poly(1, 1, W - 2, H - 2, c) + [(1 + c, 1)], fill=LINE, width=2)
    # 사진 테두리 (가는 선)
    d.rectangle((pad - 1, pad - 1, pad + w, pad + h), outline=LINE, width=1)
    # 꺾쇠: 사진 모서리 바깥쪽에 L자 (왼쪽 위 · 오른쪽 아래)
    n, t, o = max(18, pad + 6), 3, max(6, pad // 3)
    x0, y0, x1, y1 = pad - o, pad - o, pad + w + o, pad + h + o
    d.line([(x0, y0 + n), (x0, y0), (x0 + n, y0)], fill=ORG, width=t, joint="curve")
    d.line([(x1 - n, y1), (x1, y1), (x1, y1 - n)], fill=ORG, width=t, joint="curve")
    return base, (pad, pad)


def frame_image(im, pad):
    fr, at = make_frame(im.width, im.height, pad)
    out = fr.copy()
    out.paste(im.convert("RGB"), at)
    # README가 흰 바탕(라이트 모드)이어도 깎인 모서리 밖이 투명하게 보이도록 RGBA 그대로
    return out


def main(src, dst, pad=24):
    im = Image.open(src)
    if getattr(im, "n_frames", 1) > 1:
        frames, durs = [], []
        for f in ImageSequence.Iterator(im):
            durs.append(f.info.get("duration", 1000))
            # 움짤은 투명을 못 쓰므로(색 수 제한) 바탕색으로 채움
            fr = frame_image(f.convert("RGB"), pad)
            flat = Image.new("RGB", fr.size, BG)
            flat.paste(fr, (0, 0), fr)
            frames.append(flat.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
        frames[0].save(dst, save_all=True, append_images=frames[1:], duration=durs, loop=0, optimize=True, disposal=1)
    else:
        out = frame_image(im, pad)
        out.save(dst, optimize=True)
    print(dst, Image.open(dst).size)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 24)

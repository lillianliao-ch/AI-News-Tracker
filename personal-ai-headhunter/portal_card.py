#!/usr/bin/env python3
"""
VIP 服务通道名片卡生成器
用 Pillow 动态合成候选人专属名片卡（深色科技感设计）
"""

import os
import io
import base64
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# 卡片尺寸
CARD_W, CARD_H = 750, 420

# 颜色
BG_DARK = (15, 18, 35)       # 深蓝背景
BG_MID = (25, 30, 60)        # 中间层
GOLD = (212, 175, 85)        # 金色
GOLD_DIM = (160, 130, 65)    # 暗金色
WHITE = (255, 255, 255)
WHITE_DIM = (180, 185, 200)  # 浅灰白
BORDER_GOLD = (180, 150, 70, 180)  # 半透明金色边框

# 字体路径（macOS 自带中文字体）
FONT_PATHS = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]

def _get_font(size, bold=False):
    """获取可用的中文字体"""
    for fp in FONT_PATHS:
        if os.path.exists(fp):
            try:
                # PingFang.ttc has multiple faces; index 0 = Regular, index 1+ = others
                if fp.endswith('.ttc'):
                    return ImageFont.truetype(fp, size, index=0)
                return ImageFont.truetype(fp, size)
            except:
                continue
    return ImageFont.load_default()


def _draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """绘制圆角矩形"""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def generate_portal_card(candidate_name: str, portal_code: str, 
                          portal_base: str = "https://jobs.rupro-consulting.com") -> bytes:
    """
    生成候选人专属 VIP 服务通道名片卡。
    
    Args:
        candidate_name: 候选人姓名
        portal_code: 门户短码（随机12位）
        portal_base: 门户基础 URL
    
    Returns:
        PNG 图片的 bytes
    """
    portal_url = f"{portal_base}/p/{portal_code}"
    
    # === 1. 创建渐变背景 ===
    img = Image.new('RGB', (CARD_W, CARD_H), BG_DARK)
    draw = ImageDraw.Draw(img)
    
    # 渐变效果（从左上深色到右下稍亮）
    for y in range(CARD_H):
        for x in range(CARD_W):
            # 径向渐变
            dx = (x - CARD_W * 0.7) / CARD_W
            dy = (y - CARD_H * 0.3) / CARD_H
            dist = (dx*dx + dy*dy) ** 0.5
            factor = max(0, min(1, 1.0 - dist * 1.2))
            r = int(BG_DARK[0] + (BG_MID[0] - BG_DARK[0]) * factor)
            g = int(BG_DARK[1] + (BG_MID[1] - BG_DARK[1]) * factor)
            b = int(BG_DARK[2] + (BG_MID[2] - BG_DARK[2]) * factor)
            img.putpixel((x, y), (r, g, b))
    
    draw = ImageDraw.Draw(img)
    
    # === 2. 金色边框 ===
    _draw_rounded_rect(draw, (8, 8, CARD_W-8, CARD_H-8), radius=18, 
                        outline=GOLD_DIM, width=2)
    
    # === 3. 装饰线条（科技感） ===
    # 右上角装饰线
    for i in range(3):
        offset = i * 12
        draw.line([(CARD_W - 120 + offset, 20), (CARD_W - 20, 20 + offset * 3)], 
                  fill=(*GOLD_DIM, 60), width=1)
    # 左下角装饰线
    for i in range(3):
        offset = i * 12
        draw.line([(20, CARD_H - 80 + offset), (100 + offset * 2, CARD_H - 20)], 
                  fill=(*GOLD_DIM, 60), width=1)
    
    # === 4. Logo 文字 ===
    font_logo = _get_font(16)
    draw.text((30, 25), "RuPro Consulting · AI猎头", fill=GOLD_DIM, font=font_logo)
    
    # === 5. 生成并粘贴二维码 ===
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M,
                        box_size=6, border=2)
    qr.add_data(portal_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="white", back_color=(40, 45, 75)).convert('RGB')
    
    # 二维码区域（带磨砂背景）
    qr_size = 170
    qr_x, qr_y = 40, 75
    
    # 磨砂背景
    _draw_rounded_rect(draw, (qr_x - 10, qr_y - 10, qr_x + qr_size + 10, qr_y + qr_size + 10), 
                        radius=12, fill=(40, 45, 75))
    _draw_rounded_rect(draw, (qr_x - 10, qr_y - 10, qr_x + qr_size + 10, qr_y + qr_size + 10), 
                        radius=12, outline=(80, 85, 115), width=1)
    
    qr_resized = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
    img.paste(qr_resized, (qr_x, qr_y))
    
    # 二维码下方提示
    font_tiny = _get_font(13)
    draw.text((qr_x + 45, qr_y + qr_size + 15), "扫码进入", fill=WHITE_DIM, font=font_tiny)
    
    # === 6. 右侧文字 ===
    text_x = 260
    
    # 主标题 "Hi 候选人名"
    font_name = _get_font(38)
    font_greeting = _get_font(20)
    draw.text((text_x, 80), f"Hi {candidate_name}", fill=WHITE, font=font_name)
    
    # 副标题 "这是您的VIP服务通道"
    font_sub = _get_font(24)
    draw.text((text_x, 135), "这是您的VIP服务通道", fill=GOLD, font=font_sub)
    
    # 描述文字
    font_desc = _get_font(16)
    draw.text((text_x, 180), "扫码查看为您精选的AI领域机会", fill=WHITE_DIM, font=font_desc)
    draw.text((text_x, 205), "新职位推荐将实时更新", fill=WHITE_DIM, font=font_desc)
    
    # === 7. 底部分隔线 + URL ===
    line_y = CARD_H - 80
    draw.line([(30, line_y), (CARD_W - 30, line_y)], fill=GOLD_DIM, width=1)
    
    # URL
    font_url = _get_font(14)
    draw.text((30, line_y + 15), portal_url, fill=WHITE_DIM, font=font_url)
    
    # 右下角提示
    draw.text((CARD_W - 230, line_y + 15), "长按保存 · 随时查看最新推荐", fill=GOLD_DIM, font=font_url)
    
    # === 8. 输出 PNG ===
    buf = io.BytesIO()
    img.save(buf, format='PNG', quality=95)
    return buf.getvalue()


def generate_portal_card_base64(candidate_name: str, portal_code: str,
                                 portal_base: str = "https://jobs.rupro-consulting.com") -> str:
    """生成名片卡并返回 base64 编码（供 Streamlit 内联显示）"""
    png_bytes = generate_portal_card(candidate_name, portal_code, portal_base)
    return base64.b64encode(png_bytes).decode()


if __name__ == "__main__":
    # 测试生成
    card_bytes = generate_portal_card("王海", "a3f8c2e19b47")
    with open("/tmp/test_portal_card.png", "wb") as f:
        f.write(card_bytes)
    print(f"✅ 测试名片卡已生成: /tmp/test_portal_card.png ({len(card_bytes)} bytes)")

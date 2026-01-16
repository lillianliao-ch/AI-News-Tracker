#!/usr/bin/env python3
"""
生成 Chrome 插件图标
"""

from PIL import Image, ImageDraw, ImageFont

def create_icon(size, output_path):
    """
    创建简单的图标
    
    Args:
        size: 图标尺寸
        output_path: 输出路径
    """
    # 创建图像（渐变紫色背景）
    img = Image.new('RGBA', (size, size), (102, 126, 234, 255))  # #667eea
    draw = ImageDraw.Draw(img)
    
    # 绘制白色圆角矩形边框
    border_width = max(2, size // 16)
    draw.rectangle(
        [border_width, border_width, size - border_width, size - border_width],
        outline=(255, 255, 255, 255),
        width=border_width
    )
    
    # 添加文字 "AI"
    try:
        # 尝试使用系统字体
        font_size = size // 2
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        # 如果找不到字体，使用默认字体
        font = ImageFont.load_default()
    
    text = "AI"
    
    # 计算文字位置（居中）
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - bbox[1]
    
    # 绘制文字
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    # 保存
    img.save(output_path, 'PNG')
    print(f"✅ 生成图标: {output_path} ({size}x{size})")

if __name__ == "__main__":
    import os
    
    # 创建图标目录
    icons_dir = "icons"
    os.makedirs(icons_dir, exist_ok=True)
    
    # 生成不同尺寸的图标
    sizes = [16, 48, 128]
    for size in sizes:
        output_path = f"{icons_dir}/icon{size}.png"
        create_icon(size, output_path)
    
    print("\n✅ 所有图标生成完成！")


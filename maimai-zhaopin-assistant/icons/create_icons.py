#!/usr/bin/env python3
"""
创建脉脉招聘助手图标文件
这个脚本创建简单的蓝色图标用于Chrome扩展
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_icon(size, output_path):
    """创建指定尺寸的图标"""
    # 创建蓝色背景
    img = Image.new('RGBA', (size, size), (24, 144, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 添加白色圆角矩形
    margin = size // 8
    rect_coords = [margin, margin, size - margin, size - margin]
    draw.rounded_rectangle(rect_coords, radius=size//16, fill=(255, 255, 255, 255))
    
    # 添加蓝色"脉"字简化图形
    center = size // 2
    
    # 绘制简化的"M"字母代表"脉脉"
    line_width = max(2, size // 16)
    
    # M字的左竖线
    draw.line([(center - size//4, center - size//6), (center - size//4, center + size//6)], 
              fill=(24, 144, 255, 255), width=line_width)
    
    # M字的右竖线
    draw.line([(center + size//4, center - size//6), (center + size//4, center + size//6)], 
              fill=(24, 144, 255, 255), width=line_width)
    
    # M字的中间连接
    draw.line([(center - size//4, center - size//6), (center, center)], 
              fill=(24, 144, 255, 255), width=line_width)
    draw.line([(center, center), (center + size//4, center - size//6)], 
              fill=(24, 144, 255, 255), width=line_width)
    
    # 保存图标
    img.save(output_path, 'PNG')
    print(f"Created icon: {output_path}")

def main():
    """主函数"""
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 创建不同尺寸的图标
    sizes = [16, 48, 128]
    
    for size in sizes:
        output_path = os.path.join(script_dir, f'icon{size}.png')
        create_icon(size, output_path)
    
    print("所有图标创建完成!")

if __name__ == "__main__":
    main()
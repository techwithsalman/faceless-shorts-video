import os
import math
from PIL import Image, ImageDraw, ImageFilter

def create_prompt2video_icon():
    os.makedirs("assets", exist_ok=True)
    size = 512
    # Create high-resolution image with alpha
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Background rounded squircle
    margin = 24
    radius = 110
    # Base dark gradient
    for y in range(margin, size - margin):
        t = (y - margin) / (size - 2 * margin)
        r = int(10 * (1 - t) + 20 * t)
        g = int(12 * (1 - t) + 26 * t)
        b = int(18 * (1 - t) + 40 * t)
        draw.line([(margin, y), (size - margin, y)], fill=(r, g, b, 255))

    # Mask to rounded rectangle
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=radius, fill=255)

    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    base.paste(img, (0, 0), mask=mask)

    # 2. Glowing cyan border
    border_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(border_img)
    bdraw.rounded_rectangle([margin + 2, margin + 2, size - margin - 2, size - margin - 2], radius=radius, outline=(0, 229, 255, 180), width=6)
    
    # 3. Outer subtle glow
    glow_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow_img)
    gdraw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=radius, outline=(0, 229, 255, 120), width=12)
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(10))

    final = Image.alpha_composite(glow_img, base)
    final = Image.alpha_composite(final, border_img)

    # 4. Central Motif: Stylized Futuristic Play Triangle with AI Spark
    emblem = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    edraw = ImageDraw.Draw(emblem)

    # Triangle coordinates (centered)
    # Center is (256, 256)
    cx, cy = 256, 256
    # Points for large play triangle
    p1 = (cx - 70, cy - 110) # top left
    p2 = (cx - 70, cy + 110) # bottom left
    p3 = (cx + 110, cy)      # right tip

    # Draw glow behind triangle
    t_glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    tg_draw = ImageDraw.Draw(t_glow)
    tg_draw.polygon([p1, p2, p3], fill=(0, 229, 255, 140))
    t_glow = t_glow.filter(ImageFilter.GaussianBlur(16))
    final = Image.alpha_composite(final, t_glow)

    # Draw gradient or styled polygon
    # Left segment: Electric Cyan
    edraw.polygon([p1, p2, (cx + 10, cy + 30), (cx + 10, cy - 30)], fill=(0, 210, 240, 255))
    # Right tip segment: Bright Cyan / White highlight
    edraw.polygon([(cx + 10, cy - 30), (cx + 10, cy + 30), p3], fill=(165, 243, 252, 255))
    # Stylized cut / angle
    edraw.line([p1, p3], fill=(255, 255, 255, 220), width=4)
    edraw.line([p2, p3], fill=(0, 180, 220, 200), width=4)
    edraw.line([p1, p2], fill=(0, 229, 255, 240), width=4)

    # Neural AI Nodes & Accent Spark
    # Center node
    node_color = (245, 158, 11, 255) # Vivid Amber
    edraw.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=node_color, outline=(255, 255, 255, 255), width=3)
    # Small satellite nodes
    edraw.ellipse([cx - 50, cy - 70, cx - 36, cy - 56], fill=(0, 229, 255, 255), outline=(255, 255, 255, 220), width=2)
    edraw.ellipse([cx - 50, cy + 56, cx - 36, cy + 70], fill=(0, 229, 255, 255), outline=(255, 255, 255, 220), width=2)
    edraw.ellipse([cx + 60, cy - 8, cx + 76, cy + 8], fill=(0, 229, 255, 255), outline=(255, 255, 255, 220), width=2)

    # Interconnecting lines
    edraw.line([(cx - 43, cy - 63), (cx, cy)], fill=(255, 255, 255, 180), width=2)
    edraw.line([(cx - 43, cy + 63), (cx, cy)], fill=(255, 255, 255, 180), width=2)
    edraw.line([(cx + 68, cy), (cx, cy)], fill=(255, 255, 255, 180), width=2)

    final = Image.alpha_composite(final, emblem)

    # Save PNG (512x512)
    png_path = os.path.join("assets", "icon.png")
    final.save(png_path, "PNG")
    print(f"Saved PNG icon to {png_path} ({final.size})")

    # Save multi-resolution ICO for Windows installer & taskbar
    ico_path = os.path.join("assets", "icon.ico")
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    final.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"Saved ICO icon to {ico_path} with sizes {icon_sizes}")

if __name__ == "__main__":
    create_prompt2video_icon()

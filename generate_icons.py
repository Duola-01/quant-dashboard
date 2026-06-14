"""生成 PWA 图标 — 192x192 和 512x512 纯色方块 + 文字"""
import struct, zlib, os

def create_png(width, height, r, g, b, label=""):
    """创建纯色 PNG，带简单文字标记"""
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))

    raw = b""
    for y in range(height):
        raw += b"\x00"
        for x in range(width):
            # 简单的中心十字图案（深色线条）
            cx, cy = width // 2, height // 2
            if abs(x - cx) < width // 8 and abs(y - cy) < height // 3:
                raw += bytes([min(r + 50, 255), min(g + 50, 255), min(b + 50, 255)])
            elif abs(y - cy) < height // 8 and abs(x - cx) < width // 3:
                raw += bytes([min(r + 50, 255), min(g + 50, 255), min(b + 50, 255)])
            else:
                raw += bytes([r, g, b])

    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return header + ihdr + idat + iend

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

# 深蓝灰底色 (Streamlit 风格)
r, g, b = 14, 17, 23

for size in [192, 512]:
    png_data = create_png(size, size, r, g, b)
    path = os.path.join(static_dir, f"icon-{size}.png")
    with open(path, "wb") as f:
        f.write(png_data)
    print(f"Created {path} ({size}x{size})")

print("Icons generated.")

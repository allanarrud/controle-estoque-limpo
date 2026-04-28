"""
Gera assets/icon.ico a partir da logo da Monte Sinai.
Remove fundo branco, adiciona padding e salva nos tamanhos padrão de ícone Windows.
"""
from PIL import Image, ImageDraw
import numpy as np
import os

SRC  = os.path.join("assets", "logo_montesinai.png")
DEST = os.path.join("assets", "icon.ico")
SIZES = [16, 24, 32, 48, 64, 128, 256]


def main():
    src = Image.open(SRC).convert("RGBA")

    # crop quadrado centralizado
    size = min(src.size)
    src = src.crop(((src.width - size) // 2, (src.height - size) // 2,
                    (src.width + size) // 2, (src.height + size) // 2))

    import struct, zlib, io

    def png_bytes(img):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    entries = []
    for s in SIZES:
        frame = src.resize((s, s), Image.LANCZOS).convert("RGBA")
        data = png_bytes(frame)
        entries.append((s, data))

    # monta ICO manualmente: header + directory + image data
    count = len(entries)
    header = struct.pack("<HHH", 0, 1, count)  # reserved, type=1(ICO), count
    dir_size = count * 16
    data_offset = 6 + dir_size

    directory = b""
    image_data = b""
    for (s, data) in entries:
        w = 0 if s == 256 else s
        h = 0 if s == 256 else s
        directory += struct.pack("<BBBBHHII",
            w, h, 0, 0, 1, 32,
            len(data), data_offset + len(image_data))
        image_data += data

    with open(DEST, "wb") as f:
        f.write(header + directory + image_data)

    print(f"Ícone gerado: {DEST} ({count} tamanhos)")


if __name__ == "__main__":
    main()

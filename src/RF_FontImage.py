"""
    RF_FontImage.py
    Generate TGA bitmap font textures and base FNT data file for RTCW from TrueTypeFont file.
"""


from typing import Tuple, List, Dict, Optional, NoReturn
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from RF_Set import *


class FontImage:
    def __init__(self, ttf_path: str, font_size: int, output_dir: str = "", max_glyphs: int = GLYPHS_PER_FONT):
        self.ttf_glyphs: List[TTFGlyph] = []
        self.textures: List[Texture] = []
        self.glyphs: List[Glyph] = []

        self.font: Optional[TTFont] = None
        self.chars: List[str] = []
        self.available_chars: List[str] = []

        self.ttf_path: str = ttf_path
        self.font_size: int = font_size
        self.output_dir: str = output_dir
        self.max_glyphs: int = max_glyphs

        self._startup()

    def _startup(self) -> NoReturn:
        if self.output_dir and not self.output_dir.isspace():
            os.makedirs(self.output_dir, exist_ok=True)

        # path is not specified, user may want to call the read data function manually later
        if not self.ttf_path or self.ttf_path.isspace():
            return
        else:
            self._load_font()

    def _load_font(self) -> NoReturn:
        try_path = self.ttf_path.replace('/', '\\')
        if not os.path.exists(try_path):
            print(f"\"{try_path}\" not exist, ", end='')
            try_path = SYS_FONTS_DIR.replace('/', '\\') + "\\" + try_path.split('\\')[-1]
            print(f"try \"{try_path}\"...")
        if not os.path.exists(try_path):
            raise FileNotFoundError(f"[Error] couldn't open \"{self.ttf_path}\"")

        if try_path.lower().endswith(".ttf"):
            self.font = TTFont(try_path)
        elif try_path.lower().endswith(".ttc"):
            self.font = TTFont(try_path, fontNumber=0)

        print(f"Checking available characters in {try_path}...")
        self.available_chars = self._get_available_characters()
        self.chars = self.available_chars
        print(f"Font contains {len(self.available_chars)} available characters")

    def _get_available_characters(self) -> List[str]:
        available_chars = set()
        available_chars.update([chr(i) for i in range(256)])

        # check cmap table
        for table in self.font['cmap'].tables:
            if table.format == 4:  # the mostly used format
                for code in table.cmap.keys():
                    if 0 <= code <= self.max_glyphs:  # Unicode range
                        available_chars.add(chr(code))

        return sorted(list(available_chars))

    def is_character_supported(self, char: str) -> bool:
        return char in self.available_chars

    def render_glyphs(self, margin: int = 4) -> NoReturn:
        if not self.font:
            self._load_font()

        font_pil = ImageFont.truetype(self.ttf_path, self.font_size)
        self.ttf_glyphs = []
        missing_count = 0

        for i, char in enumerate(self.chars):
            if i % 100 == 0:
                print(f"\rRendering {i}/{len(self.chars)} characters...", end='', flush=True)
            elif i == len(self.chars) - 1:
                print(f"\rRendering {len(self.chars)}/{len(self.chars)} characters...", flush=True)

            try:
                is_reserved_char = ord(char) < 256    # reserve 256 base ascii characters
                if not self.is_character_supported(char) and not is_reserved_char:
                    missing_count += 1
                    continue

                bbox = font_pil.getbbox(char)
                if not bbox:
                    if is_reserved_char:
                        bbox = font_pil.getbbox(' ')
                    else:
                        missing_count += 1
                        continue

                # check if bbox is valid
                # if bbox[2] - bbox[0] <= 0 or bbox[3] - bbox[1] <= 0:
                #     missing_count += 1
                #     continue

                ttf_glyph = TTFGlyph()
                ttf_glyph.char_index = i
                ttf_glyph.char = char
                ttf_glyph.width = int(bbox[2] - bbox[0] + margin * 2)
                ttf_glyph.height = int(bbox[3] - bbox[1] + margin * 2)
                ttf_glyph.margin = margin
                ttf_glyph.bbox = bbox

                metrics = font_pil.getmetrics()
                ttf_glyph.ascent, ttf_glyph.descent = metrics

                ttf_glyph.image = Image.new("RGBA", (ttf_glyph.width, ttf_glyph.height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(ttf_glyph.image)

                x_offset = margin - bbox[0]
                y_offset = margin - bbox[1]

                draw.text((x_offset, y_offset), char, font=font_pil, fill=(255, 255, 255, 255))

                self.ttf_glyphs.append(ttf_glyph)

            except Exception as e:
                print(f"[Warning] failed to render character '{char}' (U+{ord(char):04X}): {e}")
                missing_count += 1
                continue

        if missing_count > 0:
            print(f"{missing_count} characters are not rendered, they may unsupported in the selected TrueType file")

        print(f"Successfully rendered {len(self.ttf_glyphs)} characters!")

    def pack_textures(self, texture_width: int = 1024, texture_height: int = 1024,
                      char_spacing: int = 2, texture_margin: int = 16) -> NoReturn:
        self.textures = []

        current_x = texture_margin
        current_y = texture_margin
        max_row_height = 0
        texture_index = 0

        current_texture = Texture()
        current_texture.texture_index = texture_index
        current_texture.width = texture_width
        current_texture.height = texture_height

        # Sort by height, but this will disrupt the order of the characters
        # ttf_glyphs = sorted(self.ttf_glyphs, key=lambda g: g.height, reverse=True)
        ttf_glyphs = self.ttf_glyphs

        for i, ttf_glyph in enumerate(ttf_glyphs):
            # if need autowrap
            if current_x + ttf_glyph.width > texture_width - texture_margin:
                current_x = texture_margin
                current_y += max_row_height + char_spacing
                max_row_height = 0

            # if need to create an new texture file
            if current_y + ttf_glyph.height > texture_height - texture_margin:
                self.textures.append(current_texture)

                texture_index += 1
                current_texture = Texture()
                current_texture.texture_index = texture_index
                current_texture.width = texture_width
                current_texture.height = texture_height

                current_x = texture_margin
                current_y = texture_margin
                max_row_height = 0

            ttf_glyph.x = current_x
            ttf_glyph.y = current_y
            ttf_glyph.texture_index = texture_index

            # add to current texture
            current_texture.ttf_glyphs.append(ttf_glyph)

            # update position data
            current_x += ttf_glyph.width + char_spacing
            max_row_height = max(max_row_height, ttf_glyph.height)

        # the last one
        if current_texture.ttf_glyphs:
            self.textures.append(current_texture)

        print(f"Created {len(self.textures)} texture pages")

    def generate_glyphs_data(self, texture_name_base: str) -> NoReturn:
        self.glyphs = []

        for texture in self.textures:
            for ttf_glyph in texture.ttf_glyphs:
                glyph = Glyph()
                glyph.id = ord(ttf_glyph.char)
                glyph.height = ttf_glyph.height
                glyph.top = ttf_glyph.ascent + ttf_glyph.margin - ttf_glyph.bbox[1]
                glyph.bottom = glyph.top - ttf_glyph.height
                glyph.pitch = ttf_glyph.width
                glyph.xSkip = ttf_glyph.width - ttf_glyph.margin * 2 + 2
                glyph.imageWidth = ttf_glyph.width
                glyph.imageHeight = ttf_glyph.height

                glyph.s = ttf_glyph.x / texture.width
                glyph.t = ttf_glyph.y / texture.height
                glyph.s2 = (ttf_glyph.x + ttf_glyph.width) / texture.width
                glyph.t2 = (ttf_glyph.y + ttf_glyph.height) / texture.height

                glyph.glyph = 0
                glyph.shaderName = f"fonts/{texture_name_base}_{texture.texture_index:d}.tga"

                self.glyphs.append(glyph)

    def save_textures(self, texture_name_base: str) -> NoReturn:
        for texture in self.textures:
            atlas = Image.new("RGBA", (texture.width, texture.height), (0, 0, 0, 0))

            for ttf_glyph in texture.ttf_glyphs:
                if ttf_glyph.image:
                    atlas.paste(ttf_glyph.image, (ttf_glyph.x, ttf_glyph.y))

            # save to TGA
            texture_name = f"{texture_name_base}_{texture.texture_index:d}"
            tga_path = os.path.join(self.output_dir, f"{texture_name}.tga")
            self._save_tga_for_rtcw(atlas, tga_path)

            print(f"Saved texture: {texture_name}.tga ({texture.width}x{texture.height})")

    def _save_tga_for_rtcw(self, image: Image, filepath: str) -> NoReturn:
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        width, height = image.size

        # TGA header
        header = bytearray(18)
        header[2] = 2
        header[12] = width & 0xFF
        header[13] = (width >> 8) & 0xFF
        header[14] = height & 0xFF
        header[15] = (height >> 8) & 0xFF
        header[16] = 32  # depth bits

        # compatible format for RTCW
        header[17] = 0x00
        data = np.array(image)
        flipped_data = np.flipud(data)

        bgra_data = np.zeros((height, width, 4), dtype=np.uint8)
        bgra_data[..., 0] = flipped_data[..., 2]  # B
        bgra_data[..., 1] = flipped_data[..., 1]  # G
        bgra_data[..., 2] = flipped_data[..., 0]  # R
        bgra_data[..., 3] = flipped_data[..., 3]  # A

        with open(filepath, 'wb') as f:
            f.write(header)
            f.write(bgra_data.tobytes())

    def save_fnt_file(self, filepath: str, texture_name_base: str) -> NoReturn:
        special_chars: Dict[int, str] = {10: "(LF)", 13: "(CR)"}

        with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
            # some information about generated font
            f.write(f"// RTCW Font File\n")
            f.write(f"// Generated from: {os.path.basename(self.ttf_path)}\n")
            f.write(f"// Font size: {self.font_size}\n")
            f.write(f"// Total characters: {len(self.glyphs)}\n")
            f.write(f"// Texture base name: {texture_name_base}\n\n")

            sorted_glyphs = sorted(self.glyphs, key=lambda g: g.id)
            f.write("// glyphs\n{\n")
            for glyph in sorted_glyphs:
                if glyph.id in special_chars:
                    f.write(f"\t// Character: '{special_chars[glyph.id]}' (U+{glyph.id:04X})\n")
                else:
                    f.write(f"\t// Character: '{chr(glyph.id)}' (U+{glyph.id:04X})\n")
                f.write(f"\tchar {glyph.id}\n")
                f.write("\t{\n")
                f.write(f"\t\theight {glyph.height}\n")
                f.write(f"\t\ttop {glyph.top}\n")
                f.write(f"\t\tbottom {glyph.bottom}\n")
                f.write(f"\t\tpitch {glyph.pitch}\n")
                f.write(f"\t\txSkip {glyph.xSkip}\n")
                f.write(f"\t\timageWidth {glyph.imageWidth}\n")
                f.write(f"\t\timageHeight {glyph.imageHeight}\n")
                f.write(f"\t\ts {glyph.s:.6f}\n")
                f.write(f"\t\tt {glyph.t:.6f}\n")
                f.write(f"\t\ts2 {glyph.s2:.6f}\n")
                f.write(f"\t\tt2 {glyph.t2:.6f}\n")
                f.write("\t\tglyph 0\n")
                f.write(f'\t\tshaderName "{glyph.shaderName}"\n')
                f.write("\t}\n\n")
            f.write("}\n\n")

            f.write("// fontinfo\n{\n")
            f.write(f"\tglyphScale {1.0:.6f}\n")
            f.write(f"\tname \"{texture_name_base}\"\n")
            f.write("}\n")

    def generate(self, output_name: str, texture_width: int = 1024, texture_height: int = 1024,
                 char_margin: int = 2, char_spacing: int = 2, texture_margin: int = 8) -> NoReturn:
        self.render_glyphs(margin=char_margin)
        self.pack_textures(texture_width, texture_height, char_spacing, texture_margin)
        self.generate_glyphs_data(output_name)
        self.save_textures(output_name)

        # generate .fnt data file
        fnt_path = os.path.join(self.output_dir, f"{output_name}.fnt")
        self.save_fnt_file(fnt_path, output_name)

        print(f"Generation completed! Created {len(self.textures)} TGA files and 1 FNT file")


# example
if __name__ == "__main__":
    # the meaning of font_size is not quite the same as in rtcw
    generator = FontImage("./ttffont/simhei.ttf", 36, "./test")
    generator.generate("fontImage_36", texture_width=1024, texture_height=1024)


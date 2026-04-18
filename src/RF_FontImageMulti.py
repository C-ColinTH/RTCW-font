"""
    RF_FontImageMulti.py
    Generate TGA bitmap font textures and base FNT data file for RTCW from multiple TrueTypeFont files.
"""

from typing import Tuple, List, Set, Dict, Optional, Union, NoReturn
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import table__c_m_a_p

from RF_Set import *


class FontImageMulti:
    def __init__(self, corresponding_table: List[List[Union[str, List[Tuple[int, int]]]]],
                    output_dir: str = "", max_glyphs: int = GLYPHS_PER_FONT):
        self.ttf_glyphs: List[TTFGlyph] = []
        self.textures: List[Texture] = []
        self.glyphs: List[Glyph] = []

        self.font_size: int = 0
        self.output_dir: str = output_dir
        self.max_glyphs: int = max_glyphs
        self.corresponding_table: List = corresponding_table

        # ttf path, TTFont, available chars, selected chars set
        self.multi_table: List[MultiTable] = []

        self._startup()

    def _startup(self) -> None:
        if self.output_dir and not self.output_dir.isspace():
            os.makedirs(self.output_dir, exist_ok=True)

        self._set_multi_table()

    def _set_multi_table(self) -> None:
        cor_table = self.corresponding_table
        if cor_table is None:
            return

        for ctable in cor_table:
            filepath: str = ctable[0]
            char_ranges: List[Tuple[int, int]] = ctable[1]

            mtable = MultiTable()
            mtable.ttf_path = filepath
            mtable.ttfont = self._load_font(filepath)
            if mtable.ttfont is None:
                continue
            mtable.available_chars = self._get_available_characters(mtable.ttfont)
            mtable.selected_chars = self._set_char_sets(char_ranges)

            self.multi_table.append(mtable)

    def _load_font(self, ttf_path: str) -> Optional[TTFont]:
        try_path = ttf_path.replace('/', '\\')
        ttfont = None

        if not os.path.exists(try_path):
            print(f"\"{try_path}\" not exist, ", end='')
            try_path = SYS_FONTS_DIR.replace('/', '\\') + "\\" + try_path.split('\\')[-1]
            print(f"try \"{try_path}\"...")
        if not os.path.exists(try_path):
            raise FileNotFoundError(f"[Error] couldn't open \"{try_path}\"")

        if try_path.lower().endswith(".ttf"):
            ttfont = TTFont(try_path)
        elif try_path.lower().endswith(".ttc"):
            ttfont = TTFont(try_path, fontNumber=0)

        if ttfont is None:
            print(f"[Error] coulnd't load font data from \"{try_path}\"")

        return ttfont

    def _get_available_characters(self, ttfont: TTFont) -> List[str]:
        available_chars = set()
        available_chars.update([chr(i) for i in range(256)])

        if not ttfont:
            raise AttributeError("Could not find cmap table")

        try:
            cmap_table = ttfont['cmap'].tables
            for table in cmap_table:
                if table.format == 4:  # the mostly used format
                    for codepoint in table.cmap.keys():
                        if 0 <= codepoint <= self.max_glyphs:  # Unicode range
                            available_chars.add(chr(codepoint))
        except:
            best_table = ttfont.getBestCmap()
            if best_table:
                for codepoint in best_table.keys():
                    if 0 <= codepoint <= self.max_glyphs:
                        available_chars.add(chr(codepoint))

        # need to be ordered, so return a list type
        return sorted(list(available_chars))

    def _set_char_sets(self, char_ranges: List[Tuple[int, int]]) -> Set[int]:
        selected_chars = set()
        for r in char_ranges:
            for i in range(r[0], r[-1] + 1):
                # [r[0], r[-1]], including the right boundary value
                selected_chars.add(i)

        return selected_chars

    def is_character_supported(self, char: str, available_chars: List[str]) -> bool:
        return char in available_chars

    def is_character_selected(self, char: str, selected_chars: Set[int]) -> bool:
        unicode = ord(char[0])
        return unicode in selected_chars

    def render_glyphs(self, margin: int, developer_mode: bool) -> None:
        self.ttf_glyphs = []

        # prevent multiple same codepoint font structure
        # Note: if there are multiple same codepoint font structure, the latter will overwrite the former
        ttf_glyphs_dict: Dict[int, TTFGlyph] = {}

        n = 0
        for mtable in self.multi_table:
            ttf_basename = os.path.basename(mtable.ttf_path)
            available_chars = mtable.available_chars
            selected_chars = mtable.selected_chars

            font_pil = ImageFont.truetype(mtable.ttf_path, self.font_size)

            missing_count = 0
            num = len(available_chars)
            print(f"rendering glyphs from \"{ttf_basename}\"")
            for i, char in enumerate(available_chars):
                if i % 100 == 0:
                    print(f"\rProgress {i}/{num} ...", end='', flush=True)
                elif i == num - 1:
                    print(f"\rProgress {num}/{num} ...", flush=True)

                try:
                    is_reserved_char = ord(char) < 256 and n == 0   # reserve 256 base ascii characters
                    if not is_reserved_char:
                        if len(selected_chars) > 0 and not self.is_character_selected(char, selected_chars):
                            continue
                        if not self.is_character_supported(char, available_chars):
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
                    if bbox[2] - bbox[0] <= 0 and bbox[3] - bbox[1] <= 0:
                        continue

                    ttf_glyph = TTFGlyph()
                    ttf_glyph.char_index = i
                    ttf_glyph.char = char
                    ttf_glyph.unicode = ord(char[0])
                    ttf_glyph.width = int(bbox[2] - bbox[0])
                    ttf_glyph.height = int(bbox[3] - bbox[1])
                    ttf_glyph.margin = margin
                    ttf_glyph.bbox = bbox

                    metrics = font_pil.getmetrics()
                    ttf_glyph.ascent, ttf_glyph.descent = metrics

                    ttf_glyph.image = Image.new("RGBA", (ttf_glyph.width, ttf_glyph.height), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(ttf_glyph.image)

                    x_offset = -bbox[0]
                    y_offset = -bbox[1]

                    draw.text((x_offset, y_offset), char, font=font_pil, fill=(255, 255, 255, 255))

                    # draw the boundary line for debug
                    if developer_mode:
                        # texture range
                        rect_x1 = 0
                        rect_y1 = 0
                        rect_x2 = ttf_glyph.width - 1
                        rect_y2 = ttf_glyph.height - 1
                        rect_x1, rect_x2 = min(rect_x1, rect_x2), max(rect_x1, rect_x2)
                        rect_y1, rect_y2 = min(rect_y1, rect_y2), max(rect_y1, rect_y2)
                        draw.rectangle(
                            [rect_x1, rect_y1, rect_x2, rect_y2],
                            outline=(255, 0, 0, 255),  # red
                            width=1
                        )

                    ttf_glyphs_dict[ttf_glyph.unicode] = ttf_glyph
                    # self.ttf_glyphs.append(ttf_glyph)

                except Exception as e:
                    print(f"[Warning] failed to render character '{char}' (U+{ord(char):04X}): {e}")
                    missing_count += 1
                    continue

            if missing_count > 0:
                print(f"{missing_count} characters are not rendered, they may unsupported in \"{ttf_basename}\"")

            n += 1

        self.ttf_glyphs = list(ttf_glyphs_dict.values())
        self.ttf_glyphs = sorted(self.ttf_glyphs, key=lambda g: g.unicode, reverse=False)
        print(f"Successfully rendered {len(self.ttf_glyphs)} characters!")

    def pack_textures(self, texture_width: int, texture_height: int,
                        char_spacing: int, texture_margin: int) -> None:
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

            # if need to create a new texture file
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

    def generate_glyphs_data(self, texture_name_base: str, texture_format: str) -> None:
        for texture in self.textures:
            for ttf_glyph in texture.ttf_glyphs:
                glyph = Glyph()
                glyph.unicode = ord(ttf_glyph.char)

                glyph.height = ttf_glyph.height
                glyph.top = int(ttf_glyph.ascent + ttf_glyph.margin - ttf_glyph.bbox[1])
                glyph.bottom = glyph.top - ttf_glyph.height
                # glyph.pitch = ttf_glyph.width
                # glyph.xSkip = ttf_glyph.width - ttf_glyph.margin * 2 + 2
                glyph.pitch = ttf_glyph.width + ttf_glyph.margin
                glyph.xSkip = ttf_glyph.width
                glyph.imageWidth = ttf_glyph.width
                glyph.imageHeight = ttf_glyph.height

                glyph.s = ttf_glyph.x / texture.width
                glyph.t = ttf_glyph.y / texture.height
                glyph.s2 = (ttf_glyph.x + ttf_glyph.width) / texture.width
                glyph.t2 = (ttf_glyph.y + ttf_glyph.height) / texture.height

                glyph.glyph = 0
                glyph.shaderName = f"fonts/{texture_name_base}_{texture.texture_index:d}.{texture_format}"

                self.glyphs.append(glyph)

    def save_textures(self, texture_name_base: str, texture_format: str) -> None:
        """
        texture_format: "tga", "png"
        """
        format: str = texture_format.lower()

        for texture in self.textures:
            atlas = Image.new("RGBA", (texture.width, texture.height), (0, 0, 0, 0))

            for ttf_glyph in texture.ttf_glyphs:
                if ttf_glyph.image:
                    atlas.paste(ttf_glyph.image, (ttf_glyph.x, ttf_glyph.y))

            texture_name = f"{texture_name_base}_{texture.texture_index:d}"
            if format == "tga":
                tga_path = os.path.join(self.output_dir, f"{texture_name}.tga")
                self._save_tga_for_rtcw(atlas, tga_path)
            elif format == "png":
                tga_path = os.path.join(self.output_dir, f"{texture_name}.png")
                self._save_png_for_rtcw(atlas, tga_path)

            print(f"Saved texture: {texture_name}.{format} ({texture.width}x{texture.height})")

    def _save_tga_for_rtcw(self, image: Image.Image, filepath: str) -> None:
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

    def _save_png_for_rtcw(self, image: Image.Image, filepath: str) -> None:
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        image.save(filepath, 'PNG', optimize=True, compress_level=6)

    def save_fnt_file(self, filepath: str, texture_name_base: str) -> None:
        special_chars: Dict[int, str] = {10: "(LF)", 13: "(CR)"}

        with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
            # some information about generated font
            f.write(f"// RTCW Font File\n")
            f.write(f"// Generated from:\n")
            for i in range(len(self.multi_table)):
                ttf_basename = os.path.basename(self.multi_table[i].ttf_path)
                char_ranges = self.corresponding_table[i][-1]
                f.write(f"// \t\"{ttf_basename}\": {char_ranges}\n")
            f.write(f"// Font size: {self.font_size}\n")
            f.write(f"// Total characters: {len(self.glyphs)}\n")
            f.write(f"// Texture base name: {texture_name_base}\n\n")

            sorted_glyphs = sorted(self.glyphs, key=lambda g: g.unicode)
            f.write("// glyphs\n{\n")
            for glyph in sorted_glyphs:
                if glyph.unicode in special_chars:
                    f.write(f"\t// Character: '{special_chars[glyph.unicode]}' (U+{glyph.unicode:04X})\n")
                else:
                    f.write(f"\t// Character: '{chr(glyph.unicode)}' (U+{glyph.unicode:04X})\n")
                f.write(f"\tchar {glyph.unicode}\n")
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

    def generate(self, output_name: str, font_size: int = 36, save_dat: bool = True,
                    texture_width: int = 1024, texture_height: int = 1024,
                    char_margin: int = 2, char_spacing: int = 2, texture_margin: int = 8,
                    texture_format: str = "tga", developer_mode: bool = False) -> None:
        """
        texture_format: "tga", "png"
        developer_mode: draw colored boundary lines for each font for adjustment purposes
        """
        format = texture_format.lower()
        self.font_size = font_size
        self.glyphs = []
        self.ttf_glyphs = []

        self.render_glyphs(margin=char_margin, developer_mode=developer_mode)
        self.pack_textures(texture_width=texture_width, texture_height=texture_height,
                            char_spacing=char_spacing, texture_margin=texture_margin)
        self.generate_glyphs_data(texture_name_base=output_name, texture_format=format)
        self.save_textures(texture_name_base=output_name, texture_format=format)

        if save_dat:
            # generate .fnt data file
            fnt_path = os.path.join(self.output_dir, f"{output_name}.fnt")
            self.save_fnt_file(filepath=fnt_path, texture_name_base=output_name)

        print(f"Generation completed! Created {len(self.textures)} {format.upper()} files and 1 FNT file")


# example
if __name__ == "__main__":
    # the meaning of font_size is not quite the same as in rtcw

    table = [
        # Chinese, CJK
        # as base template, if the specified font with the same code point is used later
        # the corresponding font data will be overwritten, so set full range (0 - 0x10000) in this
        [
            "./test/ttf/simhei.ttf",
            [(0x0000, 0x10000)]
        ],
        # Arabic
        [
            "./test/ttf/MSUIGHUB.TTF",
            [(0x0590, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)]
        ],
        # Korean
        [
            "./test/ttf/malgun.ttf",
            [(0x1100, 0x11FF), (0x3130, 0x318F), (0xAC00, 0xD7AF), (0xA960, 0xA97F), (0xD7B0, 0xD7FF)]
        ],
        # Japanese
        [
            "./test/ttf/YuGothM.ttc",
            [(0x3040, 0x309F), (0x30A0, 0x30FF), (0x3100, 0x32FF)]
        ],
        # Eastern and Western European fonts, Ascill
        [
            "./test/ttf/DejaVuSerif.ttf",
            [(0x0000, 0x04FF)]
        ]
    ]

    generator = FontImageMulti(table, "./output", max_glyphs=65536)
    generator.generate("fontImage_utf8_1", 36, True, texture_width=2048, texture_height=2048,
                        texture_format="png", developer_mode=False)

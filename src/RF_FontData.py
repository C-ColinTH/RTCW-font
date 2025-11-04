"""
    RF_FontData.py
    Read FNT and DAT files or convert FNT and DAT files to each other for RTCW.
"""


from typing import Tuple, List, Dict, Optional, NoReturn, AnyStr
import os
import struct
from RF_Set import *


class FontData:
    """
    read FNT and DAT files or convert FNT and DAT files to each other for RTCW.
    """

    def __init__(self, filepath: str = "", output_dir: str = "", max_glyphs: int = GLYPHS_PER_FONT):
        self.glyphs: Dict[int, Glyph] = {}
        self.glyphScale: float = 0.5
        self.name: str = ""

        self.max_glyphs = max_glyphs
        self.output_dir: str = output_dir
        self.file_path: str = filepath

        self._startup()


    def _startup(self) -> NoReturn:
        if self.output_dir and not self.output_dir.isspace():
            os.makedirs(self.output_dir, exist_ok=True)

        # path is not specified, user may want to call the read data function later
        if not self.file_path or self.file_path.isspace():
            return

        if self.file_path.endswith(".fnt") and os.path.exists(self.file_path):
            self.read_fnt(filepath=self.file_path)
        elif self.file_path.endswith(".dat") and os.path.exists(self.file_path):
            self.read_dat(filepath=self.file_path)
        else:
            print(f"[WARNING] unable to read from \"{self.file_path}\"!")

    def read_fnt(self, filepath: str, encode: str = 'utf-8') -> NoReturn:
        """
        :param filepath: file path
        :param encode: 'ascii', 'latin-1', 'utf-8', 'GBK', 'GB2312', 'cp1251', 'utf-16', 'utf-32'...
        """

        """ tool functions """
        def fnt_remove_lines_comments(lines: List[AnyStr]) -> List[AnyStr]:
            return _remove_lines_comments(lines)

        def fnt_get_line_value(keyname: str) -> str:
            nonlocal i, length, lines, filepath
            j: int = 0
            line = lines[i+j].strip()

            while i + j < length and '}' not in line:
                if (keyname + ' ') in line and keyname[0] == line[0]:
                    value_str: str = line
                    return value_str.split()[-1]

                j += 1
                line = lines[i+j].strip()
            else:
                raise SyntaxError(f"[Error] {filepath} line {i+1}, glyph missing \"{keyname}\" data!")

        """ read_fnt """
        with open(file=filepath, mode='r', encoding=encode, errors='ignore') as f:
            lines: List[AnyStr] = fnt_remove_lines_comments(f.readlines())

        i: int = 0
        length: int = len(lines)
        while i < length:
            line: str = lines[i].strip()
            if "char " in line:
                value = int(fnt_get_line_value("char"))
                index = value

                glyph = Glyph()
                glyph.height = int(fnt_get_line_value("height"))
                glyph.top = int(fnt_get_line_value("top"))
                glyph.bottom = int(fnt_get_line_value("bottom"))
                glyph.pitch = int(fnt_get_line_value("pitch"))
                glyph.xSkip = int(fnt_get_line_value("xSkip"))
                glyph.imageWidth = int(fnt_get_line_value("imageWidth"))
                glyph.imageHeight = int(fnt_get_line_value("imageHeight"))
                glyph.s = float(fnt_get_line_value("s"))
                glyph.t = float(fnt_get_line_value("t"))
                glyph.s2 = float(fnt_get_line_value("s2"))
                glyph.t2 = float(fnt_get_line_value("t2"))
                glyph.glyph = int(fnt_get_line_value("glyph"))
                glyph.shaderName = fnt_get_line_value("shaderName")
                glyph.id = index
                self.glyphs[index] = glyph

                i += len(vars(glyph)) - 1     # numbers of Glyph instance variable
                continue

            if "glyphScale " in line:
                self.glyphScale = float(fnt_get_line_value("glyphScale"))
                self.name = fnt_get_line_value("name")
                break

            i += 1

    def read_dat(self, filepath: str) -> NoReturn:
        """ tool function """
        def parse_glyph_info(data_block, glyphs_index) -> Glyph:
            if len(data_block) < PER_GLYPH_DATA_SIZE:
                raise ValueError(f"[Error] the size of glyph data block is below the minimum \
                                 {PER_GLYPH_DATA_SIZE}, please make sure file is RTCW valid format.")

            glyph = Glyph()
            glyph.id = glyphs_index
            glyph.height = struct.unpack('<i', data_block[0:4])[0]
            glyph.top = struct.unpack('<i', data_block[4:8])[0]
            glyph.bottom = struct.unpack('<i', data_block[8:12])[0]
            glyph.pitch = struct.unpack('<i', data_block[12:16])[0]
            glyph.xSkip = struct.unpack('<i', data_block[16:20])[0]
            glyph.imageWidth = struct.unpack('<i', data_block[20:24])[0]
            glyph.imageHeight = struct.unpack('<i', data_block[24:28])[0]
            glyph.s = struct.unpack('<f', data_block[28:32])[0]
            glyph.t = struct.unpack('<f', data_block[32:36])[0]
            glyph.s2 = struct.unpack('<f', data_block[36:40])[0]
            glyph.t2 = struct.unpack('<f', data_block[40:44])[0]
            glyph.glyph = struct.unpack('<i', data_block[44:48])[0]
            glyph.shaderName = '\"' + data_block[48:PER_GLYPH_DATA_SIZE].split(b'\x00', maxsplit=1)[0].decode('latin-1', errors='ignore') + '\"'

            return glyph

        """ read_dat """
        with open(file=filepath, mode='rb') as f:
            # fontinfo data block
            f.seek(-GLOBAL_INFO_DATA_SIZE, 2)
            global_data = f.read(GLOBAL_INFO_DATA_SIZE)

            if len(global_data) < GLOBAL_INFO_DATA_SIZE:
                raise ValueError("[Error] broken glyph data block!")

            self.glyphScale = struct.unpack('<f', global_data[0:4])[0]
            self.name = '\"' + global_data[4:GLOBAL_INFO_DATA_SIZE].split(b'\x00', maxsplit=1)[0].decode('latin-1',errors='ignore') + '\"'

            # glyphs data block size
            f.seek(0, 2)
            file_size = f.tell()
            glyphs_data_size = file_size - GLOBAL_INFO_DATA_SIZE
            if glyphs_data_size % PER_GLYPH_DATA_SIZE != 0:
                print(f"[Warning] data block is incompatible or broken!")

            glyphs_count = glyphs_data_size // PER_GLYPH_DATA_SIZE
            print(f"found {glyphs_count} data blocks of glyph")

            f.seek(0)
            glyphs_index = 0
            while glyphs_index < glyphs_count:
                glyph_block = f.read(PER_GLYPH_DATA_SIZE)
                if len(glyph_block) < PER_GLYPH_DATA_SIZE:
                    break
                elif glyph_block == bytes(PER_GLYPH_DATA_SIZE):
                    # print(f"index {glyphs_index}: unuseful glyph data, skip...")
                    glyphs_index += 1
                    continue

                try:
                    glyph_info = parse_glyph_info(glyph_block, glyphs_index)
                    self.glyphs[glyph_info.id] = glyph_info
                    glyphs_index += 1

                    if glyphs_index % 100 == 0:
                        print(f"\rparsed {glyphs_index}/{glyphs_count} glyph", end='', flush=True)
                    elif glyphs_index == glyphs_count:
                        print(f"\rparsed {glyphs_count}/{glyphs_count} glyph", flush=True)

                except Exception as e:
                    print(f"Error: failed to parse glyph {glyphs_index}: {e}")
                    break

    def write_fnt(self, filename: str = "", output_dir: str = "") -> NoReturn:
        """
        Before using this, use read_fnt() to initial data from a RTCW .fnt file
        :param filename: save file name
        """
        special_chars: Dict[int, str] = {10: "(LF)", 13: "(CR)"}

        if self.glyphs is None or len(self.glyphs) == 0:
            print("[Warning] empty data to write!")
            return

        if not filename or filename.isspace():
            basename: str = os.path.basename(self.file_path)
        else:
            basename: str = os.path.basename(filename)

        basename = basename.rsplit(".", maxsplit=1)[0] + ".fnt"
        if output_dir and not output_dir.isspace():
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, basename)
        else:
            filepath = os.path.join(self.output_dir, basename)

        with open(file=filepath, mode='w', encoding='utf-8', errors='ignore') as f:
            # info
            f.write(f"// RTCW Font File\n")
            f.write(f"// Generated from: {os.path.basename(self.file_path)}\n")
            f.write(f"// Total characters: {len(self.glyphs)}\n\n")

            # glyphs
            f.write("// glyphs\n{\n")
            for i in range(self.max_glyphs):
                indexes = self.glyphs.keys()
                if i not in indexes:
                    pass
                else:
                    glyph = self.glyphs[i]
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
                    f.write(f"\t\tglyph {glyph.glyph}\n")
                    f.write(f"\t\tshaderName {glyph.shaderName}\n")
                    f.write("\t}\n\n")
            f.write("}\n\n")

            f.write("// fontinfo\n{\n")
            f.write(f"\tglyphScale {self.glyphScale:.6f}\n")
            f.write(f"\tname {self.name}\n")
            f.write("}\n")

    def write_dat(self, filename: str = "", output_dir: str = "") -> NoReturn:
        """
        Before using this, use read_fnt() to initial data from a RTCW .fnt file
        :param filename: save file name
        :param output_dir: save file path
        """

        """ tool functions """
        def dat_int_to_hex(value: int) -> bytes:
            byte_data = value.to_bytes(4, byteorder='little', signed=True)
            return byte_data

        def dat_float_to_hex(value: float) -> bytes:
            byte_data = struct.pack('<f', value)
            return byte_data

        def dat_str_to_hex(string: str, byte_len=MAX_SHADER_NAME) -> bytes:
            length = len(string)
            if length > byte_len:
                byte_data = string[:byte_len].encode('utf-8')
            elif length < byte_len:
                byte_data = string.encode('utf-8') + (byte_len - length) * b'\x00'
            else:
                byte_data = string.encode('utf-8')
            return byte_data

        """ write_dat """
        if self.glyphs is None or len(self.glyphs) == 0:
            print("[Warning] empty data to write!")
            return

        if not filename or filename.isspace():
            filename = os.path.basename(self.file_path.replace(".fnt", ".dat"))

        if output_dir and not output_dir.isspace():
            os.makedirs(output_dir, exist_ok=True)
            filename = os.path.join(output_dir, filename)
        else:
            filename = os.path.join(self.output_dir, filename)

        with open(file=filename, mode='wb') as f:
            # glyphs
            indexes = self.glyphs.keys()
            for i in range(self.max_glyphs):
                if i not in indexes:
                    f.write(bytes(PER_GLYPH_DATA_SIZE))   # write PER_GDATA_LEN * b"0x00"
                else:
                    glyph = self.glyphs[i]
                    f.write(dat_int_to_hex(glyph.height))
                    f.write(dat_int_to_hex(glyph.top))
                    f.write(dat_int_to_hex(glyph.bottom))
                    f.write(dat_int_to_hex(glyph.pitch))
                    f.write(dat_int_to_hex(glyph.xSkip))
                    f.write(dat_int_to_hex(glyph.imageWidth))
                    f.write(dat_int_to_hex(glyph.imageHeight))
                    f.write(dat_float_to_hex(glyph.s))
                    f.write(dat_float_to_hex(glyph.t))
                    f.write(dat_float_to_hex(glyph.s2))
                    f.write(dat_float_to_hex(glyph.t2))
                    f.write(dat_int_to_hex(glyph.glyph))
                    f.write(dat_str_to_hex(glyph.shaderName.replace('\"', ''), byte_len=MAX_SHADER_NAME))

            # fontinfo
            f.write(dat_float_to_hex(self.glyphScale))
            f.write(dat_str_to_hex(self.name.replace('\"', ''), byte_len=MAX_QPATH))

    def show_info(self, index: int = -1) -> NoReturn:
        """
        :param index: show which one, set -1 to show all
        """

        print("------font info------")
        if self.glyphs:
            indexes = self.glyphs.keys()

            for i in indexes:
                if index >= 0 and i != index:
                    continue

                glyph = self.glyphs[i]
                print(f"char {i}")
                print(f"\theight {glyph.height}")
                print(f"\ttop {glyph.top}")
                print(f"\tbottom {glyph.bottom}")
                print(f"\tpitch {glyph.pitch}")
                print(f"\txSkip {glyph.xSkip}")
                print(f"\timageWidth {glyph.imageWidth}")
                print(f"\timageHeight {glyph.imageHeight}")
                print(f"\ts {glyph.s:.6f}")
                print(f"\tt {glyph.t:.6f}")
                print(f"\ts2 {glyph.s2:.6f}")
                print(f"\tt2 {glyph.t2:.6f}")
                print(f"\tglyph {glyph.glyph}")
                print(f"\tshaderName {glyph.shaderName}\n")

                if i == index:
                    break

            print(f"glyphScale {self.glyphScale:.6f}")
            print(f"name {self.name}\n")

    def show_info_need(self, index: int) -> NoReturn:
        self.show_info(index)


def _remove_lines_comments(lines: List[AnyStr]) -> List[AnyStr]:
    cleaned_lines: List = []
    in_comment: bool = False

    if lines is None or len(lines) == 0:
        return cleaned_lines

    for line in lines:
        if not in_comment:
            # handle comment "//"
            if "//" in line:
                # line = re.sub(r'//.*', '', line)
                line = line.split("//", maxsplit=1)[0] + '\n'

            # handle comment "/*"
            if "/*" in line:
                in_comment = True
                before_comment = line.split("/*")[0]
                if before_comment:
                    cleaned_lines.append(before_comment)
                elif "*/" in line:
                    # handle comment "*/" in the same line
                    in_comment = False
                    after_comment = line.split("*/", maxsplit=1)[-1]
                    if after_comment:
                        cleaned_lines.append(after_comment)
                else:
                    cleaned_lines.append("\n")
            else:
                cleaned_lines.append(line)
        else:
            # handle comment "*/" in other line
            if "*/" in line:
                in_comment = False
                after_comment = line.split("*/", maxsplit=1)[-1]
                if after_comment:
                    cleaned_lines.append(after_comment)
            else:
                cleaned_lines.append("\n")

    return cleaned_lines


# example
if __name__ == '__main__':
    fontInfo = FontData("./test/fontImage_36.fnt")
    # fontInfo.show_info()
    fontInfo.write_dat(output_dir="./test")
    # fontInfo.write_fnt(output_dir="./test")


from typing import Tuple, List, Set, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image
    from fontTools.ttLib import TTFont


""" ========== RTCW consistent settings ========== """
MAX_SHADER_NAME = 32        # consistent with RTCW
MAX_QPATH = 64

GLOBAL_INFO_DATA_SIZE = 4 + MAX_QPATH                   # RTCW global fontinfo data block length
PER_GLYPH_DATA_SIZE = 4 * 12 + MAX_SHADER_NAME          # per RTCW Glyph data block length

GLOBAL_UNIC_HEADER = "UNIC"
GLOBAL_UNIC_HEADER_SIZE = len(GLOBAL_UNIC_HEADER.encode('utf-8'))
PER_GLYPH_UNIC_DATA_SIZE = 4 * 13 + MAX_SHADER_NAME     # per unicode Glyph data block length


""" =============== custom settings =============== """
GLYPHS_PER_FONT = 256       # Note: set 256 for default RTCW
SYS_FONTS_DIR = "C:/Windows/Fonts"


class Glyph:
    def __init__(self):
        self.unicode: int = 0
        self.height: int = 0
        self.top: int = 0
        self.bottom: int = 0
        self.pitch: int = 0
        self.xSkip: int = 0
        self.imageWidth: int = 0
        self.imageHeight: int = 0
        self.s: float = 0.0
        self.t: float = 0.0
        self.s2: float = 0.0
        self.t2: float = 0.0
        self.glyph: int = 0
        self.shaderName: str = ""


class TTFGlyph:
    def __init__(self):
        self.char_index: int = 0    # not the codepoint
        self.char: str = ''
        self.unicode: int = 0
        self.x: int = 0
        self.y: int = 0
        self.width: int = 0
        self.height: int = 0
        self.margin: int = 0
        self.ascent: int = 0
        self.descent: int = 0
        self.image: Optional[Image.Image] = None    # PIL.Image from pillow
        self.bbox: Tuple[float, float, float, float] = (0, 0, 0, 0)
        self.texture_index: int = 0


class Texture:
    def __init__(self):
        self.texture_index: int = 0
        self.width: int = 0
        self.height: int = 0
        self.ttf_glyphs: List[TTFGlyph] = []


class MultiTable:
    def __init__(self):
        self.ttf_path: str = ""
        self.font_size: int = 0
        self.char_ranges: List[Tuple[int, int]] = []
        self.ttfont: Optional[TTFont] = None
        self.available_chars: List[str] = []
        self.selected_chars: Set[int] = set()

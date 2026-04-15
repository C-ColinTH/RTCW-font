# RTCWfont
These script files will generate TGA/PNG bitmap font textures and FNT/DAT data files for Return to Castle Wolfenstein (RTCW) and RealRTCW from TrueType fonts (TTF/TTC).


## How to use
__Prerequisites__

Python 3.12 or later recommended.

Required libraries and recommended version:
- numpy: 1.26.4
- pillow: 12.0.0
- fonttools: 4.60.1


__Quick Start__

1. Clone or download the scource files.
2. Install dependencies libraries.
3. Place your TrueType font files (.ttf or .ttc) in a directory (e.g., ./ttffont/)
4. Modify the main.py file to configure your font generation by editing some parameters in main.py
5. Execute the main script: `python main.py`


By default, the script will:

1. Generate TGA font textures and a base FNT file.
2. Convert the FNT file to a DAT file (RTCW binary format)


__Custom Configuration__

You can adjust generation parameters in the generate() method:
generator.generate(
    output_name=output_name,
    texture_width=1024,      # Texture atlas width
    texture_height=1024,     # Texture atlas height
    char_margin=2,           # Margin around each character
    char_spacing=2,          # Spacing between characters
    texture_margin=8,        # Margin around texture edges
    texture_format="tga"     # "tga" or "png" format
)


__File Formats Generated__

1. Texture files: .tga or .png files containing font glyphs.
2. FNT file: Text-based font data file for reading or editing.
3. DAT file: Binary font data file for RTCW/RealRTCW game engine.


__Advanced Setting__

- Unicode Support: Set max_glyphs=65536 for extended Unicode support (default: 256 for RTCW)
- Developer Mode: Enable developer_mode=True to draw debugging borders


__Notes__
- The tool will first look for fonts in the specified path, then try the Windows system fonts directory if not found.
- RTCW's default font limit is 256 glyphs. Modify both the script and RTCW code for more glyphs.
- The font_size parameter doesn't exactly match RTCW's font size system.
- Supported font formats: TrueType (.ttf) and TrueType Collections (.ttc)
- If you get font loading errors, ensure the font path is correct.
- For Unicode support, verify your font contains the required characters.

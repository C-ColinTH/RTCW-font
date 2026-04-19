"""
Since these files were wrote by Python3.12, so it recommend to run on 3.12 or later version.
Also, the recommended version for third-party libraries is:
    numpy: 1.26.4
    pillow: 12.0.0
    fonttools: 4.60.1

If you want to generate fonts more than 256, chanege 'max_glyphs'.
You may also need to modify RTCW code to support more fonts. For default RTCW, it should be set to 256.
"""


from RF_FontData import FontData
from RF_FontImage import FontImage
from RF_FontImageMulti import FontImageMulti
import traceback


def generateImage():
    # Generate TGA font textures and base FNT data file
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
        # [
        #     "./test/ttf/DejaVuSerif.ttf",     # Additional downloads may be required
        #     [(0x0000, 0x04FF)]
        # ]
    ]

    generator = FontImageMulti(corresponding_table=table, output_dir=output_dir, max_glyphs=max_glyphs)
    generator.generate(
        output_name=output_name,
        font_size=font_size,
        texture_width=texture_size,
        texture_height=texture_size,
        char_margin=2,
        char_spacing=2,
        texture_margin=8,
        texture_format=texture_format,
        max_workers=max_workers,
        developer_mode=False
    )


def convertData():
    # convert FNT and DAT file to each other
    if FNTtoDat:
        file_path = f"{output_dir}/{output_name}.fnt"
    elif DATtoFNT:
        file_path = f"{output_dir}/{output_name}.dat"
    else:
        return

    fontinfo = FontData(
        file_path=file_path,
        output_dir=output_dir,
        max_glyphs=max_glyphs
    )

    if file_path.split('.')[-1] == "fnt":
        fontinfo.write_dat()
    elif file_path.split('.')[-1] == "dat":
        fontinfo.write_fnt()


def main():
    if GenerateImage:
        generateImage()
    if GenerateData:
        convertData()


if __name__ == '__main__':
    GenerateImage = True
    GenerateData = True
    FNTtoDat = True
    DATtoFNT = False

    output_dir = "./test"
    output_name = "fontImage_36"
    font_size = 36
    texture_size = 1024
    texture_format = "tga"
    max_workers = 8     # Maximum number of processes for parallel acceleration
    max_glyphs = 256

    try:
        main()
    except Exception:
        print(traceback.format_exc())
    finally:
        input("Enter any key to exit...")


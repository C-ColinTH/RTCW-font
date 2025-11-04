"""
Since these files were wrote by Python3.12, so it recommend to run on 3.12 or later version.
Also, the recommended version for third-party libraries is:
    numpy: 1.26.4
    pillow: 12.0.0
    fonttools: 4.60.1

If you want to generate fonts more than 256, chanege 'GLYPHS_PER_FONT' in RF_Set.py. You may also
need to modify RTCW code to support more fonts. For default RTCW, it should be set to 256.
"""


from RF_FontData import FontData
from RF_FontImage import FontImage
import traceback


def generateImage():
    # Generate TGA font textures and base FNT data file
    ttf_path = "./ttffont/simhei.ttf"
    font_size = 24
    output_dir = "./test"
    output_name = f"fontImage_{font_size}"

    generator = FontImage(ttf_path, font_size, output_dir)
    generator.generate(
        output_name=output_name,
        texture_width=1024,
        texture_height=1024,
        char_margin=2,
        char_spacing=2,
        texture_margin=8
    )


def convertData():
    # convert FNT and DAT file to each other
    file_path = "./test/fontImage_24.fnt"
    output_dir = "./test"

    fontinfo = FontData(file_path, output_dir)
    fontinfo.write_dat()


def main():
    GenerateImage = True
    GenerateData = True

    if GenerateImage:
        generateImage()
    if GenerateData:
        convertData()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print(traceback.format_exc())


from fontTools.ttLib import TTFont
import re

# List of font files to load
fonts = [
    "fonts/Font Awesome 6 Free-Solid-900.otf",
    "fonts/Font Awesome 6 Free-Regular-400.otf",
    "fonts/Font Awesome 6 Brands-Regular-400.otf"
]

def list_glyphs(font_path):
    font = TTFont(font_path)
    cmap = font['cmap'].getBestCmap()
    return set(cmap.keys())

def parse_defined_glyphs(py_file_path):
    pattern = re.compile(r"ICON_[A-Z0-9_]+ = '\\u([0-9a-fA-F]{4,6})'")
    defined = set()
    with open(py_file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = pattern.search(line)
            if match:
                defined.add(int(match.group(1), 16))
    return defined

# Get all glyphs from font files
all_glyphs = set()
for font_path in fonts:
    all_glyphs.update(list_glyphs(font_path))

# Get already defined glyphs in the IconsFontAwesome5 class
defined_glyphs = parse_defined_glyphs("Py4GWCoreLib/IconsFontAwesome5.py")

# Compute missing glyphs
missing_glyphs = sorted(all_glyphs - defined_glyphs)

# Output to file
with open("missing_icons.py", "w", encoding="utf-8") as out_file:
    for codepoint in missing_glyphs:
        out_file.write(f"UNKNOWN_{codepoint:04X} = '\\u{codepoint:04x}'\n")

print(f"Wrote {len(missing_glyphs)} missing icons to missing_icons.py")

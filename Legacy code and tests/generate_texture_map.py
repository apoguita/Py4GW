import os
import re

ITEM_MODEL_TEXTURE_PATH = "Textures\\Item Models\\"

def generate_texture_map(directory):
    texture_map = {}
    pattern = re.compile(r"\[(\d+)\]\s*-\s*(.+?)\.(png|jpg|jpeg)", re.IGNORECASE)

    for filename in os.listdir(directory):
        match = pattern.match(filename)
        if match:
            model_id = int(match.group(1))
            texture_map[model_id] = ITEM_MODEL_TEXTURE_PATH + filename

    return texture_map

if __name__ == "__main__":
    output_file = "item_model_texture_map.py"
    texture_map = generate_texture_map(ITEM_MODEL_TEXTURE_PATH)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("ITEM_MODEL_TEXTURE_PATH = \"Textures\\\\Item Models\\\\\"\n")
        f.write("ItemModelTextureMap = {\n")
        for model_id, path in sorted(texture_map.items()):
            f.write(f"    {model_id}: ITEM_MODEL_TEXTURE_PATH + \"{os.path.basename(path)}\",\n")
        f.write("}\n")

    print(f"✅ Texture map written to {output_file}")

import subprocess
import os
import uuid
def render_drawio_to_png(xml_content, output_dir="data/output/images"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    file_id = str(uuid.uuid4())
    drawio_path = os.path.join(output_dir, f"{file_id}.drawio")
    png_path = os.path.join(output_dir, f"{file_id}.png")
    with open(drawio_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    subprocess.run(["drawio", "-x", "-f", "png", "-o", png_path, drawio_path], check=True)
    return png_path
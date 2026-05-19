import pymupdf
import os
def extract_data_from_pdf(file_path, output_image_dir="data/output/images"):
    if not os.path.exists(output_image_dir):
        os.makedirs(output_image_dir)
    document = pymupdf.open(file_path)
    full_text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        full_text += page.get_text()
        image_list = page.get_images()
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_path = os.path.join(output_image_dir, f"page_{page_num}_img_{img_index}.{image_ext}")
            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)
    return full_text
import fitz  # PyMuPDF
from PIL import Image
from tqdm import tqdm

WHITE = (255, 255, 255)

def check_curr_subset_of_next(curr, next):
    w,h = curr.size
    for i in range(w):
        for j in range(h):
            p1 = curr.getpixel((i,j))
            p2 = next.getpixel((i,j))
            if(not(p1==p2 or p1==WHITE)):
                return False
    return True

def get_image_from_page(page):
    pixmap = page.get_pixmap()
    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    return image

def reduce_pdf(input_pdf, output_pdf):
    deleted = []
    doc = fitz.open(input_pdf)
    init_len = len(doc)
    print('\nScanning pages to detect redundancy...\n')
    for page_num in tqdm(range(len(doc))):
        current_page = doc.load_page(page_num)
        current_image = get_image_from_page(current_page)
        if page_num + 1 < len(doc):
            next_page = doc.load_page(page_num + 1)
            next_image = get_image_from_page(next_page)
            if check_curr_subset_of_next(current_image, next_image):
                deleted.append(page_num)
    print(f'\n{len(deleted)} redundant pages found...')
    r = 0
    for page_num in deleted:
        doc.delete_page(page_num-r)
        r += 1
    final_len = len(doc)
    doc.save(output_pdf)
    doc.close()
    ratio = 100 - (final_len/init_len)*100
    print(f'{output_pdf} saved successfully with {ratio:.2f}% reduction...\n')

pdf_path = "in.pdf"
reduce_pdf(pdf_path,'out.pdf')

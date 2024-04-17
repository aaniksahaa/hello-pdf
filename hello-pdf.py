import fitz  # PyMuPDF
from PIL import Image
from tqdm import tqdm
import os 

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

def extract_pages(input_pdf, output_pdf, start_page, end_page):
    in_doc = fitz.open(input_pdf)
    out_doc = fitz.open()
    if(end_page > len(in_doc)):
        end_page = len(in_doc)
    out_doc.insert_pdf(in_doc, from_page=start_page-1, to_page=end_page-1)
    out_doc.save(output_pdf)
    out_doc.close()
    in_doc.close()
    print(f'Pages {start_page} to {end_page} extracted successfully and saved as {output_pdf}')

def merge_pdfs_in_box(output_filename):
    folder_path = 'box'
    out_doc = fitz.open()
    print('\nMerging pdf files in box...\n')
    for filename in tqdm(os.listdir(folder_path)):
        if filename.endswith('.pdf'):
            filepath = os.path.join(folder_path, filename)
            temp_doc = fitz.open(filepath)
            out_doc.insert_pdf(temp_doc)
    out_doc.save(output_filename)
    out_doc.close()
    print(f"\nAll PDFs in '{folder_path}' merged into '{output_filename}'\n")

def add_extension_if_absent(filename):
    return filename if filename.endswith('.pdf') else filename+'.pdf'

def menu():
    while True:
        last = 2*' '
        print("\nMenu:",end=last)
        print("1. Reduce PDF",end=last)
        print("2. Extract Pages",end=last)
        print("3. Merge PDFs in Box",end=last)
        print("4. Exit")

        choice = input("\nEnter your choice (1-4): ")

        if choice == '1':
            input_filename = input("Enter input PDF filename: ")
            output_filename = input("Enter output PDF filename: ")

            input_filename = add_extension_if_absent(input_filename)
            output_filename = add_extension_if_absent(output_filename)

            reduce_pdf(input_filename, output_filename)
        elif choice == '2':
            input_filename = input("Enter input PDF filename: ")
            output_filename = input("Enter output PDF filename: ")

            input_filename = add_extension_if_absent(input_filename)
            output_filename = add_extension_if_absent(output_filename)

            start_page = int(input("Enter start page number: "))
            end_page = int(input("Enter end page number: "))
            extract_pages(input_filename, output_filename, start_page, end_page)
        elif choice == '3':
            output_filename = input("Enter output PDF filename: ")

            output_filename = add_extension_if_absent(output_filename)

            merge_pdfs_in_box(output_filename)
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 4.")

# reduce_pdf('in.pdf','out.pdf')
# extract_pages('in.pdf','out.pdf',1,3)
# merge_pdfs_in_box('merged.pdf')

menu()

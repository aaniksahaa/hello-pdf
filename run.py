import fitz  # PyMuPDF
from PIL import Image
from tqdm import tqdm
import os 
import re
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)

WHITE = (255, 255, 255)
INBOX_FOLDER = 'inbox'
OUTBOX_FOLDER = 'outbox'

def ensure_folders_exist():
    """Create inbox and outbox folders if they don't exist"""
    os.makedirs(INBOX_FOLDER, exist_ok=True)
    os.makedirs(OUTBOX_FOLDER, exist_ok=True)

def get_pdfs_in_inbox():
    """Get list of PDF files in inbox folder"""
    if not os.path.exists(INBOX_FOLDER):
        return []
    
    pdfs = []
    for filename in sorted(os.listdir(INBOX_FOLDER)):
        if filename.lower().endswith('.pdf'):
            pdfs.append(filename)
    return pdfs

def display_pdfs_and_select(pdfs, action_name):
    """Display PDFs in inbox and let user select one"""
    if not pdfs:
        print(f"{Fore.RED}No PDF files found in '{INBOX_FOLDER}' folder!")
        return None
    
    print(f"\n{Fore.CYAN}Available PDFs in '{INBOX_FOLDER}':")
    for i, pdf in enumerate(pdfs, 1):
        print(f"{Fore.YELLOW}{i}. {Fore.WHITE}{pdf}")
    
    while True:
        try:
            choice = input(f"\n{Fore.GREEN}Select PDF for {action_name} (1-{len(pdfs)}): {Style.RESET_ALL}")
            choice = int(choice)
            if 1 <= choice <= len(pdfs):
                return pdfs[choice - 1]
            else:
                print(f"{Fore.RED}Invalid choice. Please enter a number between 1 and {len(pdfs)}")
        except ValueError:
            print(f"{Fore.RED}Invalid input. Please enter a number.")

def parse_ranges(range_string):
    """Parse range string like '12-123,23-222' or '1-3,5-6,7,8' into list of tuples"""
    ranges = []
    parts = [part.strip() for part in range_string.split(',')]
    
    for part in parts:
        if not part:
            continue
            
        if '-' in part:
            # Range like "12-123"
            try:
                start, end = part.split('-', 1)
                start = int(start.strip())
                end = int(end.strip())
                if start > end:
                    raise ValueError(f"Start page ({start}) cannot be greater than end page ({end})")
                ranges.append((start, end))
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Invalid range format: '{part}'. Use format like '12-123'")
                else:
                    raise e
        else:
            # Single page like "7"
            try:
                page = int(part.strip())
                ranges.append((page, page))
            except ValueError:
                raise ValueError(f"Invalid page number: '{part}'")
    
    return ranges

def get_valid_ranges(prompt_text):
    """Get valid ranges from user input with error handling"""
    while True:
        try:
            range_input = input(f"{Fore.GREEN}{prompt_text}: {Style.RESET_ALL}")
            if not range_input.strip():
                print(f"{Fore.RED}Please enter at least one range.")
                continue
            
            ranges = parse_ranges(range_input)
            if not ranges:
                print(f"{Fore.RED}No valid ranges found. Please try again.")
                continue
                
            return ranges
        except ValueError as e:
            print(f"{Fore.RED}Error: {e}")
            print(f"{Fore.YELLOW}Examples: '12-123,23-222' or '1-3,5-6,7,8'")

def add_pdf_extension(filename):
    """Add .pdf extension if not present"""
    return filename if filename.lower().endswith('.pdf') else filename + '.pdf'

def format_ranges_for_filename(ranges):
    """Convert ranges list to string for filename"""
    range_parts = []
    for start, end in ranges:
        if start == end:
            range_parts.append(str(start))
        else:
            range_parts.append(f"{start}-{end}")
    return ",".join(range_parts)

def check_curr_subset_of_next(curr, next):
    """Check if current page is a subset of next page"""
    w, h = curr.size
    for i in range(w):
        for j in range(h):
            p1 = curr.getpixel((i, j))
            p2 = next.getpixel((i, j))
            if not (p1 == p2 or p1 == WHITE):
                return False
    return True

def get_image_from_page(page):
    """Convert PDF page to PIL Image"""
    pixmap = page.get_pixmap()
    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    return image

def reduce_pdf(input_pdf, output_pdf):
    """Reduce PDF by removing redundant pages"""
    deleted = []
    input_path = os.path.join(INBOX_FOLDER, input_pdf)
    output_path = os.path.join(OUTBOX_FOLDER, output_pdf)
    
    doc = fitz.open(input_path)
    init_len = len(doc)
    print(f'\n{Fore.CYAN}Scanning pages to detect redundancy...\n')
    
    for page_num in tqdm(range(len(doc)), desc="Scanning pages"):
        current_page = doc.load_page(page_num)
        current_image = get_image_from_page(current_page)
        if page_num + 1 < len(doc):
            next_page = doc.load_page(page_num + 1)
            next_image = get_image_from_page(next_page)
            if check_curr_subset_of_next(current_image, next_image):
                deleted.append(page_num)
    
    print(f'\n{Fore.YELLOW}{len(deleted)} redundant pages found...')
    
    r = 0
    for page_num in deleted:
        doc.delete_page(page_num - r)
        r += 1
    
    final_len = len(doc)
    doc.save(output_path)
    doc.close()
    
    ratio = 100 - (final_len / init_len) * 100
    print(f'{Fore.GREEN}{output_pdf} saved successfully with {ratio:.2f}% reduction in outbox folder!\n')

def extract_pages_multiple_ranges(input_pdf, ranges):
    """Extract multiple page ranges from PDF and create both individual and merged PDFs"""
    input_path = os.path.join(INBOX_FOLDER, input_pdf)
    base_name = os.path.splitext(input_pdf)[0]
    
    in_doc = fitz.open(input_path)
    total_pages = len(in_doc)
    
    created_files = []
    temp_docs = []  # Store extracted documents for merging
    
    for start_page, end_page in ranges:
        # Validate page range
        if start_page < 1:
            print(f"{Fore.YELLOW}Warning: Start page {start_page} adjusted to 1")
            start_page = 1
        if end_page > total_pages:
            print(f"{Fore.YELLOW}Warning: End page {end_page} adjusted to {total_pages}")
            end_page = total_pages
        if start_page > total_pages:
            print(f"{Fore.YELLOW}Warning: Skipping range {start_page}-{end_page} (beyond document)")
            continue
            
        # Create output filename for individual extraction
        output_filename = f"page-{start_page}-{end_page}-{base_name}.pdf"
        output_path = os.path.join(OUTBOX_FOLDER, output_filename)
        
        # Extract pages for individual file
        out_doc = fitz.open()
        out_doc.insert_pdf(in_doc, from_page=start_page-1, to_page=end_page-1)
        out_doc.save(output_path)
        
        # Keep a copy for merged file
        temp_docs.append(fitz.open(output_path))
        
        out_doc.close()
        
        created_files.append(output_filename)
        print(f'{Fore.GREEN}Pages {start_page}-{end_page} extracted to {output_filename}')
    
    # Create merged PDF of all extractions
    if temp_docs:
        range_string = format_ranges_for_filename(ranges)
        merged_filename = f"page-{range_string}-{base_name}.pdf"
        merged_path = os.path.join(OUTBOX_FOLDER, merged_filename)
        
        merged_doc = fitz.open()
        for temp_doc in temp_docs:
            merged_doc.insert_pdf(temp_doc)
            temp_doc.close()
        
        merged_doc.save(merged_path)
        merged_doc.close()
        
        print(f'{Fore.CYAN}Merged extraction saved as: {merged_filename}')
        created_files.append(merged_filename)
    
    in_doc.close()
    
    if created_files:
        print(f'\n{Fore.CYAN}Created {len(created_files)} PDF file(s) in outbox folder!')
        print(f'{Fore.YELLOW}Individual extractions: {len(created_files)-1 if temp_docs else len(created_files)}')
        if temp_docs:
            print(f'{Fore.YELLOW}Merged extraction: 1')
    else:
        print(f'{Fore.RED}No valid pages were extracted!')

def merge_pdfs_by_selection(pdfs, ranges, output_filename):
    """Merge selected PDFs based on ranges"""
    output_path = os.path.join(OUTBOX_FOLDER, output_filename)
    out_doc = fitz.open()
    
    # Create list of PDFs to merge based on ranges
    pdfs_to_merge = []
    
    for start_idx, end_idx in ranges:
        # Convert to 0-based indexing and validate
        start_idx = max(1, start_idx) - 1  # Convert to 0-based
        end_idx = min(len(pdfs), end_idx) - 1  # Convert to 0-based
        
        if start_idx >= len(pdfs):
            print(f"{Fore.YELLOW}Warning: Range starting at {start_idx + 1} is beyond available PDFs")
            continue
            
        for i in range(start_idx, end_idx + 1):
            if i < len(pdfs):
                pdfs_to_merge.append((i + 1, pdfs[i]))  # Store 1-based index for display
    
    if not pdfs_to_merge:
        print(f"{Fore.RED}No valid PDFs selected for merging!")
        return
    
    print(f'\n{Fore.CYAN}Merging PDFs in this order:')
    for idx, (display_num, pdf_name) in enumerate(pdfs_to_merge, 1):
        print(f'{Fore.YELLOW}{idx}. {Fore.WHITE}{pdf_name} {Style.DIM}(was #{display_num})')
    
    print(f'\n{Fore.CYAN}Processing...')
    
    for _, pdf_name in tqdm(pdfs_to_merge, desc="Merging PDFs"):
        filepath = os.path.join(INBOX_FOLDER, pdf_name)
        temp_doc = fitz.open(filepath)
        out_doc.insert_pdf(temp_doc)
        temp_doc.close()
    
    out_doc.save(output_path)
    out_doc.close()
    
    print(f"\n{Fore.GREEN}All selected PDFs merged into '{output_filename}' in outbox folder!\n")

def menu():
    """Main menu for the PDF utility"""
    ensure_folders_exist()
    
    while True:
        print(f"\n{Fore.MAGENTA}{'='*50}")
        print(f"{Fore.MAGENTA}           PDF UTILITY - ENHANCED VERSION")
        print(f"{Fore.MAGENTA}{'='*50}")
        print(f"{Fore.CYAN}1. {Fore.WHITE}Reduce PDF (Remove redundant pages)")
        print(f"{Fore.CYAN}2. {Fore.WHITE}Extract Pages (Multiple ranges)")
        print(f"{Fore.CYAN}3. {Fore.WHITE}Merge PDFs (Select from inbox)")
        print(f"{Fore.CYAN}4. {Fore.WHITE}Exit")
        print(f"{Fore.MAGENTA}{'='*50}")

        choice = input(f"\n{Fore.GREEN}Enter your choice (1-4): {Style.RESET_ALL}")

        if choice == '1':
            pdfs = get_pdfs_in_inbox()
            selected_pdf = display_pdfs_and_select(pdfs, "reduction")
            if selected_pdf:
                base_name = os.path.splitext(selected_pdf)[0]
                output_filename = f"reduced-{base_name}.pdf"
                print(f"\n{Fore.CYAN}Processing {selected_pdf}...")
                reduce_pdf(selected_pdf, output_filename)

        elif choice == '2':
            pdfs = get_pdfs_in_inbox()
            selected_pdf = display_pdfs_and_select(pdfs, "page extraction")
            if selected_pdf:
                print(f"\n{Fore.CYAN}Selected: {selected_pdf}")
                ranges = get_valid_ranges("Enter page ranges (e.g., '12-123,23-222' or '1-3,5,7-9')")
                print(f"\n{Fore.CYAN}Extracting pages from {selected_pdf}...")
                extract_pages_multiple_ranges(selected_pdf, ranges)

        elif choice == '3':
            pdfs = get_pdfs_in_inbox()
            if not pdfs:
                print(f"{Fore.RED}No PDF files found in '{INBOX_FOLDER}' folder!")
                continue
                
            print(f"\n{Fore.CYAN}Available PDFs for merging:")
            for i, pdf in enumerate(pdfs, 1):
                print(f"{Fore.YELLOW}{i}. {Fore.WHITE}{pdf}")
            
            ranges = get_valid_ranges(f"Enter PDF selection ranges (e.g., '1-3,5-6,7,8' from 1-{len(pdfs)})")
            output_filename = input(f"{Fore.GREEN}Enter output filename (will be saved in outbox): {Style.RESET_ALL}")
            output_filename = add_pdf_extension(output_filename)
            
            merge_pdfs_by_selection(pdfs, ranges, output_filename)

        elif choice == '4':
            print(f"{Fore.GREEN}Exiting... Thank you for using PDF Utility!")
            break
        else:
            print(f"{Fore.RED}Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    print(f"{Fore.CYAN}Welcome to Enhanced PDF Utility!")
    print(f"{Fore.YELLOW}Make sure your input PDFs are in the '{INBOX_FOLDER}' folder.")
    print(f"{Fore.YELLOW}Output files will be saved in the '{OUTBOX_FOLDER}' folder.")
    menu()
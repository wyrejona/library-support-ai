import pdfplumber

def load_pdf(path: str) -> str:
    text = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            # extract_text can return None if the page is blank/image-only
            page_text = page.extract_text()
            
            if page_text:
                # Add double newline to act as a clear section break for the chunker
                text.append(page_text.strip())
    
    # Join all pages with double newlines
    return "\n\n".join(text)

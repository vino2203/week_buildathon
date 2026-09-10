import os
import base64
from io import BytesIO
import fitz  # PyMuPDF
from PIL import Image
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

load_dotenv()

def extract_text_from_pdf(pdf_path, max_pages=2):
    # Initialize the multimodal model
    # We use gpt-4o which is OpenAI's latest multimodal vision model 
    llm = ChatOpenAI(model="gpt-4o", max_tokens=2048)
    
    print(f"Opening {pdf_path}...")
    doc = fitz.open(pdf_path)
    
    total_pages = min(max_pages, len(doc)) if max_pages else len(doc)
    extracted_text = ""
    
    for i in range(total_pages):
        print(f"Processing page {i+1}/{total_pages} with GPT-4o Vision...")
        page = doc.load_page(i)
        pix = page.get_pixmap(dpi=150)
        
        # Convert pixmap to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": "Extract all the text from this document image accurately. Return ONLY the text, with no markdown formatting or commentary."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                },
            ]
        )
        
        response = llm.invoke([message])
        extracted_text += f"\n\n--- Page {i+1} ---\n\n" + response.content
        
    doc.close()
    return extracted_text

if __name__ == "__main__":
    pdf_path = "Central_goverment_schemes/SCHEMES.pdf"
    output_path = "Central_goverment_schemes/SCHEMES_extracted.txt"
    
    # Process only the first 2 pages by default to prevent large API charges and long execution times.
    # The PDF has nearly 300 pages. To process the whole PDF, change max_pages to None.
    text = extract_text_from_pdf(pdf_path, max_pages=296)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
        
    print(f"Extraction complete! Saved to {output_path}")

# document_processor.py
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import os

# Initialize the embedding model (using a common one from Hugging Face)
# This will download the model the first time it's run.
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')

def get_text_from_url(url: str) -> str:
    """Scrapes text content from a given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract text from common elements, remove script/style
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text
    except requests.exceptions.RequestException as e:
        print(f"Error scraping URL {url}: {e}")
        return ""

def get_text_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Splits text into overlapping chunks."""
    # A simple chunking strategy; for production, consider more sophisticated methods
    # that respect sentence boundaries.
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= len(text):
            break
        start += chunk_size - chunk_overlap
    return chunks

def generate_embeddings(texts: list[str]) -> list:
    """Generates embeddings for a list of text chunks."""
    embeddings = EMBEDDING_MODEL.encode(texts, convert_to_tensor=False)
    return embeddings.tolist() # Convert numpy arrays to lists for easier storage/handling
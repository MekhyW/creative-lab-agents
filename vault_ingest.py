import os
import argparse
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

def ingest_vault(vault_path: str, chroma_path: str):
    """
    Finds all .md files in vault_path, chunks them, and stores in Chroma.
    """
    print(f"Scanning vault at: {vault_path}")
    documents = []
    for root, dirs, files in os.walk(vault_path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    loader = TextLoader(file_path, encoding='utf-8')
                    documents.extend(loader.load())
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
    print(f"Found {len(documents)} markdown files.")
    if not documents:
        print("No documents found to index.")
        return
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100, separators=["\n# ", "\n## ", "\n### ", "\n\n", "\n", " "])
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks.")
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=chroma_path)
    vectorstore.persist()
    print(f"Successfully indexed vault to {chroma_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Obsidian vault into Chroma")
    parser.add_argument("--vault", type=str, required=True, help="Path to Obsidian vault")
    parser.add_argument("--chroma", type=str, default="./chroma_db", help="Path to Chroma DB")
    args = parser.parse_args()
    ingest_vault(args.vault, args.chroma)

import os
import fitz
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

STATIC_FOLDER = "pdfs"
PDF_PATHS = [
    os.path.join(STATIC_FOLDER, f)
    for f in os.listdir(STATIC_FOLDER)
    if f.lower().endswith(".pdf")
]

class PDFRAG:
    def __init__(self, pdf_paths, openai_api_key):
        self.chunks = []
        for path in pdf_paths:
            text = self._extract_text(path)
            self.chunks += self._chunk_text(text)
            
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=openai_api_key
        )
        self.db = FAISS.from_texts(self.chunks, embeddings)

    def _extract_text(self, path):
        doc = fitz.open(path)
        return "\n".join(page.get_text() for page in doc)

    def _chunk_text(self, text):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )
        return splitter.split_text(text)

    def get_context(self, question, k=3):
        docs = self.db.similarity_search(question, k=k)
        return "\n\n---\n\n".join([d.page_content for d in docs])

app = FastAPI()

api_key = os.getenv("OPENAI_API_KEY")
rag = PDFRAG(PDF_PATHS, api_key)

class QuestionRequest(BaseModel):
    question: str

@app.post("/get_context")
async def get_context(request: QuestionRequest):
    try:
        context = rag.get_context(request.question)
        return {"context": context}
    except Exception as e:
        print(f"Error in RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import tempfile
from PyPDF2 import PdfReader
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from prompts import get_rag_prompt
import random

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment")

app = FastAPI(title="Document Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_store = None
document_info = {"files": [], "total_chars": 0}

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 4
    model: Optional[str] = "gpt-4o-mini"
    temperature: Optional[float] = 0.2

class QueryResponse(BaseModel):
    answer: str
    chunks: List[dict]

def load_pdf(file_path: str) -> str:
    with open(file_path, "rb") as f:
        reader = PdfReader(f)
        text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
        return "\n\n".join(text)

def load_excel(file_path: str) -> str:
    df = pd.read_excel(file_path, sheet_name=None)
    text = []
    for sheet_name, sheet_df in df.items():
        text.append(f"\n=== Sheet: {sheet_name} ===\n")
        text.append(sheet_df.to_string())
    return "\n\n".join(text)

def create_text_chunks(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", " ", ""],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return splitter.split_text(text)

@app.get("/")
async def root():
    return {"message": "Document Intelligence API", "status": "running"}

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    global vector_store, document_info
    
    try:
        all_texts = []
        file_names = []
        
        for file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                if file.filename.endswith('.pdf'):
                    text = load_pdf(tmp_path)
                elif file.filename.endswith(('.xlsx', '.xls')):
                    text = load_excel(tmp_path)
                else:
                    continue
                
                if text:
                    all_texts.append(f"\n\n=== File: {file.filename} ===\n\n{text}")
                    file_names.append(file.filename)
            finally:
                os.unlink(tmp_path)
        
        if not all_texts:
            raise HTTPException(status_code=400, detail="No valid files uploaded")
        
        full_text = "\n\n".join(all_texts)
        chunks = create_text_chunks(full_text)
        
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-3-small")
        vector_store = FAISS.from_texts(chunks, embeddings)
        
        document_info = {
            "files": file_names,
            "total_chars": len(full_text),
            "chunks": len(chunks)
        }
        
        return {
            "message": "Files processed successfully",
            "info": document_info
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    global vector_store
    
    if vector_store is None:
        raise HTTPException(status_code=400, detail="No documents uploaded. Please upload files first.")
    
    greetings = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]
    help_keywords = ["what can you do", "how can you help", "what are you", "who are you", "what is this", "help"]
    
    user_lower = request.question.lower().strip()
    
    if user_lower in greetings:
        greeting_responses = [
            "Hello! I am a Document Intelligence Assistant. I can help you analyze and extract information from your uploaded PDF documents. Please ask me any questions about the content of your document.",
            "Hi there! I'm here to help you understand your document better. Feel free to ask me anything about the content you've uploaded.",
            "Hey! I'm your Document Intelligence Assistant. I can answer questions based on the PDF you've provided. What would you like to know?",
            "Greetings! Ready to assist you with your document analysis. Ask me anything about the uploaded content!",
            "Hello! I specialize in analyzing PDF documents. How can I help you explore the content today?"
        ]
        return QueryResponse(answer=random.choice(greeting_responses), chunks=[])
    
    if any(keyword in user_lower for keyword in help_keywords):
        help_responses = [
            "I am a RAG-based Document Intelligence Assistant. I can help you by:\n\n- Answering questions based on your uploaded PDF document\n- Extracting specific information from the document\n- Providing summaries and explanations\n- Finding relevant sections related to your queries\n\nPlease ask me anything about the content of your uploaded document!",
            "I'm designed to help you understand your documents better! I can:\n\n- Answer specific questions about the PDF content\n- Find and extract relevant information\n- Provide context-based explanations\n- Locate specific sections in your document\n\nJust ask me about anything in your uploaded file!",
        ]
        return QueryResponse(answer=random.choice(help_responses), chunks=[])
    
    try:
        matches = vector_store.similarity_search(request.question, k=request.top_k)
        
        if not matches:
            return QueryResponse(
                answer="No relevant information found in the uploaded documents.",
                chunks=[]
            )
        
        context = "\n\n---\n\n".join(doc.page_content for doc in matches)
        prompt_text = get_rag_prompt(context, request.question)
        
        llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            temperature=request.temperature,
            max_tokens=1000,
            model_name=request.model,
        )
        
        response = llm.invoke(prompt_text)
        
        chunks_data = [
            {"content": doc.page_content, "index": i + 1}
            for i, doc in enumerate(matches)
        ]
        
        return QueryResponse(answer=response.content, chunks=chunks_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/info")
async def get_info():
    return document_info

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

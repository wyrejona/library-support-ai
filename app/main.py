from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import Query
from app.ai.retrieval import retriever
from app.ai.llm import ask_llm

app = FastAPI(title="Library AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict this to your WordPress domain in production
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Library AI Backend"}

@app.post("/ask")
def ask(query: Query):
    question = query.query.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Search directly using the retriever instance
    # UPDATED: k=10 allows us to retrieve more pages, increasing the chance
    # of finding specific examples alongside the general rules.
    chunks = retriever.search(question, k=10)
    
    if not chunks:
        return {"answer": "I could not find this information in the library materials."}

    # 2. Prepare Context
    # Add a separator so the LLM knows where one chunk ends and another begins
    context_block = "\n\n---\n\n".join(chunks)

    # 3. Generate Answer
    answer = ask_llm(context=context_block, question=question)
    
    return {"answer": answer}

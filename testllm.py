from app.ai.llm import OllamaClient
from app.utils import VectorStore, format_context

# Initialize
llm = OllamaClient()
vector_store = VectorStore()
vector_store.load()

# Search and answer
query = "How many books can undergraduate students borrow?"
results = vector_store.search(query)
context = format_context(results)
answer = llm.generate_response(query, context)
print(answer)

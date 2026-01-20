from app.ai.llm import ask_llm
import time

def run_tests():
    print("🧪 Starting Gemini LLM Test...\n")

    # 1. Define a mock context (simulating text retrieved from your PDFs)
    mock_context = """
    The library is open from 8:00 AM to 8:00 PM on weekdays.
    On Saturdays, hours are 10:00 AM to 4:00 PM.
    The library is closed on Sundays.
    
    Borrowing Policy:
    - Members can borrow up to 5 books at a time.
    - The standard loan period is 21 days.
    - Late fees are $0.50 per day per book.
    """

    # --- Test 1: Question ANSWERABLE from context ---
    question_1 = "How much are the late fees?"
    print(f"📝 Test 1: Answerable Question")
    print(f"   Q: {question_1}")
    
    start = time.time()
    answer_1 = ask_llm(context=mock_context, question=question_1)
    duration = time.time() - start
    
    print(f"   A: {answer_1}")
    print(f"   ⏱️  Time: {duration:.2f}s")
    print("-" * 50)

    # --- Test 2: Question NOT in context ---
    question_2 = "Do you have the book 'The Great Gatsby'?"
    print(f"📝 Test 2: Unanswerable Question (Hallucination Check)")
    print(f"   Q: {question_2}")
    
    answer_2 = ask_llm(context=mock_context, question=question_2)
    
    print(f"   A: {answer_2}")
    print("-" * 50)

if __name__ == "__main__":
    run_tests()

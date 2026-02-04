from app.utils import VectorStore, smart_search, format_context, query_intent_analyzer

print("🔍 Testing optimized vector store...")

vs = VectorStore()
if vs.load():
    print(f"✅ Loaded: {len(vs.metadata)} documents")
    
    # Test queries
    test_queries = [
        "What are library opening hours?",
        "How do I access past exam papers?",
        "What is plagiarism?",
        "Explain the borrowing rules",
        "List all library services"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: '{query}'")
        
        # Analyze intent
        intent = query_intent_analyzer(query)
        print(f"Intent analysis: {intent}")
        
        # Smart search
        results = smart_search(vs, query)
        print(f"Found {len(results)} results")
        
        if results:
            # Show top result
            top = results[0]
            print(f"Top result:")
            print(f"  Section: {top.get('section_path', 'N/A')}")
            print(f"  Score: {top.get('similarity_score', 0):.3f}")
            print(f"  Preview: {top['content'][:100]}...")
else:
    print("❌ Failed to load vector store")

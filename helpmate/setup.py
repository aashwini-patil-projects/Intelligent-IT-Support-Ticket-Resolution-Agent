"""
HelpMate Setup Script
Initializes the system by generating data and building FAISS index.
"""

import os
import sys

def print_step(step_num, description):
    print(f"\n{'='*70}")
    print(f"Step {step_num}: {description}")
    print('='*70)

def main():
    print("")
    print("="*70)
    print("         HelpMate System Setup")
    print("  Intelligent IT Support Ticket Resolution Agent")
    print("="*70)
    print("")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  WARNING: .env file not found!")
        print("\nPlease create a .env file with your Azure OpenAI credentials:")
        print("  1. Copy .env.template to .env")
        print("  2. Fill in your Azure OpenAI API credentials")
        print("\nRequired variables:")
        print("  - AZURE_OPENAI_API_KEY")
        print("  - AZURE_OPENAI_ENDPOINT")
        print("  - AZURE_OPENAI_DEPLOYMENT_NAME")
        print("  - AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        print("\nRun this script again after creating .env file.")
        sys.exit(1)
    
    print("[OK] Found .env file")
    
    # Step 1: Generate tickets
    print_step(1, "Generating Synthetic Ticket Dataset")
    print("Generating 150 IT support tickets with realistic distributions...")
    
    try:
        sys.path.insert(0, 'scripts')
        import generate_tickets
        print("[OK] Ticket dataset generated successfully")
    except Exception as e:
        print(f"[ERROR] Error generating tickets: {e}")
        sys.exit(1)
    
    # Step 2: Generate knowledge corpus
    print_step(2, "Generating Knowledge Corpus")
    print("Creating resolution notes and KB articles...")
    
    try:
        import generate_knowledge_corpus
        print("[OK] Knowledge corpus generated successfully")
    except Exception as e:
        print(f"[ERROR] Error generating corpus: {e}")
        sys.exit(1)
    
    # Step 3: Generate test scenarios
    print_step(3, "Generating Adaptive Test Scenarios")
    print("Creating 10 challenging test scenarios...")
    
    try:
        import generate_test_scenarios
        print("[OK] Test scenarios generated successfully")
    except Exception as e:
        print(f"[ERROR] Error generating test scenarios: {e}")
        sys.exit(1)
    
    # Step 4: Build FAISS index
    print_step(4, "Building FAISS Vector Index")
    print("This will take a few minutes as it embeds all documents...")
    print("(Embedding ~182 documents with Azure OpenAI)")
    
    try:
        sys.path.insert(0, 'core')
        from rag_system import RAGSystem
        rag = RAGSystem()
        rag.prepare_documents()
        rag.build_index()
        rag.save_index()
        print("[OK] FAISS index built and saved successfully")
    except Exception as e:
        print(f"[ERROR] Error building index: {e}")
        print("\nMake sure:")
        print("  1. Azure OpenAI credentials in .env are correct")
        print("  2. Your Azure OpenAI endpoint is accessible")
        print("  3. Embedding deployment name is correct")
        sys.exit(1)
    
    # Success
    print("\n" + "="*70)
    print("SETUP COMPLETE!")
    print("="*70)
    
    print("\nNext steps:")
    print("\n1. Run the demo for interview presentation:")
    print("   python scripts/demo.py")
    
    print("\n2. Start the FastAPI server:")
    print("   python scripts/app.py")
    
    print("\n3. Run full evaluation:")
    print("   python scripts/evaluate_agent.py")
    
    print("\n4. Process a single ticket:")
    print("   python core/helpmate_agent.py")
    
    print("\n" + "="*70)
    print("Ready for technical review!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()

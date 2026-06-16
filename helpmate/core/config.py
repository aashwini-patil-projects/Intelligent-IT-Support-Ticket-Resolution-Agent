import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Azure OpenAI
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    
    # RAG Configuration
    EMBEDDING_MODEL = "text-embedding-3-large"  # or text-embedding-3-small for cost savings
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    TOP_K_RETRIEVAL = 5
    
    # Agent Configuration
    MAX_ITERATIONS = 10
    TEMPERATURE = 0.1
    
    # Priority thresholds
    P1_REQUIRES_ESCALATION = True
    P4_AUTO_RESOLVE = True
    
    # Paths
    DATA_DIR = "data"
    TICKETS_FILE = "data/tickets.csv"
    KNOWLEDGE_CORPUS_FILE = "data/knowledge_corpus.json"
    TEST_SCENARIOS_FILE = "data/test_scenarios.json"
    FAISS_INDEX_PATH = "data/faiss_index"
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        required = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT_NAME",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
        ]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        return True

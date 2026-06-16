import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import pandas as pd
import faiss
import numpy as np
import pickle
from typing import List, Dict, Any
from openai import AzureOpenAI
from core.config import Config

class RAGSystem:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=Config.AZURE_OPENAI_API_KEY,
            api_version=Config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT
        )
        
        self.index = None
        self.documents = []
        self.metadata = []
        
    def embed_text(self, text: str) -> List[float]:
        """Generate embeddings using Azure OpenAI"""
        response = self.client.embeddings.create(
            input=text,
            model=Config.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
        )
        return response.data[0].embedding
    
    def prepare_documents(self, exclude_test_tickets=True):
        """Prepare documents from knowledge corpus and tickets"""
        documents = []
        metadata = []
        
        # Load knowledge corpus
        with open(Config.KNOWLEDGE_CORPUS_FILE, 'r') as f:
            corpus = json.load(f)
        
        # Add resolution notes
        for resolution in corpus['resolution_notes']:
            doc_text = f"""
Ticket: {resolution['ticket_id']}
Category: {resolution['category']}
Subject: {resolution['subject']}
Priority: {resolution['priority']}
Summary: {resolution['summary']}
Diagnosis: {resolution['diagnosis']}
Resolution: {resolution['resolution']}
Verification: {resolution['verification']}
Preventive Action: {resolution['preventive_action']}
            """.strip()
            
            documents.append(doc_text)
            metadata.append({
                'type': 'resolution_note',
                'ticket_id': resolution['ticket_id'],
                'category': resolution['category'],
                'priority': resolution['priority']
            })
        
        # Add KB articles
        for kb in corpus['kb_articles']:
            doc_text = f"""
KB Article: {kb['kb_id']}
Title: {kb['title']}
Category: {kb['category']}
Content: {kb['content']}
            """.strip()
            
            documents.append(doc_text)
            metadata.append({
                'type': 'kb_article',
                'kb_id': kb['kb_id'],
                'category': kb['category'],
                'title': kb['title']
            })
        
        # Load tickets (exclude test scenarios)
        tickets_df = pd.read_csv(Config.TICKETS_FILE)
        
        # Add ticket summaries for similarity search
        for _, ticket in tickets_df.iterrows():
            doc_text = f"""
Ticket: {ticket['ticket_id']}
Category: {ticket['category']}
Subject: {ticket['subject']}
Description: {ticket['description']}
Priority: {ticket['priority']}
Resolution: {ticket['resolution_code']}
Time to Resolve: {ticket['time_to_resolve_hours']} hours
            """.strip()
            
            documents.append(doc_text)
            metadata.append({
                'type': 'historical_ticket',
                'ticket_id': ticket['ticket_id'],
                'category': ticket['category'],
                'priority': ticket['priority'],
                'resolution_code': ticket['resolution_code']
            })
        
        self.documents = documents
        self.metadata = metadata
        
        print(f"Prepared {len(documents)} documents for indexing")
        print(f"  - Resolution notes: {sum(1 for m in metadata if m['type'] == 'resolution_note')}")
        print(f"  - KB articles: {sum(1 for m in metadata if m['type'] == 'kb_article')}")
        print(f"  - Historical tickets: {sum(1 for m in metadata if m['type'] == 'historical_ticket')}")
        
        return documents, metadata
    
    def build_index(self):
        """Build FAISS index from documents"""
        print("Building FAISS index...")
        
        # Generate embeddings for all documents
        embeddings = []
        for i, doc in enumerate(self.documents):
            if i % 10 == 0:
                print(f"  Embedding document {i+1}/{len(self.documents)}")
            embedding = self.embed_text(doc)
            embeddings.append(embedding)
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Create FAISS index
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array)
        
        print(f"FAISS index built with {self.index.ntotal} vectors")
        
    def save_index(self, path=None):
        """Save FAISS index and metadata"""
        if path is None:
            path = Config.FAISS_INDEX_PATH
        
        # Save FAISS index
        faiss.write_index(self.index, f"{path}.index")
        
        # Save documents and metadata
        with open(f"{path}.pkl", 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'metadata': self.metadata
            }, f)
        
        print(f"Index saved to {path}")
    
    def load_index(self, path=None):
        """Load FAISS index and metadata"""
        if path is None:
            path = Config.FAISS_INDEX_PATH
        
        # Load FAISS index
        self.index = faiss.read_index(f"{path}.index")
        
        # Load documents and metadata
        with open(f"{path}.pkl", 'rb') as f:
            data = pickle.load(f)
            self.documents = data['documents']
            self.metadata = data['metadata']
        
        print(f"Index loaded from {path}")
        print(f"  Total documents: {len(self.documents)}")
    
    def search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        if top_k is None:
            top_k = Config.TOP_K_RETRIEVAL
        
        # Generate query embedding
        query_embedding = np.array([self.embed_text(query)]).astype('float32')
        
        # Search in FAISS index
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Prepare results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                results.append({
                    'document': self.documents[idx],
                    'metadata': self.metadata[idx],
                    'distance': float(distances[0][i]),
                    'rank': i + 1
                })
        
        return results
    
    def search_by_category(self, query: str, category: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search with category filter"""
        all_results = self.search(query, top_k=top_k*3)  # Get more results to filter
        
        # Filter by category
        filtered_results = [
            r for r in all_results 
            if r['metadata'].get('category', '').lower() == category.lower()
        ]
        
        return filtered_results[:top_k or Config.TOP_K_RETRIEVAL]

if __name__ == "__main__":
    # Build and save index
    rag = RAGSystem()
    rag.prepare_documents()
    rag.build_index()
    rag.save_index()
    
    # Test retrieval
    print("\n" + "="*50)
    print("Testing retrieval...")
    results = rag.search("VPN connection timeout error", top_k=3)
    
    for i, result in enumerate(results):
        print(f"\nResult {i+1} (distance: {result['distance']:.4f}):")
        print(f"Type: {result['metadata']['type']}")
        print(f"Document preview: {result['document'][:200]}...")

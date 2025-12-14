from datetime import datetime
import json
import os

# Try to initialize ChromaDB, gracefully degrade if not available
CHROMADB_AVAILABLE = False
chroma_client = None
conversations_collection = None
data_products_collection = None

try:
    import chromadb
    from chromadb.utils import embedding_functions

    # Initialize ChromaDB with persistent storage
    chroma_client = chromadb.PersistentClient(path="./chroma_db")

    # Use ChromaDB's default embedding function
    default_ef = embedding_functions.DefaultEmbeddingFunction()

    # Collections for different purposes
    conversations_collection = chroma_client.get_or_create_collection(
        name="conversations",
        metadata={"description": "Chat conversation history"},
        embedding_function=default_ef
    )

    data_products_collection = chroma_client.get_or_create_collection(
        name="data_products",
        metadata={"description": "Data product information and insights"},
        embedding_function=default_ef
    )

    CHROMADB_AVAILABLE = True
    print("ChromaDB initialized successfully - conversation memory enabled")
except Exception as e:
    print(f"ChromaDB not available: {e}")
    print("Running without conversation memory - responses may be slower")


def store_conversation(user_message: str, assistant_response: str, metadata: dict = None):
    """Store a conversation exchange in ChromaDB"""
    if not CHROMADB_AVAILABLE:
        return None

    conversation_text = f"User: {user_message}\nAssistant: {assistant_response}"

    doc_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    meta = {
        "user_message": user_message,
        "timestamp": datetime.now().isoformat(),
        "type": "conversation"
    }
    if metadata:
        meta.update(metadata)

    try:
        # ChromaDB will auto-generate embeddings using the collection's embedding function
        conversations_collection.add(
            ids=[doc_id],
            documents=[conversation_text],
            metadatas=[meta]
        )
        return doc_id
    except Exception as e:
        print(f"Error storing conversation: {e}")
        return None


def get_relevant_conversations(query: str, n_results: int = 3) -> list:
    """Retrieve relevant past conversations based on query similarity"""
    if not CHROMADB_AVAILABLE:
        return []

    try:
        # ChromaDB will auto-generate query embedding using the collection's embedding function
        results = conversations_collection.query(
            query_texts=[query],
            n_results=n_results
        )

        conversations = []
        if results and results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                conversations.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else None
                })

        return conversations
    except Exception as e:
        print(f"Error retrieving conversations: {e}")
        return []


def store_data_product_info(product_data: dict):
    """Store data product information for context retrieval"""
    if not CHROMADB_AVAILABLE:
        return

    product_text = json.dumps(product_data, indent=2)

    doc_id = f"product_{product_data.get('id', 'unknown')}_{datetime.now().strftime('%Y%m%d')}"

    # Update or add the product info
    try:
        data_products_collection.update(
            ids=[doc_id],
            documents=[product_text],
            metadatas=[{
                "product_id": str(product_data.get('id', '')),
                "product_name": product_data.get('name', ''),
                "timestamp": datetime.now().isoformat(),
                "type": "product_data"
            }]
        )
    except:
        try:
            data_products_collection.add(
                ids=[doc_id],
                documents=[product_text],
                metadatas=[{
                    "product_id": str(product_data.get('id', '')),
                    "product_name": product_data.get('name', ''),
                    "timestamp": datetime.now().isoformat(),
                    "type": "product_data"
                }]
            )
        except Exception as e:
            print(f"Error storing product info: {e}")


def get_relevant_product_info(query: str, n_results: int = 2) -> list:
    """Retrieve relevant product information based on query"""
    if not CHROMADB_AVAILABLE:
        return []

    try:
        results = data_products_collection.query(
            query_texts=[query],
            n_results=n_results
        )

        products = []
        if results and results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                products.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                })

        return products
    except Exception as e:
        print(f"Error retrieving product info: {e}")
        return []


def get_conversation_count() -> int:
    """Get total number of stored conversations"""
    if not CHROMADB_AVAILABLE:
        return 0
    try:
        return conversations_collection.count()
    except:
        return 0


def is_available() -> bool:
    """Check if ChromaDB is available"""
    return CHROMADB_AVAILABLE


def clear_old_conversations(days: int = 30):
    """Clear conversations older than specified days"""
    # ChromaDB doesn't support date-based deletion directly
    # This would need to be implemented with metadata filtering
    pass


def persist():
    """Persist the database to disk (auto-persisted with PersistentClient)"""
    # PersistentClient auto-persists, this is a no-op for compatibility
    pass

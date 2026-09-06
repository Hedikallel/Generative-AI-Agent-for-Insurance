#!/usr/bin/env python3
"""
Configuration ChromaDB pour éviter les problèmes onnxruntime sur Windows
"""
import os
import sys
from pathlib import Path

# Configuration pour éviter les problèmes onnxruntime
CHROMA_CONFIG = {
    "path": "chroma_db",
    "anonymized_telemetry": False,
    "allow_reset": True,
    "is_http": False
}

def get_chroma_client():
    """Retourne un client ChromaDB configuré"""
    try:
        import chromadb
        
        # Configuration pour éviter onnxruntime
        client = chromadb.PersistentClient(
            path=CHROMA_CONFIG["path"],
            settings=chromadb.config.Settings(
                anonymized_telemetry=CHROMA_CONFIG["anonymized_telemetry"],
                allow_reset=CHROMA_CONFIG["allow_reset"],
                is_http=CHROMA_CONFIG["is_http"]
            )
        )
        
        return client
        
    except ImportError as e:
        print(f"❌ ChromaDB non installé: {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de ChromaDB: {e}")
        return None

def check_collections():
    """Vérifie les collections disponibles"""
    client = get_chroma_client()
    if not client:
        return []
    
    try:
        collections = client.list_collections()
        return collections
    except Exception as e:
        print(f"⚠️ Erreur lors de la vérification des collections: {e}")
        return []

def get_collection_info(collection_name="documents"):
    """Récupère les informations d'une collection"""
    client = get_chroma_client()
    if not client:
        return None
    
    try:
        collection = client.get_collection(name=collection_name)
        count = collection.count()
        
        return {
            "name": collection_name,
            "count": count,
            "status": "active"
        }
    except Exception as e:
        print(f"⚠️ Erreur lors de la récupération de la collection: {e}")
        return None

def test_chroma_connection():
    """Teste la connexion à ChromaDB"""
    print("🔍 Test de connexion à ChromaDB...")
    
    # Vérifier si le dossier existe
    if not os.path.exists(CHROMA_CONFIG["path"]):
        print(f"❌ Dossier ChromaDB non trouvé: {CHROMA_CONFIG['path']}")
        return False
    
    # Tester la connexion
    client = get_chroma_client()
    if not client:
        return False
    
    try:
        collections = client.list_collections()
        print(f"✅ Connexion réussie - {len(collections)} collections trouvées")
        
        for col in collections:
            info = get_collection_info(col.name)
            if info:
                print(f"   📚 {col.name}: {info['count']} documents")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Configuration ChromaDB")
    print("=" * 30)
    
    print(f"Chemin: {CHROMA_CONFIG['path']}")
    print(f"Télémetrie: {CHROMA_CONFIG['anonymized_telemetry']}")
    print(f"Reset autorisé: {CHROMA_CONFIG['allow_reset']}")
    
    # Test de connexion
    if test_chroma_connection():
        print("\n✅ ChromaDB fonctionne correctement")
    else:
        print("\n❌ Problème avec ChromaDB")


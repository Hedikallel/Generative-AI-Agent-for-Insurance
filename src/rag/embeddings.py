"""
Module de gestion des embeddings et de la base de données ChromaDB
"""
import os
import json
from typing import List, Dict, Any
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import pandas as pd
from loguru import logger


class EmbeddingManager:
    """Gestionnaire des embeddings pour le système RAG"""
    
    def __init__(self, db_path: str = "chroma_db", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialise le gestionnaire d'embeddings
        
        Args:
            db_path: Chemin vers la base de données ChromaDB
            model_name: Nom du modèle d'embeddings à utiliser
        """
        self.db_path = db_path
        self.model_name = model_name
        
        # Initialiser le modèle d'embeddings
        logger.info(f"Chargement du modèle d'embeddings: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)
        
        # Initialiser ChromaDB
        self._init_chromadb()
        
    def _init_chromadb(self):
        """Initialise la base de données ChromaDB"""
        try:
            # Créer le dossier s'il n'existe pas
            os.makedirs(self.db_path, exist_ok=True)
            
            # Initialiser le client ChromaDB
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Créer ou récupérer la collection
            self.collection = self.client.get_or_create_collection(
                name="banque_documents",
                metadata={"description": "Documents bancaires et conditions générales"}
            )
            
            logger.info("✅ Base de données ChromaDB initialisée avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation de ChromaDB: {e}")
            raise
    
    def create_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Découpe le texte en chunks avec overlap
        
        Args:
            text: Texte à découper
            chunk_size: Taille maximale de chaque chunk
            overlap: Nombre de caractères de chevauchement
            
        Returns:
            Liste des chunks de texte
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Si ce n'est pas le dernier chunk, essayer de couper à un espace
            if end < len(text):
                # Chercher le dernier espace dans la fenêtre
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Avancer avec overlap
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Ajoute des documents à la base de données
        
        Args:
            documents: Liste de documents avec 'text', 'metadata', 'id'
            
        Returns:
            True si succès, False sinon
        """
        try:
            texts = []
            metadatas = []
            ids = []
            
            for doc in documents:
                # Créer des chunks pour chaque document
                chunks = self.create_chunks(doc['text'])
                
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{doc['id']}_chunk_{i}"
                    texts.append(chunk)
                    metadatas.append({
                        **doc['metadata'],
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'chunk_size': len(chunk)
                    })
                    ids.append(chunk_id)
            
            # Ajouter à ChromaDB
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"✅ {len(texts)} chunks ajoutés à la base de données")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'ajout des documents: {e}")
            return False
    
    def search_similar(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche les documents les plus similaires à une requête
        
        Args:
            query: Requête de recherche
            n_results: Nombre de résultats à retourner
            
        Returns:
            Liste des documents similaires avec métadonnées
        """
        try:
            # Encoder la requête
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Rechercher dans ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Formater les résultats
            formatted_results = []
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i]
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche: {e}")
            return []
    
    def load_from_csv(self, csv_path: str) -> bool:
        """
        Charge les documents depuis un fichier CSV
        
        Args:
            csv_path: Chemin vers le fichier CSV
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Lire le CSV
            df = pd.read_csv(csv_path)
            
            # Vérifier les colonnes requises
            required_columns = ['texte', 'chemin_relatif']
            if not all(col in df.columns for col in required_columns):
                logger.error(f"❌ Colonnes manquantes dans le CSV: {required_columns}")
                return False
            
            # Préparer les documents
            documents = []
            for idx, row in df.iterrows():
                # Extraire les informations du chemin
                path_parts = row['chemin_relatif'].split('\\')  # Utiliser \\ pour Windows
                
                metadata = {
                    'source_file': path_parts[-1] if path_parts else 'unknown',
                    'category': path_parts[0] if len(path_parts) > 0 else 'unknown',
                    'subcategory': path_parts[1] if len(path_parts) > 1 else 'unknown',
                    'file_path': row['chemin_relatif'],
                    'row_index': idx
                }
                
                documents.append({
                    'id': f"doc_{idx}",
                    'text': row['texte'],
                    'metadata': metadata
                })
            
            # Ajouter à la base de données
            return self.add_documents(documents)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement depuis CSV: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Retourne les informations sur la collection"""
        try:
            count = self.collection.count()
            return {
                'total_documents': count,
                'collection_name': self.collection.name,
                'embedding_model': self.model_name
            }
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des infos: {e}")
            return {}


if __name__ == "__main__":
    # Test du module
    manager = EmbeddingManager()
    
    # Charger depuis le CSV existant
    csv_path = "src/data/texte_sans_arabe.csv"
    if os.path.exists(csv_path):
        success = manager.load_from_csv(csv_path)
        if success:
            info = manager.get_collection_info()
            print(f"✅ Base de données initialisée: {info}")
        else:
            print("❌ Erreur lors de l'initialisation")
    else:
        print(f"❌ Fichier CSV non trouvé: {csv_path}")

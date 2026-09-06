#!/usr/bin/env python3
"""
API simple pour connecter le frontend HTML au backend RAG (version légère)
Utilise pandas et recherche textuelle simple + LLM Manager existant
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import pandas as pd
import re
from difflib import SequenceMatcher

# Ajouter le chemin src au PYTHONPATH
sys.path.append(str(Path(__file__).parent / "src"))

# Modèles Pydantic
class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"

class ChatResponse(BaseModel):
    response: str

class HealthResponse(BaseModel):
    status: str
    message: str

# Initialiser FastAPI
app = FastAPI(
    title="ChatBot Bancaire API (Léger + LLM)",
    description="API simple pour le système RAG bancaire - Version avec LLM Manager",
    version="1.0.0"
)

# Configuration CORS pour permettre les requêtes depuis le frontend HTML
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifiez les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales pour le système RAG
df_documents = None
total_documents = 0
llm_manager = None
llm_available = False
catalogue_text = ""

@app.on_event("startup")
async def startup_event():
    """Initialise le système au démarrage"""
    global df_documents, total_documents, llm_manager, llm_available, catalogue_text
    
    try:
        print("🚀 Initialisation du système RAG léger avec LLM Manager...")
        
        # 1. Charger les documents depuis le CSV
        csv_path = "src/data/texte_brut.csv"
        if os.path.exists(csv_path):
            df_documents = pd.read_csv(csv_path)
            total_documents = len(df_documents)
            print(f"✅ Documents chargés: {total_documents} lignes")
            
            # Afficher un aperçu des catégories
            if 'categorie_principale' in df_documents.columns:
                categories = df_documents['categorie_principale'].value_counts()
                print("📚 Catégories disponibles:")
                for cat, count in categories.head(5).items():
                    print(f"   • {cat}: {count} documents")

                # Construire le catalogue des types de contrats
                _build_catalogue()
        else:
            print(f"❌ Fichier CSV non trouvé: {csv_path}")
        
        # 2. Initialiser le LLM Manager
        try:
            from rag.llm_manager import LLMManager
            llm_manager = LLMManager()
            
            # Tester le LLM
            if llm_manager.test_model():
                llm_available = True
                print("✅ LLM Manager initialisé et opérationnel")
            else:
                print("⚠️ LLM Manager initialisé mais test échoué")
                llm_available = False
                
        except Exception as e:
            print(f"⚠️ LLM Manager non disponible: {e}")
            print("💡 Le système fonctionnera en mode recherche uniquement")
            llm_available = False
            
        print("✅ Système RAG léger avec LLM initialisé !")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        df_documents = None

@app.get("/", response_model=HealthResponse)
async def root():
    """Point d'entrée principal"""
    return HealthResponse(
        status="success",
        message="ChatBot Bancaire API - Système RAG Léger avec LLM Manager"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Vérification de l'état de l'API"""
    if df_documents is None:
        raise HTTPException(status_code=503, detail="Système RAG non initialisé")
    
    llm_status = "✅ LLM disponible" if llm_available else "⚠️ LLM non disponible"
    
    return HealthResponse(
        status="healthy",
        message=f"Système RAG opérationnel - {total_documents} documents - {llm_status}"
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint principal pour le chat
    
    Args:
        request: Requête contenant le message de l'utilisateur
        
    Returns:
        Réponse du chatbot avec sources et niveau de confiance
    """
    if df_documents is None:
        raise HTTPException(status_code=503, detail="Système RAG non initialisé")
    
    try:
        message = request.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message vide")
        
        print(f"🔍 Question reçue: {message}")
        
        # Rechercher des documents similaires
        results = search_documents_simple(message, n_results=3)
        
        if not results:
            return ChatResponse(
                response="Je n'ai pas trouvé d'informations pertinentes pour votre question. Pouvez-vous reformuler ou poser une question plus spécifique ?"
            )
        
        # Construire la réponse basée sur les résultats
        if llm_available and llm_manager:
            # Utiliser le LLM Manager pour une réponse plus naturelle
            response = generate_llm_response(message, results)
        else:
            # Utiliser le système de fallback
            response = generate_fallback_response(message, results)
        
        # Calculer le niveau de confiance (basé sur la similarité)
        confidence = calculate_confidence(results)
        
        # Préparer les sources
        sources = prepare_sources(results)
        
        print(f"✅ Réponse générée avec confiance: {confidence:.2f}")
        
        # Retourner la réponse sans inclure le niveau de confiance
        return ChatResponse(
            response=response
        )
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

def generate_llm_response(question: str, results: List[Dict[str, Any]]) -> str:
    """Génère une réponse avec le LLM Manager existant sans inclure les sources"""
    try:
        # Formater les résultats pour le LLM Manager sans les sources
        formatted_results = []
        for result in results:
            formatted_results.append({
                'text': result.get('text', ''),
                'metadata': {}  # Supprimer les métadonnées inutiles
            })

        # Utiliser le LLM Manager
        response = llm_manager.generate_response(question, formatted_results)
        return response

    except Exception as e:
        print(f"⚠️ Erreur LLM Manager, utilisation du fallback: {e}")
        return generate_fallback_response(question, results)

def generate_fallback_response(question: str, results: List[Dict[str, Any]]) -> str:
    """Génère une réponse de fallback sans inclure les sources"""
    # Réponse basée sur la recherche textuelle (comme avant)
    question_lower = question.lower()

    if any(word in question_lower for word in ['comment', 'comment faire', 'procédure', 'étapes']):
        tone = "explicatif"
        intro = f"Excellente question ! Laissez-moi vous expliquer comment procéder pour '{question}'. "
    elif any(word in question_lower for word in ['quels', 'quelles', 'liste', 'produits', 'garanties']):
        tone = "informatif"
        intro = f"Parfait ! Voici les informations que j'ai trouvées concernant '{question}'. "
    elif any(word in question_lower for word in ['pourquoi', 'raison', 'cause']):
        tone = "analytique"
        intro = f"Très bonne question ! Laissez-moi analyser les raisons et explications pour '{question}'. "
    else:
        tone = "général"
        intro = f"Merci pour cette question intéressante ! Voici ce que je peux vous dire sur '{question}'. "

    # Construire la réponse sans inclure les sources
    response = intro
    response += "Voici les informations pertinentes extraites de nos documents :\n\n"

    for i, result in enumerate(results, 1):
        text = result.get('text', '')
        response += f"{i}. {text}\n\n"

    return response

def search_documents_simple(query: str, n_results: int = 3) -> List[Dict[str, Any]]:
    """Recherche intelligente dans les documents avec amélioration de la pertinence"""
    if df_documents is None:
        return []

    # Nettoyer et analyser la requête
    query_clean = re.sub(r'[^\w\s]', ' ', query.lower()).strip()
    query_words = set(query_clean.split())

    # Détecter les questions de type "catalogue" (quels types de contrats proposez-vous ?)
    if _is_catalogue_query(query_words) and catalogue_text:
        results = [{'text': catalogue_text, 'metadata': {'source_file': 'catalogue', 'category': 'Overview', 'subcategory': ''}, 'similarity': 1.0}]
        # Ajouter un extrait de chaque catégorie pour enrichir le contexte
        for cat, group in df_documents.groupby('sous_categorie'):
            row = group.iloc[0]
            excerpt = str(row.get('texte', ''))[:300]
            results.append({'text': excerpt, 'metadata': {'source_file': str(row.get('fichier', '')), 'category': 'Conditions Générales', 'subcategory': cat}, 'similarity': 0.7})
        return results
    
    # Mots-clés importants avec pondération
    important_keywords = {
        'assurance': 0.15,
        'vie': 0.12,
        'santé': 0.12,
        'auto': 0.10,
        'habitation': 0.10,
        'décès': 0.08,
        'invalidité': 0.08,
        'prime': 0.06,
        'garantie': 0.06,
        'contrat': 0.05,
        'sinistre': 0.05,
        'résiliation': 0.04,
        'exclusion': 0.04
    }
    
    results = []
    
    for idx, row in df_documents.iterrows():
        # Extraire le texte et les métadonnées
        text = str(row.get('texte', ''))
        if pd.isna(text) or text.strip() == '':
            continue
            
        # Nettoyer le texte
        text_clean = re.sub(r'[^\w\s]', ' ', text.lower()).strip()
        text_words = set(text_clean.split())
        
        # Calculer la similarité de base (Jaccard)
        if len(query_words.union(text_words)) > 0:
            base_similarity = len(query_words.intersection(text_words)) / len(query_words.union(text_words))
        else:
            base_similarity = 0.0
        
        # Améliorer la similarité avec des bonus intelligents
        similarity = base_similarity
        
        # 1. Bonus pour correspondances exactes de phrases
        if query_clean in text_clean:
            similarity += 0.4
        
        # 2. Bonus pour correspondances de mots dans l'ordre
        query_word_list = query_clean.split()
        if len(query_word_list) > 1:
            for i in range(len(query_word_list) - 1):
                phrase = f"{query_word_list[i]} {query_word_list[i+1]}"
                if phrase in text_clean:
                    similarity += 0.2
        
        # 3. Bonus pour mots-clés importants
        for keyword, weight in important_keywords.items():
            if keyword in query_clean and keyword in text_clean:
                similarity += weight
        
        # 4. Bonus pour la catégorie correspondante
        category = str(row.get('categorie_principale', '')).lower()
        if any(word in category for word in query_clean.split()):
            similarity += 0.1
        
        # 5. Bonus pour la longueur du texte (préférer les textes plus détaillés)
        if len(text) > 500:
            similarity += 0.05
        
        # 6. Pénalité pour les textes trop courts
        if len(text) < 100:
            similarity -= 0.1
        
        # Filtrer et formater les résultats
        if similarity > 0.02:  # Seuil minimal amélioré
            # Extraire un extrait plus intelligent
            excerpt = extract_smart_excerpt(text, query_clean, 250)
            
            results.append({
                'text': excerpt,
                'similarity': min(1.0, similarity),  # Limiter à 1.0
                'metadata': {
                    'source_file': row.get('fichier', 'Document'),
                    'category': row.get('categorie_principale', 'Général'),
                    'subcategory': row.get('sous_categorie', ''),
                    'index': idx,
                    'text_length': len(text)
                }
            })
    
    # Trier par similarité et prendre les meilleurs résultats
    results.sort(key=lambda x: x['similarity'], reverse=True)
    
    # Retourner les résultats avec un maximum intelligent
    max_results = min(n_results, len(results))
    return results[:max_results]

def _build_catalogue():
    """Construit un résumé catalogue de tous les types de contrats disponibles"""
    global catalogue_text, df_documents
    if df_documents is None:
        return
    cat_labels = {
        '1-CG-Vie': 'Assurance Vie',
        '2-CG-Santé': 'Assurance Santé / Maladie',
        '3-CG-Transport': 'Assurance Transport (maritime, terrestre, aérien)',
        '4-CG-IARD': 'Assurance IARD (Incendie, Vol, Dégâts des Eaux, Responsabilité Civile, Multirisque)',
        '5-CG-Engineering': 'Assurance Engineering (Chantiers, Montage, Responsabilité Décennale)',
        '6-CG-Automobile': 'Assurance Automobile',
    }
    lines = ["Voici les types de contrats d'assurance que nous proposons :\n"]
    for cat, group in df_documents.groupby('sous_categorie'):
        label = cat_labels.get(cat, cat)
        fichiers = [f.replace('.pdf', '') for f in group['fichier'].tolist()]
        lines.append(f"• {label} :")
        for f in fichiers:
            lines.append(f"  - {f}")
    catalogue_text = '\n'.join(lines)
    print(f"✅ Catalogue construit : {len(cat_labels)} catégories")


def _is_catalogue_query(query_words: set) -> bool:
    """Détecte si la question porte sur les types/liste de contrats disponibles"""
    catalogue_triggers = {'type', 'types', 'propose', 'proposez', 'offre', 'offrez', 'disponible', 'disponibles',
                          'catalogue', 'liste', 'quels', 'quelles', 'contrats', 'assurances', 'produits',
                          'proposer', 'offrir', 'avez'}
    assurance_anchors = {'assurance', 'assurances', 'contrat', 'contrats', 'garantie', 'garanties', 'produit', 'produits'}
    return bool(query_words & catalogue_triggers) and bool(query_words & assurance_anchors)


def extract_smart_excerpt(text: str, query: str, max_length: int = 250) -> str:
    """Extrait un extrait intelligent du texte centré sur la requête"""
    if len(text) <= max_length:
        return text
    
    # Trouver la position de la requête dans le texte
    query_lower = query.lower()
    text_lower = text.lower()
    
    # Chercher la première occurrence de la requête
    pos = text_lower.find(query_lower)
    
    if pos != -1:
        # Centrer l'extrait sur la requête
        start = max(0, pos - max_length // 2)
        end = min(len(text), start + max_length)
        
        # Ajuster pour ne pas couper au milieu des mots
        while start > 0 and text[start] != ' ':
            start += 1
        while end < len(text) and text[end] != ' ':
            end += 1
        
        excerpt = text[start:end].strip()
        
        # Ajouter des indicateurs si le texte est tronqué
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(text):
            excerpt = excerpt + "..."
        
        return excerpt
    else:
        # Si la requête n'est pas trouvée, prendre le début
        return text[:max_length] + "..."

def calculate_confidence(results: List[Dict[str, Any]]) -> float:
    """Calcule le niveau de confiance de manière intelligente et nuancée"""
    if not results:
        return 0.0
    
    # Extraire les similarités et métadonnées
    similarities = [result.get('similarity', 0.0) for result in results]
    metadata_list = [result.get('metadata', {}) for result in results]
    
    # Calculer la confiance de base
    avg_similarity = sum(similarities) / len(similarities)
    max_similarity = max(similarities)
    
    # Facteurs d'amélioration de la confiance
    confidence_boost = 0.0
    
    # 1. Bonus pour la cohérence des résultats
    if len(results) > 1:
        similarity_variance = sum((s - avg_similarity) ** 2 for s in similarities) / len(similarities)
        if similarity_variance < 0.1:  # Résultats cohérents
            confidence_boost += 0.1
    
    # 2. Bonus pour la qualité des sources
    for metadata in metadata_list:
        category = metadata.get('category', '').lower()
        if 'conditions générales' in category or 'cg' in category:
            confidence_boost += 0.05
        if metadata.get('text_length', 0) > 500:  # Textes détaillés
            confidence_boost += 0.03
    
    # 3. Bonus pour la correspondance exacte
    if max_similarity > 0.8:
        confidence_boost += 0.15
    elif max_similarity > 0.6:
        confidence_boost += 0.10
    elif max_similarity > 0.4:
        confidence_boost += 0.05
    
    # 4. Pénalité pour les résultats peu nombreux
    if len(results) == 1:
        confidence_boost -= 0.05
    
    # 5. Bonus si le LLM est disponible
    if llm_available:
        confidence_boost += 0.05
    
    # Calculer la confiance finale
    base_confidence = min(1.0, avg_similarity * 1.8)  # Ajustement plus réaliste
    final_confidence = min(1.0, base_confidence + confidence_boost)
    
    return max(0.0, final_confidence)  # S'assurer que la confiance n'est pas négative

def prepare_sources(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prépare les informations sur les sources (désactivé)"""
    # Retourner une liste vide pour ne pas inclure les sources
    return []

@app.get("/suggestions")
async def get_suggestions():
    """Retourne des suggestions de questions"""
    suggestions = [
        "Quels sont vos produits d'assurance vie ?",
        "Comment fonctionne l'assurance santé ?",
        "Quelles sont les garanties auto ?",
        "Comment faire un devis ?",
        "Quels sont les délais de carence ?",
        "Comment déclarer un sinistre ?",
        "Quelles sont les exclusions de garantie ?",
        "Comment résilier un contrat ?"
    ]
    return {"suggestions": suggestions}

@app.get("/stats")
async def get_stats():
    """Retourne des statistiques sur les documents"""
    if df_documents is None:
        raise HTTPException(status_code=503, detail="Système RAG non initialisé")
    
    stats = {
        "total_documents": total_documents,
        "categories": {},
        "llm_status": "active" if llm_available else "inactive"
    }
    
    if 'categorie_principale' in df_documents.columns:
        categories = df_documents['categorie_principale'].value_counts()
        stats["categories"] = categories.to_dict()
    
    return stats

@app.get("/llm/status")
async def llm_status():
    """Vérifie le statut du LLM"""
    return {
        "llm_available": llm_available,
        "llm_manager_loaded": llm_manager is not None,
        "status": "active" if llm_available else "inactive"
    }

@app.get("/llm/test")
async def test_llm():
    """Test simple du LLM"""
    if not llm_available or not llm_manager:
        raise HTTPException(status_code=503, detail="LLM non disponible")
    
    try:
        test_response = llm_manager.test_model()
        return {"test": "success", "llm_working": test_response}
    except Exception as e:
        return {"test": "failed", "error": str(e)}

if __name__ == "__main__":
    print("🚀 Démarrage de l'API ChatBot Bancaire (Léger + LLM)...")
    print("📱 Frontend disponible sur: http://localhost:8000")
    print("🔌 API disponible sur: http://localhost:8000/docs")
    print("🤖 LLM Manager intégré")
    
    uvicorn.run(
        "api_simple_light:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

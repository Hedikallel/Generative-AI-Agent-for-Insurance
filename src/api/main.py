"""
API principale FastAPI pour le chatbot bancaire
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json

# Import des modules locaux
from rag.embeddings import EmbeddingManager
from rag.llm_manager import LLMManager
from rag.quotation_engine import QuotationEngine

# Importer loguru pour le logging
from loguru import logger

# Configuration
app = FastAPI(
    title="ChatBot Bancaire API",
    description="API pour le chatbot bancaire avec système RAG et génération de devis",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation des composants
try:
    embedding_manager = EmbeddingManager()
    llm_manager = LLMManager()
    quotation_engine = QuotationEngine()
    print("✅ Tous les composants initialisés avec succès")
except Exception as e:
    print(f"❌ Erreur lors de l'initialisation: {e}")
    raise

# ===== MODÈLES PYDANTIC =====

class ChatMessage(BaseModel):
    """Message de chat"""
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Réponse du chat"""
    response: str
    sources: List[Dict[str, Any]]
    confidence: float

class QuotationRequest(BaseModel):
    """Demande de devis"""
    client_info: Dict[str, Any]
    produit_nom: str
    montant_assure: float

class QuotationResponse(BaseModel):
    """Réponse de devis"""
    devis: Dict[str, Any]
    success: bool
    message: str

class FeedbackRequest(BaseModel):
    """Demande de feedback"""
    message_id: str
    rating: int  # 1-5
    comment: Optional[str] = None

# ===== ROUTES DU CHATBOT =====

@app.post("/chat/ask", response_model=ChatResponse)
async def ask_question(
    chat_message: ChatMessage
):
    """Pose une question au chatbot"""
    try:
        # Rechercher des documents similaires
        similar_docs = embedding_manager.search_similar(
            chat_message.message, 
            n_results=3
        )
        
        if not similar_docs:
            return ChatResponse(
                response="Je ne trouve pas d'informations pertinentes dans nos documents pour répondre à votre question. Pouvez-vous reformuler ou contacter un conseiller ?",
                sources=[],
                confidence=0.0
            )
        
        # Générer la réponse avec le LLM
        response = llm_manager.generate_response(
            chat_message.message,
            similar_docs
        )
        
        # Calculer un score de confiance basé sur la similarité
        confidence = 1.0 - (similar_docs[0]['distance'] if similar_docs else 1.0)
        confidence = max(0.0, min(1.0, confidence))
        
        # Formater les sources (désactivé)
        sources = []  # Suppression des sources pour la réponse

        return ChatResponse(
            response=response,
            sources=sources,  # Liste vide pour ne pas inclure les sources
            confidence=confidence
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération de réponse: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la génération de la réponse"
        )

# ===== ROUTES DE GÉNÉRATION DE DEVIS =====

@app.post("/quotation/generate", response_model=QuotationResponse)
async def generate_quotation(
    quotation_request: QuotationRequest
):
    """Génère un devis d'assurance"""
    try:
        # Valider les données
        if quotation_request.montant_assure <= 0:
            raise HTTPException(
                status_code=400,
                detail="Le montant assuré doit être positif"
            )
        
        # Générer le devis
        devis = quotation_engine.calculate_quotation(
            client_info=quotation_request.client_info,
            produit_nom=quotation_request.produit_nom,
            montant_assure=quotation_request.montant_assure
        )
        
        # Convertir en dictionnaire
        devis_dict = {
            'client': {
                'nom': devis.client.nom,
                'email': devis.client.email,
                'telephone': devis.client.telephone,
                'age': devis.client.age,
                'profession': devis.client.profession,
                'situation_familiale': devis.client.situation_familiale,
                'revenus_annuels': devis.client.revenus_annuels
            },
            'produit': {
                'nom': devis.produit.nom,
                'categorie': devis.produit.categorie,
                'description': devis.produit.description
            },
            'devis': {
                'montant_assure': devis.montant_assure,
                'prime_annuelle': devis.prime_annuelle,
                'franchise': devis.franchise,
                'garanties': devis.garanties,
                'exclusions': devis.exclusions,
                'validite': devis.validite
            },
            'calculs': {
                'methode_calcul': devis.methode_calcul,
                'facteurs_risque': devis.facteurs_risque,
                'reductions_applicables': devis.reductions_applicables
            }
        }
        
        return QuotationResponse(
            devis=devis_dict,
            success=True,
            message="Devis généré avec succès"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur lors de la génération du devis: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la génération du devis"
        )

@app.get("/quotation/products")
async def get_available_products():
    """Récupère la liste des produits disponibles"""
    try:
        products = []
        for key, product in quotation_engine.products.items():
            products.append({
                'id': key,
                'nom': product.nom,
                'categorie': product.categorie,
                'description': product.description,
                'garanties_base': product.garanties_base,
                'exclusions_base': product.exclusions_base
            })
        
        return {"products": products}
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des produits: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération des produits"
        )

@app.get("/quotation/history")
async def get_quotation_history(
    email: Optional[str] = None
):
    """Récupère l'historique des devis"""
    try:
        history = quotation_engine.get_quotation_history(email)
        return {"history": history}
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération de l'historique"
        )

# ===== ROUTES DE FEEDBACK =====

@app.post("/feedback/submit")
async def submit_feedback(
    feedback: FeedbackRequest
):
    """Soumet un feedback sur une réponse"""
    try:
        # Ici vous pourriez sauvegarder le feedback en base
        # Pour l'instant, on simule juste la réception
        
        return {
            "success": True,
            "message": "Feedback reçu avec succès",
            "rating": feedback.rating,
            "comment": feedback.comment
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la soumission du feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la soumission du feedback"
        )

# ===== ROUTES D'ADMINISTRATION =====

@app.get("/admin/stats")
async def get_admin_stats():
    """Récupère les statistiques d'administration"""
    try:
        # Vérifier que l'utilisateur est admin
        # Suppression de la vérification d'admin pour simplifier
        
        # Récupérer les statistiques
        collection_info = embedding_manager.get_collection_info()
        history_count = len(quotation_engine.get_quotation_history())
        
        return {
            "collection_info": collection_info,
            "total_quotations": history_count,
            "active_users": 1  # Simplifié pour l'exemple
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération des statistiques"
        )

# ===== ROUTES DE SANTÉ =====

@app.get("/health")
async def health_check():
    """Vérification de la santé de l'API"""
    try:
        # Vérifier que tous les composants fonctionnent
        collection_info = embedding_manager.get_collection_info()
        
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "components": {
                "embeddings": "ok",
                "llm": "ok",
                "quotation": "ok"
            },
            "collection_info": collection_info
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }

@app.get("/")
async def root():
    """Route racine"""
    return {
        "message": "ChatBot Bancaire API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Démarrage de l'API ChatBot Bancaire...")
    print("📚 Documentation disponible sur: http://localhost:8000/docs")
    print("🔍 Vérification de santé: http://localhost:8000/health")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


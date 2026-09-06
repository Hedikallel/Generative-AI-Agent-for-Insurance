#!/usr/bin/env python3
"""
Configuration pour le LLM Manager du ChatBot Bancaire
"""
import os
from pathlib import Path

# Configuration du modèle LLM
LLM_CONFIG = {
    # Modèle par défaut (doit être disponible dans Ollama)
    "default_model": "gemma3:latest",
    
    # Modèles alternatifs disponibles
    "available_models": [
        "gemma3:latest",
        "llama2",
        "llama2:7b",
        "llama2:13b",
        "gemma2:2b",
        "gemma2:7b",
        "mistral:7b",
        "mistral:instruct",
        "codellama:7b",
        "neural-chat:7b"
    ],
    
    # Configuration Ollama
    "ollama": {
        "base_url": "http://localhost:11434",
        "timeout": 30,
        "temperature": 0.7,
        "max_tokens": 1000
    },
    
    # Configuration des prompts
    "prompts": {
        "system_role": "assistant bancaire professionnel",
        "language": "français",
        "tone": "professionnel et bienveillant",
        "max_context_length": 4000
    }
}

# Configuration des prompts spécialisés
SPECIALIZED_PROMPTS = {
    "assurance_vie": {
        "description": "Prompt spécialisé pour les questions d'assurance vie",
        "keywords": ["vie", "décès", "invalidité", "épargne", "retraite"],
        "context": "Expert en assurance vie et produits d'épargne"
    },
    
    "assurance_sante": {
        "description": "Prompt spécialisé pour les questions d'assurance santé",
        "keywords": ["santé", "maladie", "hospitalisation", "consultation", "médicament"],
        "context": "Expert en assurance santé et couverture médicale"
    },
    
    "assurance_auto": {
        "description": "Prompt spécialisé pour les questions d'assurance auto",
        "keywords": ["auto", "véhicule", "accident", "vol", "dégâts"],
        "context": "Expert en assurance automobile et responsabilité civile"
    },
    
    "assurance_habitation": {
        "description": "Prompt spécialisé pour les questions d'assurance habitation",
        "keywords": ["habitation", "logement", "incendie", "vol", "dégâts des eaux"],
        "context": "Expert en assurance habitation et protection du logement"
    }
}

def get_llm_config():
    """Retourne la configuration LLM"""
    return LLM_CONFIG

def get_specialized_prompts():
    """Retourne les prompts spécialisés"""
    return SPECIALIZED_PROMPTS

def check_model_availability(model_name: str = None) -> bool:
    """Vérifie si un modèle est disponible"""
    import requests
    
    if model_name is None:
        model_name = LLM_CONFIG["default_model"]
    
    try:
        response = requests.get(f"{LLM_CONFIG['ollama']['base_url']}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            for model in models:
                if model_name in model.get('name', ''):
                    return True
        return False
    except:
        return False

def get_best_available_model() -> str:
    """Retourne le meilleur modèle disponible"""
    for model in LLM_CONFIG["available_models"]:
        if check_model_availability(model):
            return model
    
    # Retourner le modèle par défaut si aucun n'est disponible
    return LLM_CONFIG["default_model"]

def update_llm_config(new_config: dict):
    """Met à jour la configuration LLM"""
    global LLM_CONFIG
    LLM_CONFIG.update(new_config)

if __name__ == "__main__":
    print("🔧 Configuration LLM Manager")
    print("=" * 30)
    
    print(f"Modèle par défaut: {LLM_CONFIG['default_model']}")
    print(f"URL Ollama: {LLM_CONFIG['ollama']['base_url']}")
    print(f"Modèles disponibles: {', '.join(LLM_CONFIG['available_models'])}")
    
    # Vérifier la disponibilité
    print(f"\n🔍 Vérification des modèles...")
    for model in LLM_CONFIG["available_models"][:5]:  # Vérifier les 5 premiers
        available = check_model_availability(model)
        status = "✅" if available else "❌"
        print(f"{status} {model}")
    
    best_model = get_best_available_model()
    print(f"\n🎯 Meilleur modèle disponible: {best_model}")


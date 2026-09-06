"""
Module de gestion du LLM pour le chatbot bancaire
"""
import os
import sys
from typing import List, Dict, Any, Optional


def _patch_pydantic_forwardref_py312() -> None:
    if sys.version_info < (3, 12):
        return

    try:
        from pydantic.v1 import typing as pydantic_v1_typing
    except Exception:
        return

    if getattr(pydantic_v1_typing, "_py312_forwardref_patch", False):
        return

    original_evaluate_forwardref = pydantic_v1_typing.evaluate_forwardref

    def evaluate_forwardref_compat(type_: Any, globalns: Any, localns: Any) -> Any:
        try:
            return original_evaluate_forwardref(type_, globalns, localns)
        except TypeError as exc:
            if "recursive_guard" not in str(exc):
                raise
            return type_._evaluate(globalns, localns, recursive_guard=set())

    pydantic_v1_typing.evaluate_forwardref = evaluate_forwardref_compat
    pydantic_v1_typing._py312_forwardref_patch = True


_patch_pydantic_forwardref_py312()

from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import SystemMessage
from loguru import logger


class LLMManager:
    """Gestionnaire du LLM pour le chatbot bancaire"""
    
    def __init__(self, model_name: str = "gemma3:latest", use_ollama: bool = True):
        """
        Initialise le gestionnaire LLM
        
        Args:
            model_name: Nom du modèle à utiliser
            use_ollama: Si True, utilise Ollama, sinon utilise un modèle local
        """
        self.model_name = model_name
        self.use_ollama = use_ollama
        
        # Initialiser le modèle
        self._init_model()
        
        # Définir les prompts
        self._init_prompts()
    
    def _init_model(self):
        """Initialise le modèle LLM"""
        try:
            if self.use_ollama:
                # Utiliser Ollama (modèle local)
                self.llm = Ollama(model=self.model_name)
                self.chat_model = ChatOllama(model=self.model_name)
                logger.info(f"✅ Modèle Ollama initialisé: {self.model_name}")
            else:
                # Ici vous pourriez ajouter d'autres modèles (OpenAI, etc.)
                raise NotImplementedError("Seul Ollama est supporté pour le moment")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation du modèle: {e}")
            raise
    
    def _init_prompts(self):
        """Initialise les templates de prompts"""
        
        # Prompt système pour le chatbot bancaire
        self.system_prompt = """Tu es un assistant bancaire professionnel et bienveillant. 
Tu as accès aux conditions générales et documents de la banque pour répondre aux questions des clients.

RÈGLES IMPORTANTES:
1. Réponds toujours en français de manière claire et professionnelle
2. Base tes réponses uniquement sur les informations fournies dans le contexte
3. Si tu ne trouves pas l'information dans le contexte, dis-le clairement
4. Ne site jamais les articles/paragraphes pertinents si le client ne le demande pas
5. Pour les questions techniques, explique de manière simple
6. Reste toujours courtois et patient avec les clients

CONTEXTE: Voici les informations pertinentes extraites de nos documents:
{context}

QUESTION DU CLIENT: {question}

Réponds de manière structurée et utile."""

        # Prompt pour la génération de devis
        self.quotation_prompt = """Tu es un expert en assurance bancaire chargé de générer des devis.

À partir des informations du client et des produits disponibles, génère un devis détaillé.

INFORMATIONS CLIENT:
{client_info}

PRODUITS DISPONIBLES:
{products_info}

Génère un devis au format JSON avec la structure suivante:
{{
    "client": {{
        "nom": "Nom du client",
        "email": "email@example.com",
        "telephone": "Numéro de téléphone"
    }},
    "produit": {{
        "nom": "Nom du produit",
        "categorie": "Catégorie du produit",
        "description": "Description du produit"
    }},
    "devis": {{
        "montant_assure": "Montant assuré",
        "prime_annuelle": "Prime annuelle calculée",
        "franchise": "Franchise applicable",
        "garanties": ["Liste des garanties"],
        "exclusions": ["Liste des exclusions principales"],
        "validite": "Durée de validité du devis"
    }},
    "calculs": {{
        "methode_calcul": "Explication de la méthode de calcul",
        "facteurs_risque": ["Facteurs de risque pris en compte"],
        "reductions_applicables": ["Réductions possibles"]
    }}
}}"""

    def generate_response(self, question: str, context: List[Dict[str, Any]]) -> str:
        """
        Génère une réponse à partir d'une question et d'un contexte
        
        Args:
            question: Question de l'utilisateur
            context: Contexte extrait de la base de données
            
        Returns:
            Réponse générée par le LLM
        """
        try:
            # Formater le contexte
            context_text = self._format_context(context)
            
            # Créer le prompt
            prompt = self.system_prompt.format(
                context=context_text,
                question=question
            )
            
            # Générer la réponse
            if hasattr(self, 'chat_model'):
                messages = [
                    SystemMessage(content=prompt)
                ]
                response = self.chat_model.invoke(messages)
                return response.content
            else:
                response = self.llm.invoke(prompt)
                return response
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération de réponse: {e}")
            return f"Désolé, une erreur s'est produite lors de la génération de la réponse. Veuillez réessayer."
    
    def generate_quotation(self, client_info: Dict[str, Any], products_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Génère un devis d'assurance
        
        Args:
            client_info: Informations sur le client
            products_info: Informations sur les produits
            
        Returns:
            Devis généré au format JSON
        """
        try:
            # Formater les informations
            client_text = self._format_client_info(client_info)
            products_text = self._format_products_info(products_info)
            
            # Créer le prompt
            prompt = self.quotation_prompt.format(
                client_info=client_text,
                products_info=products_text
            )
            
            # Générer le devis
            if hasattr(self, 'chat_model'):
                messages = [
                    SystemMessage(content=prompt)
                ]
                response = self.chat_model.invoke(messages)
                
                # Essayer de parser la réponse JSON
                try:
                    import json
                    quotation = json.loads(response.content)
                    return quotation
                except json.JSONDecodeError:
                    logger.warning("La réponse n'est pas un JSON valide, retour de la réponse brute")
                    return {
                        "error": "Erreur de formatage",
                        "raw_response": response.content
                    }
            else:
                response = self.llm.invoke(prompt)
                # Même logique pour le parsing JSON
                try:
                    import json
                    quotation = json.loads(response)
                    return quotation
                except json.JSONDecodeError:
                    return {
                        "error": "Erreur de formatage",
                        "raw_response": response
                    }
                    
        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération du devis: {e}")
            return {
                "error": f"Erreur lors de la génération du devis: {str(e)}"
            }
    
    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """Formate le contexte pour le prompt sans inclure les sources"""
        formatted_parts = []

        for i, item in enumerate(context, 1):
            formatted_parts.append(f"""
--- DOCUMENT {i} ---
Contenu:    
{item.get('text', '')}
--- FIN DOCUMENT {i} ---
""")

        return "\n".join(formatted_parts)
    
    def _format_client_info(self, client_info: Dict[str, Any]) -> str:
        """Formate les informations client pour le prompt"""
        parts = []
        for key, value in client_info.items():
            parts.append(f"{key}: {value}")
        return "\n".join(parts)
    
    def _format_products_info(self, products_info: List[Dict[str, Any]]) -> str:
        """Formate les informations produits pour le prompt"""
        formatted_parts = []
        
        for i, product in enumerate(products_info, 1):
            parts = []
            for key, value in product.items():
                parts.append(f"{key}: {value}")
            
            formatted_parts.append(f"Produit {i}:\n" + "\n".join(parts))
        
        return "\n\n".join(formatted_parts)
    
    def test_model(self) -> bool:
        """Teste si le modèle fonctionne correctement"""
        try:
            test_prompt = "Dis-moi bonjour en français"
            response = self.generate_response(test_prompt, [])
            logger.info(f"✅ Test du modèle réussi: {response[:100]}...")
            return True
        except Exception as e:
            logger.error(f"❌ Test du modèle échoué: {e}")
            return False


if __name__ == "__main__":
    # Test du module
    try:
        llm_manager = LLMManager()
        
        # Test de base
        if llm_manager.test_model():
            print("✅ Module LLM initialisé avec succès")
            
            # Test de génération de réponse
            test_context = [{
                'text': 'Ceci est un test de contexte pour le chatbot bancaire.',
                'metadata': {'source_file': 'test.pdf', 'category': 'test'}
            }]
            
            response = llm_manager.generate_response(
                "Quels sont vos produits d'assurance ?",
                test_context
            )
            print(f"✅ Réponse générée: {response[:200]}...")
        else:
            print("❌ Échec du test du modèle")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")


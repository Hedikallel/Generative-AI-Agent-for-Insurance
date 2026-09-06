# 🚀 Guide d'utilisation du LLM Manager intégré

## 🎯 **État actuel : LLM Manager CONNECTÉ !**

Votre backend est maintenant **parfaitement connecté** au LLM Manager existant ! 🎉

## 🔧 **Architecture intégrée**

```
Frontend HTML → API FastAPI → LLM Manager (Ollama) → Réponses naturelles
                    ↓
            Recherche textuelle (fallback)
```

## 🚀 **Démarrage rapide**

### **1. Démarrer le système :**
```bash
python start_simple.py
```

### **2. Choisir l'option 4** pour démarrer l'API et ouvrir le frontend

### **3. Vérifier le statut LLM :**
- **Statut :** http://localhost:8000/llm/status
- **Test :** http://localhost:8000/llm/test

## 🤖 **Fonctionnalités LLM**

### **✅ Ce qui fonctionne maintenant :**
- **Recherche intelligente** dans vos documents CSV
- **Génération de réponses naturelles** via Ollama
- **Fallback automatique** si LLM indisponible
- **Prompts spécialisés** pour chaque type d'assurance
- **Contexte intelligent** basé sur vos documents

### **🎭 Types de réponses :**
1. **Mode LLM** : Réponses naturelles et fluides
2. **Mode Fallback** : Réponses structurées par recherche textuelle

## 🔍 **Vérification du système**

### **Statut de l'API :**
```bash
curl http://localhost:8000/health
```

### **Statut du LLM :**
```bash
curl http://localhost:8000/llm/status
```

### **Test du LLM :**
```bash
curl http://localhost:8000/llm/test
```

## 📚 **Endpoints disponibles**

| Endpoint | Description | Méthode |
|----------|-------------|---------|
| `/` | Accueil | GET |
| `/health` | État du système | GET |
| `/chat` | Chat avec LLM | POST |
| `/suggestions` | Questions suggérées | GET |
| `/stats` | Statistiques documents | GET |
| `/llm/status` | Statut LLM | GET |
| `/llm/test` | Test LLM | GET |

## 🎯 **Exemple d'utilisation**

### **Question via l'API :**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Quels sont vos produits d\'assurance vie ?", "user_id": "test"}'
```

### **Réponse attendue :**
```json
{
  "response": "Réponse naturelle générée par le LLM...",
  "sources": [...],
  "confidence": 0.85
}
```

## 🔧 **Configuration avancée**

### **Modifier le modèle LLM :**
Éditez `src/rag/llm_manager.py` :
```python
self.model_name = "mistral:7b"  # Au lieu de "gemma3:1b"
```

### **Modèles disponibles :**
- `llama2` (par défaut)
- `mistral:7b`
- `gemma2:7b`
- `neural-chat:7b`

### **Installer un nouveau modèle :**
```bash
ollama pull mistral:7b
```

## 🚨 **Dépannage**

### **LLM non disponible :**
1. **Vérifier Ollama :** `ollama list`
2. **Installer un modèle :** `ollama pull llama2`
3. **Redémarrer Ollama** si nécessaire

### **Erreur d'import :**
1. **Vérifier les dépendances :** `pip install langchain langchain-community`
2. **Vérifier le chemin :** `src/rag/llm_manager.py` doit exister

### **Mode fallback activé :**
- Le système fonctionne sans LLM
- Réponses basées sur la recherche textuelle
- Vérifier les logs pour identifier le problème

## 🎉 **Avantages de l'intégration**

### **✅ Avant (sans LLM) :**
- Recherche textuelle simple
- Réponses basées sur extraction
- Pas de génération naturelle

### **🚀 Maintenant (avec LLM) :**
- **Recherche intelligente** + **Génération naturelle**
- **Fallback automatique** en cas de problème
- **Prompts spécialisés** par domaine
- **Contexte intelligent** basé sur vos documents
- **Réponses fluides** et professionnelles

## 🔮 **Prochaines étapes**

1. **Tester le système** avec différentes questions
2. **Ajuster les prompts** selon vos besoins
3. **Ajouter des modèles** spécialisés
4. **Implémenter la génération de devis** (déjà dans le LLM Manager !)

---

## 🎯 **Résumé : Votre backend est maintenant CONNECTÉ au LLM !**

- ✅ **LLM Manager intégré** et fonctionnel
- ✅ **Recherche intelligente** dans vos documents
- ✅ **Génération de réponses naturelles** via Ollama
- ✅ **Fallback automatique** si problème LLM
- ✅ **API complète** avec tous les endpoints
- ✅ **Frontend connecté** et opérationnel

**Votre ChatBot Bancaire est maintenant un vrai assistant IA ! 🚀🤖**


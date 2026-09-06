#!/usr/bin/env python3
"""
Script de démarrage simplifié pour le ChatBot Bancaire (avec LLM Manager)
"""
import os
import sys
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Vérifie les dépendances essentielles"""
    print("🔍 Vérification des dépendances...")
    
    required_packages = [
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('pandas', 'pandas')
    ]
    
    missing_packages = []
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - MANQUANT")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n❌ Packages manquants: {', '.join(missing_packages)}")
        print("📦 Installez-les avec: pip install fastapi uvicorn pandas")
        return False
    
    print("✅ Toutes les dépendances sont installées")
    return True

def check_csv_file():
    """Vérifie que le fichier CSV existe"""
    csv_path = "src/data/texte_brut.csv"
    if os.path.exists(csv_path):
        print(f"✅ Fichier CSV trouvé: {csv_path}")
        return True
    else:
        print(f"❌ Fichier CSV non trouvé: {csv_path}")
        return False

def check_llm_manager():
    """Vérifie si le LLM Manager peut être importé"""
    print("\n🤖 Vérification du LLM Manager...")
    
    try:
        # Vérifier si le module rag existe
        rag_path = "src/rag"
        if not os.path.exists(rag_path):
            print("⚠️ Module RAG non trouvé - LLM Manager non disponible")
            return False
        
        # Essayer d'importer le LLM Manager
        sys.path.append(str(Path(__file__).parent / "src"))
        from rag.llm_manager import LLMManager
        print("✅ Module LLM Manager trouvé")
        return True
        
    except ImportError as e:
        print(f"⚠️ LLM Manager non importable: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Erreur lors de la vérification: {e}")
        return False

def start_api():
    """Démarre l'API FastAPI simplifiée avec LLM"""
    print("\n🚀 Démarrage de l'API avec LLM Manager...")
    
    try:
        # Importer et démarrer l'API
        from api_simple_light import app
        import uvicorn
        
        print("✅ API avec LLM Manager importée avec succès")
        print("🌐 L'API sera disponible sur: http://localhost:8000")
        print("📚 Documentation: http://localhost:8000/docs")
        print("📊 Statistiques: http://localhost:8000/stats")
        print("🤖 Statut LLM: http://localhost:8000/llm/status")
        print("🧪 Test LLM: http://localhost:8000/llm/test")
        
        # Démarrer l'API
        uvicorn.run(
            "api_simple_light:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # Désactiver le reload pour éviter les conflits
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage de l'API: {e}")
        return False

def open_frontend():
    """Ouvre le frontend HTML dans le navigateur"""
    frontend_path = Path(__file__).parent / "frontend_simple.html"
    
    if frontend_path.exists():
        print(f"\n📱 Ouverture du frontend: {frontend_path}")
        webbrowser.open(f"file://{frontend_path.absolute()}")
        return True
    else:
        print(f"❌ Frontend non trouvé: {frontend_path}")
        return False

def test_api():
    """Teste l'API sans la démarrer"""
    print("\n🧪 Test de l'API...")
    
    try:
        # Tester l'import
        from api_simple_light import app
        print("✅ API importée avec succès")
        
        # Tester le chargement des données
        csv_path = "src/data/texte_brut.csv"
        if os.path.exists(csv_path):
            import pandas as pd
            df = pd.read_csv(csv_path)
            print(f"✅ CSV lu: {len(df)} lignes")
            
            if 'categorie_principale' in df.columns:
                categories = df['categorie_principale'].value_counts()
                print("📚 Catégories disponibles:")
                for cat, count in categories.head(3).items():
                    print(f"   • {cat}: {count} documents")
        
        # Tester le LLM Manager
        if check_llm_manager():
            print("✅ LLM Manager disponible")
        else:
            print("⚠️ LLM Manager non disponible - Mode fallback activé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def main():
    """Fonction principale"""
    print("🏦 CHATBOT BANCAIRE - Démarrage avec LLM Manager")
    print("=" * 50)
    print("🤖 Version intégrée avec LLM Manager existant")
    
    # Vérifications préalables
    if not check_dependencies():
        print("\n❌ Impossible de démarrer - dépendances manquantes")
        return 1
    
    if not check_csv_file():
        print("\n❌ Impossible de démarrer - fichier CSV manquant")
        return 1
    
    # Vérifier le LLM Manager
    llm_available = check_llm_manager()
    if llm_available:
        print("✅ LLM Manager disponible - Réponses naturelles activées")
    else:
        print("⚠️ LLM Manager non disponible - Mode recherche uniquement")
    
    print("\n✅ Toutes les vérifications sont passées")
    
    # Demander à l'utilisateur ce qu'il veut faire
    print("\n🎯 Que voulez-vous faire ?")
    print("1. Tester l'API (sans la démarrer)")
    print("2. Démarrer l'API seulement")
    print("3. Ouvrir le frontend seulement")
    print("4. Démarrer l'API et ouvrir le frontend")
    print("5. Quitter")
    
    while True:
        try:
            choice = input("\nVotre choix (1-5): ").strip()
            
            if choice == "1":
                test_api()
                break
            elif choice == "2":
                start_api()
                break
            elif choice == "3":
                open_frontend()
                print("\n💡 Pour tester le frontend, démarrez d'abord l'API avec l'option 2")
                break
            elif choice == "4":
                print("\n⏳ Démarrage en 3 secondes...")
                time.sleep(3)
                open_frontend()
                start_api()
                break
            elif choice == "5":
                print("👋 Au revoir !")
                break
            else:
                print("❌ Choix invalide. Entrez 1, 2, 3, 4 ou 5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Arrêt demandé par l'utilisateur")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
            break
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

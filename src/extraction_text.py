# extract_text.py
import pymupdf   
import os
import pandas as pd
from pathlib import Path
import pytesseract
from PIL import Image
import io
import tempfile




TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Configuration automatique de Tesseract
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    print(f"✅ Tesseract trouvé à : {TESSERACT_PATH}")
else:
    print(f"⚠️  Tesseract non trouvé à : {TESSERACT_PATH}")
    print("   Vérifiez le chemin ou laissez vide pour utiliser le PATH système")

# ===== FONCTIONS =====
def is_text_extractable(pdf_path):
    """Vérifie si le PDF contient du texte extractible directement"""
    try:
        with pymupdf.open(pdf_path) as doc:
            total_text = ""
            for page in doc:
                text = page.get_text().strip()
                total_text += text
            
            # Si on trouve du texte significatif (plus de 100 caractères lisibles)
            if len(total_text) > 100:
                # Vérifier si le texte contient des caractères lisibles
                readable_chars = sum(1 for c in total_text if c.isalnum() or c.isspace())
                if readable_chars > len(total_text) * 0.7:  # 70% de caractères lisibles
                    return True
        return False
    except Exception:
        return False

def extract_text_with_ocr(pdf_path):
    """Extrait le texte d'un PDF en utilisant l'OCR sur les images extraites avec PyMuPDF"""
    try:
        with pymupdf.open(pdf_path) as doc:
            text = ""
            total_pages = len(doc)
            
            for page_num in range(total_pages):
                page = doc[page_num]
                print(f"    🔍 Traitement OCR de la page {page_num+1}/{total_pages}")
                
                # Convertir la page entière en image pour l'OCR
                mat = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))  # Résolution 2x
                img_data = mat.tobytes("png")
                
                # Convertir en image PIL
                img = Image.open(io.BytesIO(img_data))
                
                # OCR multilingue : français + arabe pour une meilleure reconnaissance
                try:
                    # Essayer d'abord le français + arabe
                    page_text = pytesseract.image_to_string(img, lang='fra+ara')
                except:
                    try:
                        # Si ça ne marche pas, essayer français seul
                        page_text = pytesseract.image_to_string(img, lang='fra')
                    except:
                        try:
                            # Si ça ne marche pas, essayer arabe seul
                            page_text = pytesseract.image_to_string(img, lang='ara')
                        except:
                            try:
                                # En dernier recours, essayer l'anglais
                                page_text = pytesseract.image_to_string(img, lang='eng')
                            except:
                                # Dernière chance : sans spécifier de langue
                                page_text = pytesseract.image_to_string(img)
                
                text += f"\n--- Page {page_num+1} ---\n{page_text}"
            
            return text.strip()
            
    except Exception as e:
        print(f"    ❌ Erreur OCR: {e}")
        return f"ERREUR_OCR: {str(e)}"

def extract_text_from_pdf(pdf_path):
    """Extrait le texte d'un fichier PDF avec détection automatique du type"""
    try:
        print(f"    🔍 Analyse du type de PDF...")
        
        # Vérifier d'abord si le PDF contient du texte extractible
        if is_text_extractable(pdf_path):
            print(f"    ✅ PDF avec texte extractible - extraction directe")
            text = ""
            with pymupdf.open(pdf_path) as doc:
                for page in doc:
                    text += page.get_text()
            return text
        else:
            print(f"    🖼️ PDF avec images détecté - utilisation de l'OCR")
            return extract_text_with_ocr(pdf_path)
            
    except Exception as e:
        print(f"    ❌ Erreur lors de l'extraction de {pdf_path}: {e}")
        return f"ERREUR: {str(e)}"

def main():
    data = []
    base_path = Path("src/pdf")
    
    if not base_path.exists():
        print(f"❌ Le dossier {base_path} n'existe pas!")
        return
    
    print("🔍 Début de l'extraction des textes PDF...")
    
    # Parcourir récursivement tous les dossiers et sous-dossiers
    for pdf_file in base_path.rglob("*.pdf"):
        # Obtenir le chemin relatif depuis le dossier pdf
        relative_path = pdf_file.relative_to(base_path)
        
        # Déterminer la catégorie principale (premier niveau)
        if len(relative_path.parts) >= 2:
            main_category = relative_path.parts[0]
            sub_category = relative_path.parts[1] if len(relative_path.parts) > 1 else ""
            category_display = f"{main_category}/{sub_category}" if sub_category else main_category
        else:
            category_display = relative_path.parts[0] if relative_path.parts else "Racine"
        
        print(f"📄 Extraction depuis: {relative_path}")
        text = extract_text_from_pdf(str(pdf_file))
        
        # Nettoyer le texte (supprimer les espaces multiples et sauts de ligne)
        if text and not text.startswith("ERREUR"):
            text = " ".join(text.split())
        
        data.append({
            "categorie_principale": main_category if len(relative_path.parts) >= 2 else "Racine",
            "sous_categorie": sub_category if len(relative_path.parts) > 1 else "",
            "categorie_complete": category_display,
            "fichier": pdf_file.name,
            "chemin_relatif": str(relative_path),
            "chemin_complet": str(pdf_file),
            "taille_fichier_mb": round(pdf_file.stat().st_size / (1024 * 1024), 2),
            "texte": text
        })
    
    if not data:
        print("❌ Aucun fichier PDF trouvé!")
        return
    
    # Sauvegarde
    df = pd.DataFrame(data)
    output_dir = Path("src/data")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "texte_brut.csv"
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    
    print(f"\n✅ Extraction terminée!")
    print(f"📊 {len(data)} fichiers traités")
    print(f"💾 Fichier sauvegardé: {output_file}")
    
    # Aperçu des données
    print(f"\n📋 Aperçu des données extraites:")
    print(df[["categorie_complete", "fichier", "taille_fichier_mb"]].head(10))
    
    # Statistiques par catégorie
    print(f"\n📊 Statistiques par catégorie principale:")
    stats = df.groupby("categorie_principale").agg({
        "fichier": "count",
        "taille_fichier_mb": "sum"
    }).rename(columns={"fichier": "nombre_fichiers", "taille_fichier_mb": "taille_totale_mb"})
    print(stats)

if __name__ == "__main__":
    main()

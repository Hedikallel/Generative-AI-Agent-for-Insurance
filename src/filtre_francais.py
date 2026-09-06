# filtre_francais.py
import pandas as pd
import re
from pathlib import Path

def remove_arabic_characters(text):
    """
    Supprime les caractères arabes du texte et garde le reste
    """
    if not text or pd.isna(text):
        return ""
    
    text = str(text)
    
    arabic_pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
    
    # Supprimer les caractères arabes
    text_without_arabic = re.sub(arabic_pattern, '', text)
    
    # Nettoyer les espaces multiples et les lignes vides
    text_cleaned = re.sub(r'\s+', ' ', text_without_arabic).strip()
    
    return text_cleaned

def main():
    print("🔍 Début du filtrage pour supprimer les caractères arabes...")
    
    # Chemin vers le fichier CSV source
    input_file = Path("src/data/texte_brut.csv")
    
    if not input_file.exists():
        print(f"❌ Le fichier {input_file} n'existe pas!")
        print("   Assurez-vous d'avoir d'abord exécuté extraction_text.py")
        return
    
    # Lire le CSV source
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig')
        print(f"✅ Fichier CSV lu avec succès: {len(df)} lignes")
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du CSV: {e}")
        return
    
    # Créer une copie pour le filtrage
    df_filtered = df.copy()
    
    # Appliquer le filtre pour supprimer les caractères arabes sur la colonne 'texte'
    print("🔍 Suppression des caractères arabes...")
    
    for index, row in df.iterrows():
        original_text = row['texte']
        text_without_arabic = remove_arabic_characters(original_text)
        
        # Mettre à jour le texte filtré
        df_filtered.at[index, 'texte'] = text_without_arabic
        
        # Afficher le progrès
        if (index + 1) % 10 == 0:
            print(f"   📄 Traité {index + 1}/{len(df)} fichiers")
    
    # Sauvegarder le nouveau CSV
    output_file = Path("src/data/texte_sans_arabe.csv")
    output_file.parent.mkdir(exist_ok=True)
    
    try:
        df_filtered.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"✅ Fichier filtré sauvegardé: {output_file}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return
    
    print(f"\n✅ Filtrage terminé avec succès!")

if __name__ == "__main__":
    main()

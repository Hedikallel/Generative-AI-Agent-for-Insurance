"""
Module de génération de devis pour le chatbot bancaire
"""
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class Client:
    """Informations sur le client"""
    nom: str
    email: str
    telephone: str
    age: int
    profession: str
    situation_familiale: str
    revenus_annuels: float


@dataclass
class Produit:
    """Informations sur le produit d'assurance"""
    nom: str
    categorie: str
    description: str
    garanties_base: List[str]
    exclusions_base: List[str]
    prime_base: float
    franchise_base: float


@dataclass
class Devis:
    """Devis généré"""
    client: Client
    produit: Produit
    montant_assure: float
    prime_annuelle: float
    franchise: float
    garanties: List[str]
    exclusions: List[str]
    validite: str
    date_generation: str
    methode_calcul: str
    facteurs_risque: List[str]
    reductions_applicables: List[str]


class QuotationEngine:
    """Moteur de génération de devis d'assurance"""
    
    def __init__(self, db_path: str = "quotation_history.db"):
        """
        Initialise le moteur de devis
        
        Args:
            db_path: Chemin vers la base de données SQLite
        """
        self.db_path = db_path
        self._init_database()
        self._load_products()
    
    def _init_database(self):
        """Initialise la base de données SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Table des clients
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    telephone TEXT,
                    age INTEGER,
                    profession TEXT,
                    situation_familiale TEXT,
                    revenus_annuels REAL,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table des devis
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS devis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    produit_nom TEXT NOT NULL,
                    montant_assure REAL NOT NULL,
                    prime_annuelle REAL NOT NULL,
                    franchise REAL NOT NULL,
                    garanties TEXT,
                    exclusions TEXT,
                    validite TEXT,
                    date_generation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    statut TEXT DEFAULT 'generé',
                    FOREIGN KEY (client_id) REFERENCES clients (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Base de données des devis initialisée")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation de la base: {e}")
            raise
    
    def _load_products(self):
        """Charge les produits d'assurance disponibles"""
        self.products = {
            "assurance_vie": Produit(
                nom="Assurance Vie",
                categorie="Vie",
                description="Assurance vie avec épargne et protection",
                garanties_base=["Décès", "Invalidité", "Épargne"],
                exclusions_base=["Suicide dans les 2 ans", "Actes de guerre"],
                prime_base=0.5,  # 0.5% du capital
                franchise_base=0
            ),
            "assurance_sante": Produit(
                nom="Assurance Santé",
                categorie="Santé",
                description="Couverture des frais de santé",
                garanties_base=["Hospitalisation", "Consultations", "Médicaments"],
                exclusions_base=["Soins esthétiques", "Médecines alternatives"],
                prime_base=3.0,  # 3% du capital
                franchise_base=100
            ),
            "assurance_auto": Produit(
                nom="Assurance Automobile",
                categorie="Transport",
                description="Assurance tous risques véhicule",
                garanties_base=["Dommages collision", "Vol", "Responsabilité civile"],
                exclusions_base=["Conduite sous influence", "Course"],
                prime_base=2.5,  # 2.5% du capital
                franchise_base=200
            ),
            "assurance_habitation": Produit(
                nom="Assurance Habitation",
                categorie="IARD",
                description="Protection multirisque habitation",
                garanties_base=["Incendie", "Vol", "Dégâts des eaux"],
                exclusions_base=["Catastrophes naturelles", "Actes de terrorisme"],
                prime_base=1.8,  # 1.8% du capital
                franchise_base=150
            )
        }
        logger.info(f"✅ {len(self.products)} produits chargés")
    
    def calculate_quotation(self, client_info: Dict[str, Any], produit_nom: str, 
                           montant_assure: float) -> Devis:
        """
        Calcule un devis d'assurance
        
        Args:
            client_info: Informations sur le client
            produit_nom: Nom du produit demandé
            montant_assure: Montant à assurer
            
        Returns:
            Devis calculé
        """
        try:
            # Vérifier que le produit existe
            if produit_nom not in self.products:
                raise ValueError(f"Produit non trouvé: {produit_nom}")
            
            produit = self.products[produit_nom]
            
            # Créer l'objet client
            client = Client(**client_info)
            
            # Calculer la prime de base
            prime_base = (produit.prime_base / 100) * montant_assure
            
            # Appliquer les facteurs de risque
            prime_finale = self._apply_risk_factors(prime_base, client, produit)
            
            # Calculer la franchise
            franchise = self._calculate_franchise(produit.franchise_base, client, produit)
            
            # Déterminer les garanties et exclusions
            garanties = self._determine_guarantees(produit.garanties_base, client, produit)
            exclusions = self._determine_exclusions(produit.exclusions_base, client, produit)
            
            # Calculer la validité
            validite = self._calculate_validity(client, produit)
            
            # Créer le devis
            devis = Devis(
                client=client,
                produit=produit,
                montant_assure=montant_assure,
                prime_annuelle=prime_finale,
                franchise=franchise,
                garanties=garanties,
                exclusions=exclusions,
                validite=validite,
                date_generation=datetime.now().isoformat(),
                methode_calcul=self._get_calculation_method(produit),
                facteurs_risque=self._get_risk_factors(client, produit),
                reductions_applicables=self._get_applicable_reductions(client, produit)
            )
            
            # Sauvegarder le devis
            self._save_quotation(devis)
            
            logger.info(f"✅ Devis généré pour {client.nom}: {prime_finale:.2f}€")
            return devis
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du calcul du devis: {e}")
            raise
    
    def _apply_risk_factors(self, prime_base: float, client: Client, produit: Produit) -> float:
        """Applique les facteurs de risque à la prime"""
        prime = prime_base
        
        # Facteur âge
        if client.age < 25:
            prime *= 1.5  # +50% pour les jeunes conducteurs
        elif client.age > 65:
            prime *= 1.3  # +30% pour les seniors
        
        # Facteur profession
        if client.profession.lower() in ['chauffeur', 'transporteur', 'pompier']:
            prime *= 1.2  # +20% pour les professions à risque
        
        # Facteur situation familiale
        if client.situation_familiale.lower() == 'marié':
            prime *= 0.9  # -10% pour les mariés
        
        # Facteur revenus
        if client.revenus_annuels > 100000:
            prime *= 0.95  # -5% pour les hauts revenus
        
        return round(prime, 2)
    
    def _calculate_franchise(self, franchise_base: float, client: Client, produit: Produit) -> float:
        """Calcule la franchise applicable"""
        franchise = franchise_base
        
        # Réduction de franchise pour les clients fidèles (simulation)
        if client.age > 30 and client.revenus_annuels > 50000:
            franchise *= 0.8  # -20% de franchise
        
        return round(franchise, 2)
    
    def _determine_guarantees(self, garanties_base: List[str], client: Client, produit: Produit) -> List[str]:
        """Détermine les garanties applicables"""
        garanties = garanties_base.copy()
        
        # Ajouter des garanties selon le profil client
        if produit.categorie == "Vie" and client.age > 50:
            garanties.append("Garantie dépendance")
        
        if produit.categorie == "Santé" and client.situation_familiale.lower() == "marié":
            garanties.append("Garantie famille")
        
        return garanties
    
    def _determine_exclusions(self, exclusions_base: List[str], client: Client, produit: Produit) -> List[str]:
        """Détermine les exclusions applicables"""
        exclusions = exclusions_base.copy()
        
        # Ajouter des exclusions selon le profil client
        if client.profession.lower() in ['pilote', 'plongeur']:
            exclusions.append("Sports à risque")
        
        return exclusions
    
    def _calculate_validity(self, client: Client, produit: Produit) -> str:
        """Calcule la validité du devis"""
        # Validité standard : 30 jours
        validite_jours = 30
        
        # Extension pour certains profils
        if client.revenus_annuels > 100000:
            validite_jours = 45
        
        date_fin = datetime.now() + timedelta(days=validite_jours)
        return date_fin.strftime("%d/%m/%Y")
    
    def _get_calculation_method(self, produit: Produit) -> str:
        """Retourne la méthode de calcul utilisée"""
        return f"Calcul basé sur {produit.prime_base}% du capital assuré avec ajustements selon le profil client"
    
    def _get_risk_factors(self, client: Client, produit: Produit) -> List[str]:
        """Retourne les facteurs de risque identifiés"""
        facteurs = []
        
        if client.age < 25:
            facteurs.append("Âge jeune (facteur 1.5)")
        elif client.age > 65:
            facteurs.append("Âge senior (facteur 1.3)")
        
        if client.profession.lower() in ['chauffeur', 'transporteur']:
            facteurs.append("Profession à risque (facteur 1.2)")
        
        return facteurs
    
    def _get_applicable_reductions(self, client: Client, produit: Produit) -> List[str]:
        """Retourne les réductions applicables"""
        reductions = []
        
        if client.situation_familiale.lower() == 'marié':
            reductions.append("Réduction mariage (-10%)")
        
        if client.revenus_annuels > 100000:
            reductions.append("Réduction hauts revenus (-5%)")
        
        if client.age > 30 and client.revenus_annuels > 50000:
            reductions.append("Réduction franchise (-20%)")
        
        return reductions
    
    def _save_quotation(self, devis: Devis):
        """Sauvegarde le devis en base de données"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insérer ou mettre à jour le client
            cursor.execute('''
                INSERT OR REPLACE INTO clients 
                (nom, email, telephone, age, profession, situation_familiale, revenus_annuels)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                devis.client.nom, devis.client.email, devis.client.telephone,
                devis.client.age, devis.client.profession, devis.client.situation_familiale,
                devis.client.revenus_annuels
            ))
            
            client_id = cursor.lastrowid
            
            # Insérer le devis
            cursor.execute('''
                INSERT INTO devis 
                (client_id, produit_nom, montant_assure, prime_annuelle, franchise,
                 garanties, exclusions, validite)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                client_id, devis.produit.nom, devis.montant_assure,
                devis.prime_annuelle, devis.franchise,
                json.dumps(devis.garanties), json.dumps(devis.exclusions),
                devis.validite
            ))
            
            conn.commit()
            conn.close()
            logger.info("✅ Devis sauvegardé en base de données")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde: {e}")
    
    def get_quotation_history(self, email: str = None) -> List[Dict[str, Any]]:
        """Récupère l'historique des devis"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if email:
                cursor.execute('''
                    SELECT d.*, c.nom, c.email 
                    FROM devis d 
                    JOIN clients c ON d.client_id = c.id 
                    WHERE c.email = ?
                    ORDER BY d.date_generation DESC
                ''', (email,))
            else:
                cursor.execute('''
                    SELECT d.*, c.nom, c.email 
                    FROM devis d 
                    JOIN clients c ON d.client_id = c.id 
                    ORDER BY d.date_generation DESC
                ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            # Formater les résultats
            history = []
            for row in rows:
                history.append({
                    'id': row[0],
                    'client_nom': row[8],
                    'client_email': row[9],
                    'produit': row[2],
                    'montant_assure': row[3],
                    'prime_annuelle': row[4],
                    'franchise': row[5],
                    'garanties': json.loads(row[6]) if row[6] else [],
                    'exclusions': json.loads(row[7]) if row[7] else [],
                    'validite': row[8],
                    'date_generation': row[9],
                    'statut': row[10]
                })
            
            return history
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération de l'historique: {e}")
            return []
    
    def export_quotation_to_json(self, devis: Devis) -> str:
        """Exporte le devis au format JSON"""
        try:
            # Convertir le devis en dictionnaire
            devis_dict = asdict(devis)
            
            # Formater la date
            devis_dict['date_generation'] = datetime.fromisoformat(devis_dict['date_generation']).strftime("%d/%m/%Y %H:%M")
            
            return json.dumps(devis_dict, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'export JSON: {e}")
            return json.dumps({"error": str(e)})


if __name__ == "__main__":
    # Test du module
    try:
        engine = QuotationEngine()
        
        # Test de génération de devis
        client_info = {
            "nom": "Jean Dupont",
            "email": "jean.dupont@email.com",
            "telephone": "0123456789",
            "age": 35,
            "profession": "Ingénieur",
            "situation_familiale": "Marié",
            "revenus_annuels": 75000.0
        }
        
        devis = engine.calculate_quotation(
            client_info=client_info,
            produit_nom="assurance_vie",
            montant_assure=100000.0
        )
        
        print("✅ Devis généré avec succès:")
        print(f"Client: {devis.client.nom}")
        print(f"Produit: {devis.produit.nom}")
        print(f"Prime annuelle: {devis.prime_annuelle}€")
        print(f"Franchise: {devis.franchise}€")
        
        # Test export JSON
        json_export = engine.export_quotation_to_json(devis)
        print(f"\nExport JSON:\n{json_export}")
        
        # Test historique
        history = engine.get_quotation_history("jean.dupont@email.com")
        print(f"\nHistorique: {len(history)} devis trouvés")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")


"""
Module d'authentification pour l'API FastAPI
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from loguru import logger

# Configuration de sécurité
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Contexte de hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Schéma de sécurité
security = HTTPBearer()


class Token(BaseModel):
    """Schéma du token d'authentification"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Données du token décodé"""
    email: Optional[str] = None


class User(BaseModel):
    """Schéma utilisateur"""
    email: str
    nom: str
    is_active: bool = True


class UserInDB(User):
    """Utilisateur en base de données avec mot de passe hashé"""
    hashed_password: str


class UserCreate(BaseModel):
    """Schéma de création d'utilisateur"""
    email: str
    nom: str
    password: str


class UserLogin(BaseModel):
    """Schéma de connexion utilisateur"""
    email: str
    password: str


class AuthManager:
    """Gestionnaire d'authentification"""
    
    def __init__(self):
        # Base de données simulée (en production, utilisez une vraie DB)
        self.users_db = {
            "admin@banque.com": {
                "email": "admin@banque.com",
                "nom": "Administrateur",
                "hashed_password": self.get_password_hash("admin123"),
                "is_active": True
            },
            "conseiller@banque.com": {
                "email": "conseiller@banque.com",
                "nom": "Conseiller Client",
                "hashed_password": self.get_password_hash("conseiller123"),
                "is_active": True
            }
        }
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Vérifie un mot de passe"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash un mot de passe"""
        return pwd_context.hash(password)
    
    def get_user(self, email: str) -> Optional[UserInDB]:
        """Récupère un utilisateur par email"""
        if email in self.users_db:
            user_dict = self.users_db[email]
            return UserInDB(**user_dict)
        return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authentifie un utilisateur"""
        user = self.get_user(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Crée un token d'accès JWT"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Vérifie et décode un token JWT"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                return None
            token_data = TokenData(email=email)
            return token_data
        except JWTError:
            return None
    
    def create_user(self, user_create: UserCreate) -> User:
        """Crée un nouvel utilisateur"""
        if user_create.email in self.users_db:
            raise HTTPException(
                status_code=400,
                detail="Un utilisateur avec cet email existe déjà"
            )
        
        hashed_password = self.get_password_hash(user_create.password)
        user_dict = {
            "email": user_create.email,
            "nom": user_create.nom,
            "hashed_password": hashed_password,
            "is_active": True
        }
        
        self.users_db[user_create.email] = user_dict
        return User(email=user_create.email, nom=user_create.nom)


# Instance globale du gestionnaire d'authentification
auth_manager = AuthManager()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dépendance pour récupérer l'utilisateur courant"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        token_data = auth_manager.verify_token(token)
        if token_data is None:
            raise credentials_exception
        
        email = token_data.email
        if email is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = auth_manager.get_user(email=email)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dépendance pour récupérer l'utilisateur actif courant"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Utilisateur inactif")
    return current_user


def create_user_access_token(data: dict) -> str:
    """Crée un token d'accès pour un utilisateur"""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return auth_manager.create_access_token(
        data=data, expires_delta=access_token_expires
    )


if __name__ == "__main__":
    # Test du module d'authentification
    try:
        # Test de création d'utilisateur
        user_create = UserCreate(
            email="test@example.com",
            nom="Utilisateur Test",
            password="password123"
        )
        
        user = auth_manager.create_user(user_create)
        print(f"✅ Utilisateur créé: {user.nom}")
        
        # Test d'authentification
        user_auth = auth_manager.authenticate_user("test@example.com", "password123")
        if user_auth:
            print(f"✅ Authentification réussie: {user_auth.nom}")
            
            # Test de création de token
            token = create_user_access_token(data={"sub": user_auth.email})
            print(f"✅ Token créé: {token[:50]}...")
            
            # Test de vérification de token
            token_data = auth_manager.verify_token(token)
            if token_data:
                print(f"✅ Token vérifié pour: {token_data.email}")
            else:
                print("❌ Échec de vérification du token")
        else:
            print("❌ Échec de l'authentification")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")


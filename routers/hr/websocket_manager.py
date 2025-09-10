from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
from datetime import datetime

class HRWebSocketManager:
    def __init__(self):
        # Dictionnaire pour stocker les connexions par company_id
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Dictionnaire pour stocker les connexions par user_id
        self.user_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, company_id: int, user_id: int):
        """Connecter un utilisateur au WebSocket"""
        await websocket.accept()
        
        # Ajouter la connexion à la liste de l'entreprise
        if company_id not in self.active_connections:
            self.active_connections[company_id] = []
        self.active_connections[company_id].append(websocket)
        
        # Ajouter la connexion utilisateur
        self.user_connections[user_id] = websocket
        
        print(f"User {user_id} connected to HR WebSocket for company {company_id}")
        
        # Envoyer un message de bienvenue
        await self.send_personal_message({
            "type": "connection_established",
            "message": "Connexion WebSocket établie",
            "timestamp": datetime.now().isoformat()
        }, user_id)

    def disconnect(self, websocket: WebSocket, company_id: int, user_id: int):
        """Déconnecter un utilisateur du WebSocket"""
        # Retirer de la liste de l'entreprise
        if company_id in self.active_connections:
            if websocket in self.active_connections[company_id]:
                self.active_connections[company_id].remove(websocket)
            if not self.active_connections[company_id]:
                del self.active_connections[company_id]
        
        # Retirer de la liste des utilisateurs
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        
        print(f"User {user_id} disconnected from HR WebSocket for company {company_id}")

    async def send_personal_message(self, message: dict, user_id: int):
        """Envoyer un message à un utilisateur spécifique"""
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_text(json.dumps(message))
                return True
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
                return False
        return False

    async def broadcast_to_company(self, message: dict, company_id: int):
        """Diffuser un message à tous les utilisateurs d'une entreprise"""
        if company_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[company_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    print(f"Error broadcasting to company {company_id}: {e}")
                    disconnected.append(websocket)
            
            # Nettoyer les connexions défaillantes
            for websocket in disconnected:
                self.active_connections[company_id].remove(websocket)

    async def broadcast_job_created(self, job_data: dict, company_id: int):
        """Diffuser un nouveau job créé"""
        message = {
            "type": "job_created",
            "job": job_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_company(message, company_id)

    async def broadcast_job_updated(self, job_data: dict, company_id: int):
        """Diffuser un job mis à jour"""
        message = {
            "type": "job_updated",
            "job": job_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_company(message, company_id)

    async def broadcast_job_deleted(self, job_id: int, company_id: int):
        """Diffuser la suppression d'un job"""
        message = {
            "type": "job_deleted",
            "job_id": job_id,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_company(message, company_id)

    async def broadcast_dashboard_stats(self, stats: dict, company_id: int):
        """Diffuser les statistiques du dashboard"""
        message = {
            "type": "dashboard_stats_updated",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_company(message, company_id)

# Instance globale du gestionnaire WebSocket
hr_websocket_manager = HRWebSocketManager()

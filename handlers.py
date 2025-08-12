from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import logging
from datetime import datetime
from typing import Dict, Any

from ..database import get_db
from ..core.auth import get_current_user_websocket
from ..models.user import User
from ..models.survey import Survey
from ..models.response import SurveyResponse
from .connection_manager import manager

logger = logging.getLogger(__name__)

class WebSocketEventHandler:
    """Handles WebSocket events and messages"""
    
    def __init__(self):
        self.event_handlers = {
            'subscribe_survey': self.handle_subscribe_survey,
            'unsubscribe_survey': self.handle_unsubscribe_survey,
            'join_room': self.handle_join_room,
            'leave_room': self.handle_leave_room,
            'survey_response_update': self.handle_survey_response_update,
            'dashboard_refresh': self.handle_dashboard_refresh,
            'ping': self.handle_ping
        }
    
    async def handle_message(self, websocket: WebSocket, message: str, user: User, db: Session):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            event_type = data.get('type')
            payload = data.get('payload', {})
            
            if event_type in self.event_handlers:
                await self.event_handlers[event_type](websocket, payload, user, db)
            else:
                await self.send_error(websocket, f"Unknown event type: {event_type}")
                
        except json.JSONDecodeError:
            await self.send_error(websocket, "Invalid JSON message")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self.send_error(websocket, "Internal server error")
    
    async def handle_subscribe_survey(self, websocket: WebSocket, payload: Dict, user: User, db: Session):
        """Handle survey subscription"""
        survey_id = payload.get('survey_id')
        
        if not survey_id:
            await self.send_error(websocket, "survey_id is required")
            return
        
        # Check if survey exists and user has access
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            await self.send_error(websocket, "Survey not found")
            return
        
        # Check permissions
        if survey.creator_id != user.id and user.role not in ["admin", "analyst"]:
            await self.send_error(websocket, "Not authorized to monitor this survey")
            return
        
        # Subscribe to survey updates
        manager.subscribe_to_survey(websocket, survey_id)
        
        # Send confirmation
        await manager.send_personal_message({
            'type': 'subscription_confirmed',
            'survey_id': survey_id,
            'survey_title': survey.title,
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)
        
        # Send current survey stats
        await self.send_survey_stats(websocket, survey_id, db)
    
    async def handle_unsubscribe_survey(self, websocket: WebSocket, payload: Dict, user: User, db: Session):
        """Handle survey unsubscription"""
        survey_id = payload.get('survey_id')
        
        if not survey_id:
            await self.send_error(websocket, "survey_id is required")
            return
        
        manager.unsubscribe_from_survey(websocket, survey_id)
        
        await manager.send_personal_message({
            'type': 'unsubscription_confirmed',
            'survey_id': survey_id,
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)
    
    async def handle_join_room(self, websocket: WebSocket, payload: Dict, user: User, db: Session):
        """Handle joining a room/channel"""
        room_id = payload.get('room_id')
        
        if not room_id:
            await self.send_error(websocket, "room_id is required")
            return
        
        # Add to room
        if room_id not in manager.room_connections:
            manager.room_connections[room_id] = set()
        manager.room_connections[room_id].add(websocket)
        
        # Update connection metadata
        if websocket in manager.connection_metadata:
            manager.connection_metadata[websocket]['room_id'] = room_id
        
        await manager.send_personal_message({
            'type': 'room_joined',
            'room_id': room_id,
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)
        
        # Notify others in the room
        await manager.send_to_room({
            'type': 'user_joined_room',
            'user_id': user.id,
            'username': user.username,
            'room_id': room_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room_id)
    
    async def handle_leave_room(self, websocket: WebSocket, payload: Dict, user: User, db: Session):
        """Handle leaving a room/channel"""
        room_id = payload.get('room_id')
        
        if not room_id:
            await self.send_error(websocket, "room_id is required")
            return
        
        # Remove from room
        if room_id in manager.room_connections:
            manager.room_connections[room_id].discard(websocket)
            
            if not manager.room_connections[room_id]:
                del manager.room_connections[room_id]
        
        await manager.send_personal_message({
            'type': 'room_left',
            'room_id': room_id,
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)
        
        # Notify others in the room
        if room_id in manager.room_connections:
            await manager.send_to_room({
                'type': 'user_left_room',
                'user_id': user.id,
                'username': user.username,
                'room_id': room_id,
                'timestamp': datetime.utcnow().isoformat()
            }, room_id)
    
    async def handle_survey_response_update(self, websocket: WebSocket, payload: Dict, user: User, db: Session):
        """Handle survey response updates"""
        survey_id = payload.get('survey_id')
        response_data = payload.get('response_data', {})
        
        if not survey_id:
            await self.send_error(websocket, "survey_id is required")
            return
        
        # Get survey
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            await self.send_error(websocket, "Survey not found")
            return
        
        # Broadcast update to survey subscribers
        await manager.send_to_survey({
            'type': 'survey_response_received',
            'survey_id': survey_id,
            'response_preview': {
                'user_id': user.id,
                'timestamp': datetime.utcnow().isoformat(),
                'field_count': len(response_data),
                'is_complete': payload.get('is_complete', False)
            }
        }, survey_id)
        
        # Send updated stats
        await self.send_survey_stats_to_subscribers(survey_id, db)
    
    async def handle_dashboard_refresh(self, websocket: WebSocket, payload: Dict, user: User, db: Session):
        """Handle dashboard refresh requests"""
        dashboard_type = payload.get('dashboard_type', 'general')
        
        # Send current dashboard data
        dashboard_data = await self.get_dashboard_data(user, db, dashboard_type)
        
        await manager.send_personal_message({
            'type': 'dashboard_data',
            'dashboard_type': dashboard_type,
            'data': dashboard_data,
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)
    
    async def handle_ping(self, websocket: WebSocket, payload: Dict, user: User, db: Session):
        """Handle ping messages"""
        await manager.send_personal_message({
            'type': 'pong',
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)
    
    async def send_error(self, websocket: WebSocket, message: str):
        """Send error message to WebSocket"""
        await manager.send_personal_message({
            'type': 'error',
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)
    
    async def send_survey_stats(self, websocket: WebSocket, survey_id: int, db: Session):
        """Send current survey statistics"""
        stats = await self.get_survey_stats(survey_id, db)
        
        await manager.send_personal_message({
            'type': 'survey_stats',
            'survey_id': survey_id,
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)
    
    async def send_survey_stats_to_subscribers(self, survey_id: int, db: Session):
        """Send survey stats to all subscribers"""
        stats = await self.get_survey_stats(survey_id, db)
        
        await manager.send_to_survey({
            'type': 'survey_stats_update',
            'survey_id': survey_id,
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat()
        }, survey_id)
    
    async def get_survey_stats(self, survey_id: int, db: Session) -> Dict:
        """Get current survey statistics"""
        try:
            # Get response count
            total_responses = db.query(SurveyResponse).filter(
                SurveyResponse.survey_id == survey_id
            ).count()
            
            # Get completed responses
            completed_responses = db.query(SurveyResponse).filter(
                SurveyResponse.survey_id == survey_id,
                SurveyResponse.is_complete == True
            ).count()
            
            # Get recent responses (last hour)
            from datetime import timedelta
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            recent_responses = db.query(SurveyResponse).filter(
                SurveyResponse.survey_id == survey_id,
                SurveyResponse.created_at >= recent_cutoff
            ).count()
            
            # Calculate completion rate
            completion_rate = (completed_responses / total_responses * 100) if total_responses > 0 else 0
            
            return {
                'total_responses': total_responses,
                'completed_responses': completed_responses,
                'completion_rate': round(completion_rate, 2),
                'recent_responses': recent_responses,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting survey stats: {e}")
            return {
                'error': 'Failed to get survey statistics',
                'last_updated': datetime.utcnow().isoformat()
            }
    
    async def get_dashboard_data(self, user: User, db: Session, dashboard_type: str) -> Dict:
        """Get dashboard data for real-time updates"""
        try:
            if dashboard_type == 'general':
                # Get user's surveys
                user_surveys = db.query(Survey).filter(Survey.creator_id == user.id).count()
                
                # Get total responses for user's surveys
                total_responses = db.query(SurveyResponse).join(Survey).filter(
                    Survey.creator_id == user.id
                ).count()
                
                return {
                    'user_surveys': user_surveys,
                    'total_responses': total_responses,
                    'user_role': user.role
                }
            
            elif dashboard_type == 'analytics':
                # Get analytics data
                return {
                    'active_surveys': db.query(Survey).filter(Survey.status == 'published').count(),
                    'total_users': db.query(User).count()
                }
            
            else:
                return {'message': f'Dashboard type {dashboard_type} not implemented'}
                
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {'error': 'Failed to get dashboard data'}

# Global event handler instance
event_handler = WebSocketEventHandler()

# Notification functions for triggering real-time updates
async def notify_survey_response_created(survey_id: int, response_data: Dict, db: Session):
    """Notify subscribers when a new survey response is created"""
    await manager.send_to_survey({
        'type': 'new_survey_response',
        'survey_id': survey_id,
        'response_preview': {
            'timestamp': datetime.utcnow().isoformat(),
            'field_count': len(response_data.get('data', {})),
            'is_complete': response_data.get('is_complete', False)
        }
    }, survey_id)
    
    # Send updated stats
    await event_handler.send_survey_stats_to_subscribers(survey_id, db)

async def notify_survey_updated(survey_id: int, update_data: Dict):
    """Notify subscribers when a survey is updated"""
    await manager.send_to_survey({
        'type': 'survey_updated',
        'survey_id': survey_id,
        'updates': update_data,
        'timestamp': datetime.utcnow().isoformat()
    }, survey_id)

async def notify_dashboard_update(room_id: str, update_data: Dict):
    """Notify dashboard subscribers of updates"""
    await manager.send_to_room({
        'type': 'dashboard_update',
        'data': update_data,
        'timestamp': datetime.utcnow().isoformat()
    }, room_id)

async def broadcast_system_notification(message: str, notification_type: str = "info"):
    """Broadcast system-wide notifications"""
    await manager.broadcast({
        'type': 'system_notification',
        'notification_type': notification_type,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    })


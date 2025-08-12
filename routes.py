from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
import logging
from typing import Optional

from ..database import get_db
from ..core.auth import get_current_user_websocket
from ..models.user import User
from .connection_manager import manager
from .handlers import event_handler

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    connection_type: str = Query("general"),
    room_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Main WebSocket endpoint for real-time communication
    
    Parameters:
    - token: JWT token for authentication
    - connection_type: Type of connection (general, survey, dashboard)
    - room_id: Optional room/channel ID to join
    """
    
    # Authenticate user
    try:
        user = await get_current_user_websocket(token, db)
        if not user:
            await websocket.close(code=4001, reason="Authentication failed")
            return
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        return
    
    # Connect to WebSocket
    await manager.connect(websocket, user.id, connection_type, room_id)
    
    try:
        while True:
            # Wait for messages
            data = await websocket.receive_text()
            
            # Handle the message
            await event_handler.handle_message(websocket, data, user, db)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user.id}: {e}")
    finally:
        # Clean up connection
        manager.disconnect(websocket)

@router.websocket("/ws/survey/{survey_id}")
async def survey_websocket_endpoint(
    websocket: WebSocket,
    survey_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint specifically for survey monitoring
    """
    
    # Authenticate user
    try:
        user = await get_current_user_websocket(token, db)
        if not user:
            await websocket.close(code=4001, reason="Authentication failed")
            return
    except Exception as e:
        logger.error(f"Survey WebSocket authentication error: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        return
    
    # Connect to WebSocket
    await manager.connect(websocket, user.id, "survey", f"survey_{survey_id}")
    
    # Subscribe to survey updates
    manager.subscribe_to_survey(websocket, survey_id)
    
    try:
        # Send initial survey stats
        await event_handler.send_survey_stats(websocket, survey_id, db)
        
        while True:
            # Wait for messages
            data = await websocket.receive_text()
            
            # Handle the message
            await event_handler.handle_message(websocket, data, user, db)
            
    except WebSocketDisconnect:
        logger.info(f"Survey WebSocket disconnected for user {user.id}, survey {survey_id}")
    except Exception as e:
        logger.error(f"Survey WebSocket error for user {user.id}, survey {survey_id}: {e}")
    finally:
        # Clean up connection
        manager.unsubscribe_from_survey(websocket, survey_id)
        manager.disconnect(websocket)

@router.websocket("/ws/dashboard")
async def dashboard_websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    dashboard_type: str = Query("general"),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for dashboard real-time updates
    """
    
    # Authenticate user
    try:
        user = await get_current_user_websocket(token, db)
        if not user:
            await websocket.close(code=4001, reason="Authentication failed")
            return
    except Exception as e:
        logger.error(f"Dashboard WebSocket authentication error: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        return
    
    # Connect to WebSocket
    room_id = f"dashboard_{dashboard_type}"
    await manager.connect(websocket, user.id, "dashboard", room_id)
    
    try:
        # Send initial dashboard data
        dashboard_data = await event_handler.get_dashboard_data(user, db, dashboard_type)
        await manager.send_personal_message({
            'type': 'dashboard_data',
            'dashboard_type': dashboard_type,
            'data': dashboard_data,
            'timestamp': event_handler.datetime.utcnow().isoformat()
        }, websocket)
        
        while True:
            # Wait for messages
            data = await websocket.receive_text()
            
            # Handle the message
            await event_handler.handle_message(websocket, data, user, db)
            
    except WebSocketDisconnect:
        logger.info(f"Dashboard WebSocket disconnected for user {user.id}")
    except Exception as e:
        logger.error(f"Dashboard WebSocket error for user {user.id}: {e}")
    finally:
        # Clean up connection
        manager.disconnect(websocket)

# REST endpoints for WebSocket management
@router.get("/ws/stats")
async def get_websocket_stats(
    current_user: User = Depends(get_current_user_websocket)
):
    """Get WebSocket connection statistics"""
    if current_user.role not in ["admin", "analyst"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return manager.get_connection_stats()

@router.post("/ws/broadcast")
async def broadcast_message(
    message: str,
    notification_type: str = "info",
    current_user: User = Depends(get_current_user_websocket)
):
    """Broadcast a message to all connected users (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from .handlers import broadcast_system_notification
    await broadcast_system_notification(message, notification_type)
    
    return {"message": "Broadcast sent successfully"}

@router.post("/ws/notify-survey/{survey_id}")
async def notify_survey_update(
    survey_id: int,
    update_data: dict,
    current_user: User = Depends(get_current_user_websocket),
    db: Session = Depends(get_db)
):
    """Send notification to survey subscribers"""
    # Check if user has access to the survey
    from ..models.survey import Survey
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    if survey.creator_id != current_user.id and current_user.role not in ["admin", "analyst"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    from .handlers import notify_survey_updated
    await notify_survey_updated(survey_id, update_data)
    
    return {"message": "Survey notification sent successfully"}


# WebSocket Manager for Real-time Booking Updates
# This module handles WebSocket connections for live booking status updates

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from .database import get_week_db

logger = logging.getLogger("booking.websocket")


class WebSocketManager:
    def __init__(self):
        # Store active connections by date subscription
        self.connections: Dict[str, Set[WebSocket]] = {}
        # Store all active connections
        self.active_connections: Set[WebSocket] = set()
        # Connection metadata for better management
        self.connection_metadata: Dict[WebSocket, Dict] = {}
        # Rate limiting
        self.message_timestamps: Dict[WebSocket, list] = {}
        self.max_messages_per_minute = 60

    def _rate_limit_check(self, websocket: WebSocket) -> bool:
        """Check if websocket is within rate limits"""
        now = datetime.now().timestamp()
        if websocket not in self.message_timestamps:
            self.message_timestamps[websocket] = []
        
        # Clean old timestamps (older than 1 minute)
        self.message_timestamps[websocket] = [
            ts for ts in self.message_timestamps[websocket] 
            if now - ts < 60
        ]
        
        # Check rate limit
        if len(self.message_timestamps[websocket]) >= self.max_messages_per_minute:
            return False
        
        self.message_timestamps[websocket].append(now)
        return True

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection with enhanced error handling"""
        print(f"🟡 Accepting WebSocket connection...")
        try:
            await websocket.accept()
            print(f"🟢 WebSocket accepted successfully")
            self.active_connections.add(websocket)
            
            # Initialize connection metadata
            self.connection_metadata[websocket] = {
                "connected_at": datetime.now(),
                "last_activity": datetime.now(),
                "subscribed_dates": set(),
                "message_count": 0
            }
            
            total = len(self.active_connections)
            logger.info(f"New WebSocket connection established. Total: {total}")
            print(f"📊 Total active connections: {total}")
            
        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection: {e}")
            print(f"🔴 Failed to accept WebSocket connection: {e}")
            raise

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection with cleanup"""
        self.active_connections.discard(websocket)

        # Remove from date subscriptions
        for date, connections in self.connections.items():
            connections.discard(websocket)

        # Clean up empty date subscriptions
        self.connections = {
            date: connections
            for date, connections in self.connections.items()
            if connections
        }
        
        # Clean up metadata and rate limiting data
        self.connection_metadata.pop(websocket, None)
        self.message_timestamps.pop(websocket, None)

        total = len(self.active_connections)
        logger.info(f"WebSocket connection removed. Total: {total}")

    def subscribe_to_date(self, websocket: WebSocket, date: str):
        """Subscribe a connection to updates for a specific date"""
        if date not in self.connections:
            self.connections[date] = set()
        self.connections[date].add(websocket)
        
        # Update metadata
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["subscribed_dates"].add(date)
        
        logger.info(f"WebSocket subscribed to date {date}")

    async def send_to_date_subscribers(self, date: str, message: dict):
        """Send a message to all connections subscribed to a specific date with batching"""
        if date not in self.connections:
            return

        # Add timestamp and performance metadata
        message["timestamp"] = datetime.now().isoformat()
        message["server_time"] = datetime.now().timestamp()

        # Batch send for better performance
        disconnected = set()
        send_tasks = []
        
        for websocket in self.connections[date]:
            try:
                # Check if connection is still valid
                if websocket in self.active_connections:
                    task = asyncio.create_task(websocket.send_text(json.dumps(message)))
                    send_tasks.append((websocket, task))
                else:
                    disconnected.add(websocket)
            except Exception as e:
                logger.warning(f"Failed to queue message for WebSocket: {e}")
                disconnected.add(websocket)

        # Wait for all sends to complete
        for websocket, task in send_tasks:
            try:
                await task
                # Update activity timestamp
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["last_activity"] = datetime.now()
                    self.connection_metadata[websocket]["message_count"] += 1
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected WebSockets
        for websocket in disconnected:
            self.disconnect(websocket)
            
    async def send_to_all(self, message: dict):
        """Send a message to all active connections with performance optimization"""
        if not self.active_connections:
            return
            
        message["timestamp"] = datetime.now().isoformat()
        message["server_time"] = datetime.now().timestamp()
        
        disconnected = set()
        send_tasks = []
        
        for websocket in self.active_connections.copy():
            try:
                task = asyncio.create_task(websocket.send_text(json.dumps(message)))
                send_tasks.append((websocket, task))
            except Exception as e:
                logger.warning(f"Failed to queue message for WebSocket: {e}")
                disconnected.add(websocket)
        
        # Wait for all sends with timeout
        for websocket, task in send_tasks:
            try:
                await asyncio.wait_for(task, timeout=5.0)  # 5 second timeout
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["last_activity"] = datetime.now()
                    self.connection_metadata[websocket]["message_count"] += 1
            except asyncio.TimeoutError:
                logger.warning(f"WebSocket send timeout")
                disconnected.add(websocket)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected WebSockets
        for websocket in disconnected:
            self.disconnect(websocket)
            
    async def handle_message(self, websocket: WebSocket, data: dict):
        """Handle incoming WebSocket messages with rate limiting and validation"""
        
        # Rate limiting
        if not self._rate_limit_check(websocket):
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Rate limit exceeded",
                "timestamp": datetime.now().isoformat()
            }))
            return
        
        message_type = data.get("type")
        
        if message_type == "subscribe":
            date = data.get("date")
            if date:
                # Validate date format
                try:
                    datetime.strptime(date, "%Y-%m-%d")
                    self.subscribe_to_date(websocket, date)
                    
                    # Send current availability status
                    try:
                        availability = self.get_current_availability(date)
                        await websocket.send_text(json.dumps({
                            "type": "availability_snapshot",
                            "date": date,
                            "availability": availability,
                            "timestamp": datetime.now().isoformat()
                        }))
                    except Exception as e:
                        logger.error(f"Failed to send availability snapshot: {e}")
                except ValueError:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid date format. Use YYYY-MM-DD",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
        elif message_type == "ping":
            # Respond to heartbeat
            await websocket.send_text(json.dumps({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }))
            
        elif message_type == "get_stats":
            # Send connection statistics (for debugging)
            stats = {
                "type": "stats",
                "total_connections": len(self.active_connections),
                "subscribed_dates": list(self.connections.keys()),
                "your_subscriptions": list(self.connection_metadata.get(websocket, {}).get("subscribed_dates", [])),
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(stats))
        else:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Unknown message type: {message_type}",
                "timestamp": datetime.now().isoformat()
            }))

    def get_current_availability(self, date: str) -> dict:
        """Get current availability for a date"""
        try:
            conn = get_week_db(date)
            c = conn.cursor()
            c.execute(
                "SELECT time_slot, COUNT(*) as count FROM bookings WHERE date = ? GROUP BY time_slot",
                (date,)
            )
            slots = {row["time_slot"]: row["count"] for row in c.fetchall()}
            
            all_slots = ['12:00 PM', '3:00 PM', '6:00 PM', '9:00 PM']
            result = {}
            for slot in all_slots:
                count = slots.get(slot, 0)
                if count == 0:
                    status = "available"
                elif count == 1:
                    status = "waiting"
                else:
                    status = "booked"
                result[slot] = {"status": status, "count": count}
            
            return result
        except Exception as e:
            logger.error(f"Failed to get availability for {date}: {e}")
            return {}
            
    async def notify_availability_change(self, date: str, time_slot: str, new_status: str):
        """Notify subscribers about availability changes"""
        await self.send_to_date_subscribers(date, {
            "type": "availability_update",
            "date": date,
            "timeSlot": time_slot,
            "status": new_status
        })
        
    async def notify_booking_conflict(self, date: str, time_slot: str):
        """Notify about booking conflicts"""
        await self.send_to_date_subscribers(date, {
            "type": "booking_conflict",
            "date": date,
            "timeSlot": time_slot
        })
        
    async def notify_waitlist_update(self, date: str, time_slot: str, position: int = None, slot_opened: bool = False):
        """Notify about waitlist updates"""
        await self.send_to_date_subscribers(date, {
            "type": "waitlist_update",
            "date": date,
            "timeSlot": time_slot,
            "position": position,
            "slotOpened": slot_opened
        })
        
    async def notify_system_maintenance(self, message: str):
        """Notify all users about system maintenance"""
        await self.send_to_all({
            "type": "system_maintenance",
            "message": message
        })

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint handler"""
    print("🟡 WebSocket connection attempt received")
    
    try:
        await websocket_manager.connect(websocket)
        print("🟢 WebSocket connection accepted successfully")
    except Exception as e:
        print(f"🔴 Failed to accept WebSocket connection: {e}")
        return
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            print(f"📨 Received WebSocket message: {data}")
            
            try:
                message = json.loads(data)
                await websocket_manager.handle_message(websocket, message)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from WebSocket: {data}")
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected normally")
        print("🟡 WebSocket disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        print(f"🔴 WebSocket error: {e}")
    finally:
        websocket_manager.disconnect(websocket)
        print("🔵 WebSocket cleanup completed")

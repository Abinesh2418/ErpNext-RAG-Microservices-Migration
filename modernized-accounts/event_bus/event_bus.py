from typing import Callable, Dict, List, Any
from datetime import datetime
import json
import os


class EventBus:
    """
    In-memory event bus for managing event subscriptions and publications.
    
    This is a simplified event bus suitable for prototyping and demonstrations.
    In production, this would be replaced by a message broker like RabbitMQ or Kafka.
    """
    
    def __init__(self):
        """Initialize the event bus with an empty subscribers dictionary."""
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_log: List[Dict[str, Any]] = []
        self._log_file = os.path.join(os.path.dirname(__file__), 'event_logs.json')
    
    def subscribe(self, event_name: str, handler: Callable) -> None:
        """
        Subscribe a handler function to an event.
        """
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        
        self._subscribers[event_name].append(handler)
        print(f"✓ Subscriber registered for event: {event_name}")
    
    def publish(self, event_name: str, payload: Dict[str, Any]) -> None:
        """
        Publish an event to all registered subscribers.
        """
        timestamp = datetime.now().isoformat()
        
        # Create log entry
        log_entry = {
            "event": event_name,
            "timestamp": timestamp,
            "payload": payload
        }
        
        # Log the event
        self._event_log.append(log_entry)
        
        # Save to JSON file
        self._save_log_to_file(log_entry)
        
        print(f"\n{'='*70}")
        print(f"📤 EVENT PUBLISHED: {event_name}")
        print(f"   Timestamp: {timestamp}")
        print(f"   Payload: {payload}")
        print(f"{'='*70}\n")
        
        # Call all registered handlers for this event
        if event_name in self._subscribers:
            for handler in self._subscribers[event_name]:
                try:
                    handler(payload)
                except Exception as e:
                    print(f"❌ Error executing handler: {e}")
        else:
            print(f"⚠ No subscribers found for event: {event_name}")
    
    def get_event_log(self) -> List[Dict[str, Any]]:
        """
        Get the log of all published events.
        
        Returns:
            List[Dict]: A list of published events with timestamps and payloads
        """
        return self._event_log
    
    def clear_subscribers(self, event_name: str = None) -> None:
        """
        Clear all subscribers for an event, or all events.
        
        Args:
            event_name (str, optional): Specific event to clear. If None, clears all.
        """
        if event_name:
            if event_name in self._subscribers:
                del self._subscribers[event_name]
        else:
            self._subscribers.clear()
    
    def _save_log_to_file(self, log_entry: Dict[str, Any]) -> None:
        """
        Append log entry to JSON file.
        
        Args:
            log_entry (Dict[str, Any]): The log entry to save
        """
        try:
            # Read existing logs
            if os.path.exists(self._log_file):
                with open(self._log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # Append new log
            logs.append(log_entry)
            
            # Write back to file
            with open(self._log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Warning: Could not save event log to file: {e}")


# Global event bus instance (Singleton pattern for simplicity)
_event_bus = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# Convenience functions for quick access
def subscribe(event_name: str, handler: Callable) -> None:
    """Subscribe to an event using the global event bus."""
    get_event_bus().subscribe(event_name, handler)


def publish(event_name: str, payload: Dict[str, Any]) -> None:
    """Publish an event using the global event bus."""
    get_event_bus().publish(event_name, payload)

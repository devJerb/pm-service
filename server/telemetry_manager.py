"""
Telemetry manager for PM Service AI Assistant.

Handles comprehensive telemetry tracking including LangSmith integration,
cost calculation, and Supabase persistence for analytics.
"""

import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .config import get_langsmith_client, initialize_langsmith_tracing
from .supabase_client import get_supabase_client


@dataclass
class TelemetryEvent:
    """Data class for telemetry events."""
    chat_id: str
    category: str
    ai_mode: str
    latency_ms: float
    tokens_used: int
    estimated_cost_usd: float
    model_name: str
    status: str  # 'success' or 'error'
    error_message: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class TelemetryCollector:
    """
    Collects and manages telemetry data for AI interactions.
    
    Handles LangSmith integration, cost calculation, and Supabase persistence.
    """
    
    def __init__(self):
        """Initialize telemetry collector with clients."""
        self.supabase = get_supabase_client()
        self.langsmith_client = None
        self.session_events: List[TelemetryEvent] = []
        
        # Initialize LangSmith if available
        try:
            if initialize_langsmith_tracing():
                self.langsmith_client = get_langsmith_client()
        except Exception:
            # LangSmith not available, continue without it
            pass
    
    def calculate_cost(self, tokens_used: int, model_name: str = "gemini-flash-latest") -> float:
        """
        Calculate estimated cost based on token usage and model.
        
        Args:
            tokens_used: Number of tokens used
            model_name: Name of the model used
            
        Returns:
            float: Estimated cost in USD
        """
        # Gemini pricing (as of 2024) - adjust as needed
        pricing = {
            "gemini-flash-latest": 0.000002,  # $2 per 1M tokens
            "gemini-1.5-pro": 0.0000035,      # $3.5 per 1M tokens
            "gemini-1.5-flash": 0.000002,     # $2 per 1M tokens
        }
        
        cost_per_token = pricing.get(model_name, 0.000002)  # Default to flash pricing
        return tokens_used * cost_per_token
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        
        Args:
            text: Input text
            
        Returns:
            int: Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters for English text
        return max(1, len(text) // 4)
    
    def track_event(
        self,
        chat_id: str,
        category: str,
        ai_mode: str,
        latency_ms: float,
        input_text: str,
        response_text: str = "",
        model_name: str = "gemini-flash-latest",
        status: str = "success",
        error_message: Optional[str] = None
    ) -> TelemetryEvent:
        """
        Track a telemetry event.
        
        Args:
            chat_id: Chat session identifier
            category: Work category (Lease & Contracts, etc.)
            ai_mode: AI mode (Chat, Draft, Plan, Ask)
            latency_ms: Response latency in milliseconds
            input_text: User input text
            response_text: AI response text
            model_name: Model used
            status: Event status ('success' or 'error')
            error_message: Error message if status is 'error'
            
        Returns:
            TelemetryEvent: Created telemetry event
        """
        # Calculate token usage
        input_tokens = self.estimate_tokens(input_text)
        response_tokens = self.estimate_tokens(response_text) if response_text else 0
        total_tokens = input_tokens + response_tokens
        
        # Calculate cost
        estimated_cost = self.calculate_cost(total_tokens, model_name)
        
        # Create telemetry event
        event = TelemetryEvent(
            chat_id=chat_id,
            category=category,
            ai_mode=ai_mode,
            latency_ms=latency_ms,
            tokens_used=total_tokens,
            estimated_cost_usd=estimated_cost,
            model_name=model_name,
            status=status,
            error_message=error_message
        )
        
        # Store in session
        self.session_events.append(event)
        
        # Persist to Supabase
        self._persist_to_supabase(event)
        
        return event
    
    def _persist_to_supabase(self, event: TelemetryEvent):
        """Persist telemetry event to Supabase."""
        try:
            event_data = asdict(event)
            event_data['timestamp'] = datetime.fromtimestamp(event.timestamp).isoformat()
            
            self.supabase.table("telemetry_events").insert(event_data).execute()
        except Exception as e:
            # Log error but don't fail the main operation
            print(f"Failed to persist telemetry event: {e}")
    
    def get_session_metrics(self) -> Dict[str, Any]:
        """
        Get aggregated metrics for the current session.
        
        Returns:
            Dict containing session metrics
        """
        if not self.session_events:
            return {
                "total_messages": 0,
                "avg_latency_ms": 0,
                "total_tokens": 0,
                "total_cost_usd": 0,
                "success_rate": 0,
                "category_distribution": {},
                "ai_mode_distribution": {},
                "error_count": 0
            }
        
        total_messages = len(self.session_events)
        successful_events = [e for e in self.session_events if e.status == "success"]
        error_events = [e for e in self.session_events if e.status == "error"]
        
        avg_latency = sum(e.latency_ms for e in successful_events) / len(successful_events) if successful_events else 0
        total_tokens = sum(e.tokens_used for e in self.session_events)
        total_cost = sum(e.estimated_cost_usd for e in self.session_events)
        success_rate = (len(successful_events) / total_messages * 100) if total_messages > 0 else 0
        
        # Category distribution
        category_dist = {}
        for event in self.session_events:
            category_dist[event.category] = category_dist.get(event.category, 0) + 1
        
        # AI mode distribution
        ai_mode_dist = {}
        for event in self.session_events:
            ai_mode_dist[event.ai_mode] = ai_mode_dist.get(event.ai_mode, 0) + 1
        
        return {
            "total_messages": total_messages,
            "avg_latency_ms": round(avg_latency, 2),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "success_rate": round(success_rate, 1),
            "category_distribution": category_dist,
            "ai_mode_distribution": ai_mode_dist,
            "error_count": len(error_events)
        }
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent telemetry activity.
        
        Args:
            limit: Maximum number of recent events to return
            
        Returns:
            List of recent activity records
        """
        try:
            # Get recent events from Supabase
            response = self.supabase.table("telemetry_events")\
                .select("chat_id, category, ai_mode, latency_ms, status, timestamp")\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            
            activities = []
            for event in response.data:
                activities.append({
                    "time": datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00")).strftime("%I:%M %p"),
                    "action": f"{event['ai_mode']} Message",
                    "details": f"{event['category']} - {event['latency_ms']:.1f}ms",
                    "status": event["status"]
                })
            
            return activities
        except Exception:
            # Fallback to session events if Supabase fails
            recent_events = sorted(self.session_events, key=lambda x: x.timestamp, reverse=True)[:limit]
            activities = []
            for event in recent_events:
                activities.append({
                    "time": datetime.fromtimestamp(event.timestamp).strftime("%I:%M %p"),
                    "action": f"{event.ai_mode} Message",
                    "details": f"{event.category} - {event.latency_ms:.1f}ms",
                    "status": event.status
                })
            return activities
    
    def get_performance_chart_data(self, hours: int = 3) -> Dict[str, List]:
        """
        Get performance chart data for the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dict with chart data
        """
        try:
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Get events from Supabase
            response = self.supabase.table("telemetry_events")\
                .select("latency_ms, tokens_used, timestamp")\
                .gte("timestamp", start_time.isoformat())\
                .order("timestamp")\
                .execute()
            
            # Group by hour
            hourly_data = {}
            for event in response.data:
                event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                hour = event_time.hour
                
                if hour not in hourly_data:
                    hourly_data[hour] = {"messages": 0, "latency": [], "tokens": 0}
                
                hourly_data[hour]["messages"] += 1
                hourly_data[hour]["latency"].append(event["latency_ms"])
                hourly_data[hour]["tokens"] += event["tokens_used"]
            
            # Format for chart
            hours_list = []
            messages_list = []
            latency_list = []
            
            for hour in sorted(hourly_data.keys()):
                hours_list.append(hour)
                messages_list.append(hourly_data[hour]["messages"])
                avg_latency = sum(hourly_data[hour]["latency"]) / len(hourly_data[hour]["latency"])
                latency_list.append(round(avg_latency, 1))
            
            return {
                "hours": hours_list,
                "messages": messages_list,
                "latency": latency_list
            }
        except Exception:
            # Fallback to session data
            return {
                "hours": [datetime.now().hour],
                "messages": [len(self.session_events)],
                "latency": [self.get_session_metrics()["avg_latency_ms"]]
            }
    
    def clear_session_data(self):
        """Clear session telemetry data."""
        self.session_events.clear()


# Global telemetry collector instance
_telemetry_collector = None


def get_telemetry_collector() -> TelemetryCollector:
    """Get the global telemetry collector instance."""
    global _telemetry_collector
    if _telemetry_collector is None:
        _telemetry_collector = TelemetryCollector()
    return _telemetry_collector

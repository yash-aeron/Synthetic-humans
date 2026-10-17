import asyncio
import json
import logging
from typing import Dict, Set, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class SimulationEventBus:
    """
    Asynchronous in-memory pub-sub event bus for real-time simulation streaming.
    Supports Server-Sent Events (SSE) connections from multiple concurrent dashboard clients.
    """

    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, experiment_id: str) -> asyncio.Queue:
        """Register a new listener queue for an experiment's telemetry stream."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            if experiment_id not in self._subscribers:
                self._subscribers[experiment_id] = set()
            self._subscribers[experiment_id].add(queue)
        logger.debug(f"Subscribed queue to experiment {experiment_id} (total listeners: {len(self._subscribers[experiment_id])})")
        return queue

    async def unsubscribe(self, experiment_id: str, queue: asyncio.Queue):
        """Remove a listener queue."""
        async with self._lock:
            if experiment_id in self._subscribers:
                self._subscribers[experiment_id].discard(queue)
                if not self._subscribers[experiment_id]:
                    del self._subscribers[experiment_id]
        logger.debug(f"Unsubscribed queue from experiment {experiment_id}")

    async def publish(self, experiment_id: str, event_data: Dict[str, Any]):
        """Broadcast an event to all active subscribers of the experiment."""
        event_data.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        event_data.setdefault("experiment_id", experiment_id)

        async with self._lock:
            listeners = list(self._subscribers.get(experiment_id, set()))

        for q in listeners:
            try:
                # Non-blocking put; drop oldest event if client buffer is full to prevent backpressure
                if q.full():
                    try:
                        q.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                q.put_nowait(event_data)
            except Exception as e:
                logger.debug(f"Failed to deliver event to subscriber queue: {e}")

# Global singleton event bus
event_bus = SimulationEventBus()

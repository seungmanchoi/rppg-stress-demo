import asyncio
from collections import defaultdict
from typing import Any


class EventBus:
    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, jid: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues[jid].append(q)
        return q

    def unsubscribe(self, jid: str, q: asyncio.Queue) -> None:
        if q in self._queues[jid]:
            self._queues[jid].remove(q)

    async def publish(self, jid: str, event: dict[str, Any]) -> None:
        for q in list(self._queues[jid]):
            await q.put(event)


bus = EventBus()

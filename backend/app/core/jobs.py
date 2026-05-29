import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Job:
    id: str
    status: str = "queued"
    progress: float = 0.0
    stage: str = ""
    created_at: float = field(default_factory=time.time)
    result: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = asyncio.Lock()

    async def create(self) -> Job:
        async with self._lock:
            j = Job(id=uuid.uuid4().hex)
            self._jobs[j.id] = j
            return j

    def get(self, jid: str) -> Job | None:
        return self._jobs.get(jid)

    async def update(self, jid: str, **kwargs) -> None:
        async with self._lock:
            j = self._jobs.get(jid)
            if not j:
                return
            for k, v in kwargs.items():
                setattr(j, k, v)

    async def delete(self, jid: str) -> None:
        async with self._lock:
            self._jobs.pop(jid, None)

    async def cleanup(self, ttl: float = 3600.0) -> None:
        now = time.time()
        async with self._lock:
            for k in list(self._jobs):
                if now - self._jobs[k].created_at > ttl:
                    del self._jobs[k]


store = JobStore()

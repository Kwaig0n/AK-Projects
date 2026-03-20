"""In-memory SSE event bus keyed by run_id."""
import asyncio
import json
from datetime import datetime
from collections import defaultdict


# run_id -> asyncio.Queue of log entry dicts
_run_queues: dict[str, asyncio.Queue] = defaultdict(lambda: asyncio.Queue(maxsize=500))


def emit_log(run_id: str, level: str, message: str) -> None:
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "message": message,
    }
    try:
        _run_queues[run_id].put_nowait(entry)
    except asyncio.QueueFull:
        pass  # Drop if queue full — run is being consumed too slowly


async def stream_logs(run_id: str):
    """AsyncGenerator that yields SSE-formatted strings for a run."""
    queue = _run_queues[run_id]
    while True:
        try:
            entry = await asyncio.wait_for(queue.get(), timeout=30.0)
            yield f"data: {json.dumps(entry)}\n\n"
            if entry.get("level") == "done":
                break
        except asyncio.TimeoutError:
            yield 'data: {"type":"heartbeat"}\n\n'


def cleanup_run(run_id: str) -> None:
    _run_queues.pop(run_id, None)

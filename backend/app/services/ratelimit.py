"""In-memory sliding-window limits (NFR-10). Swap for Redis when running >1 process."""
import time
from collections import defaultdict, deque

from ..errors import ApiError

_hits: dict[str, deque] = defaultdict(deque)


def check(bucket: str, key: str, limit: int, window_s: int = 3600) -> None:
    q = _hits[f"{bucket}:{key}"]
    t = time.monotonic()
    while q and t - q[0] > window_s:
        q.popleft()
    if len(q) >= limit:
        raise ApiError("rate_limited", f"Bạn đã đạt giới hạn {limit} lượt/giờ. Vui lòng thử lại sau.")
    q.append(t)


def reset() -> None:
    _hits.clear()

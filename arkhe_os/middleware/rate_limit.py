from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import numpy as np

# Limiter based on remote address
limiter = Limiter(key_func=get_remote_address)

def get_dynamic_rate_limit(request: Request) -> str:
    """
    Returns a rate limit string that adapts to the system's coherence.
    Higher coherence (M > 0.95) allows more requests.
    """
    scaffold = getattr(request.app.state, 'scaffold', None)
    m = scaffold.coherence_M if scaffold else 0.92

    if m > 0.95:
        return "1000/minute"
    elif m > 0.85:
        return "100/minute"
    else:
        return "10/minute"

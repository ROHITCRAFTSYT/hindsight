"""Vercel Python entrypoint.

Vercel's Python runtime looks for a module-level ASGI/WSGI variable named
`app`. Our real FastAPI app lives in backend/app/main.py as part of a regular
package (backend/app/), so this file just puts backend/ on the import path
and re-exports it.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

"""Vercel ASGI entrypoint.

Keep this thin so the existing FastAPI app, UI, and search behavior continue
to live in app.py.
"""

from app import app

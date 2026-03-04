"""Root-level entry point — forwards to the app package.

The canonical application now lives in ``app/main.py``.
This file exists for backward compatibility with uvicorn invocations
that still reference ``main:app``.

Start the server with either:
    uvicorn main:app --reload          # old style (still works)
    uvicorn app.main:app --reload      # new canonical style
"""
from app.main import app as app  # noqa: F401

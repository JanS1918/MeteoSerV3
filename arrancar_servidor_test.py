#!/usr/bin/env python
"""Arranca servidor MeteoSer para testing."""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main_asgi:app",
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )

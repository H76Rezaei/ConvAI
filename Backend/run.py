#!/usr/bin/env python3
"""
Startup script for FastAPI Chat Backend
"""

import os
import uvicorn

if __name__ == "__main__":
    # Use environment variables for deployment
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    
    print(f"Starting FastAPI Chat Backend")
    print(f"Running on http://{host}:{port}")
    print(f"Debug mode: {debug}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )
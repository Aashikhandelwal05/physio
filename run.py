#!/usr/bin/env python3
"""
Simple startup script for the Physio Prescription Manager
"""
import uvicorn

if __name__ == "__main__":
    print("Starting Physio Prescription Manager...")
    print("Open your browser and go to: http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "app:app",  # Must be string import path when reload=True
        host="127.0.0.1", 
        port=8000, 
        reload=True,
        log_level="info"
    )
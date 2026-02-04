import os
import subprocess
import asyncio
import json
from typing import List
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LYNK Test Lab")

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root directory of the project
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@app.get("/api/tests")
async def list_tests():
    """Discover all pytest files in the tests/ directory and categorize them."""
    tests_dir = os.path.join(ROOT_DIR, "tests")
    test_files = []
    
    # Category mapping for better display
    category_map = {
        "core": "Core Engine",
        "telemetry": "Data Flow & Analytics",
        "ack": "Reliability & Handshakes",
        "command": "Robot Command Center",
        "integration": "System Full Flow",
        "comm": "Comm Interface",
        "tests": "Security & Common"
    }

    for root, dirs, files in os.walk(tests_dir):
        # Ignore pycache
        if "__pycache__" in root:
            continue
            
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, ROOT_DIR)
                cat_key = os.path.basename(root)
                
                is_critical = any(kw in file for kw in ["crypto", "security", "stress", "resilience"]) or "integration" in rel_path
                
                # Special categorization based on filename if it's in the root 'tests' dir
                category = category_map.get(cat_key, cat_key.capitalize())
                if cat_key == "tests":
                    if "stress" in file or "security" in file:
                        category = "Security & Stress"
                    elif "resilience" in file or "routing" in file or "wrap" in file:
                        category = "Core Engine"

                test_files.append({
                    "name": file,
                    "path": rel_path,
                    "category": category,
                    "is_critical": is_critical
                })
    
    return sorted(test_files, key=lambda x: (x["category"], x["name"]))

@app.get("/api/run/{test_name:path}")
async def run_test(test_name: str):
    """Run a specific test and stream the output."""
    test_path = os.path.join(ROOT_DIR, test_name)
    
    async def event_generator():
        # Start pytest process
        process = await asyncio.create_subprocess_exec(
            "pytest", "-v", test_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=ROOT_DIR
        )

        yield f"data: {json.dumps({'type': 'status', 'msg': 'STARTED'})}\n\n"

        while True:
            line = await process.stdout.readline()
            if not line:
                break
            
            decoded_line = line.decode().strip()
            if decoded_line:
                yield f"data: {json.dumps({'type': 'log', 'msg': decoded_line})}\n\n"

        await process.wait()
        status = "PASSED" if process.returncode == 0 else "FAILED"
        yield f"data: {json.dumps({'type': 'status', 'msg': status, 'code': process.returncode})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Serve static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

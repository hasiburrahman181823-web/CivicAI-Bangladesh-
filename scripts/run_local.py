"""Run the packaged web application on the local machine."""
import argparse
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port",type=int,default=8000)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    if not (root/"dist/index.html").is_file():
        raise SystemExit("Build the frontend with npm ci and npm run build first.")
    os.chdir(root)
    sys.path.insert(0,str(root))
    import uvicorn
    uvicorn.run("backend.app.main:app",host="127.0.0.1",port=args.port)

import os
import sys
import tempfile
import subprocess
import shutil
import glob
import threading
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Report Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScriptPayload(BaseModel):
    python_code: str
    output_filename: str = "Rapport_Diagnostic.docx"


@app.post("/generate")
async def generate_report(payload: ScriptPayload):
    work_dir = tempfile.mkdtemp(prefix="report_")

    try:
        script_path = os.path.join(work_dir, "generate_report.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(payload.python_code)

        result = subprocess.run(
            [sys.executable, script_path],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Script execution failed",
                    "stderr": result.stderr[-2000:],
                    "stdout": result.stdout[-1000:],
                }
            )

        docx_files = glob.glob(os.path.join(work_dir, "*.docx"))

        if not docx_files:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "No .docx file was generated",
                    "stdout": result.stdout[-1000:],
                    "files_in_dir": os.listdir(work_dir),
                }
            )

        docx_path = docx_files[0]
        file_size = os.path.getsize(docx_path)
        print(f"Generated: {os.path.basename(docx_path)} ({file_size/1024:.1f} KB)")

        return FileResponse(
            path=docx_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=payload.output_filename,
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Script timed out (120s)")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        def cleanup():
            time.sleep(5)
            shutil.rmtree(work_dir, ignore_errors=True)
        threading.Thread(target=cleanup, daemon=True).start()


@app.get("/health")
async def health():
    return {"status": "ok", "message": "Report Generator API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

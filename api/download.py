import yt_dlp
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import os
import uuid
from pathlib import Path

app = FastAPI()

@app.get("/info")
def get_info(url: str = Query(..., description="YouTube URL")):
    """Ambil info video (judul, thumbnail, formats) — cepat, no timeout"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)  # Hanya extract info, no download
        return {
            "title": info.get('title'),
            "thumbnail": info.get('thumbnail'),
            "duration": info.get('duration'),
            "formats": [{"height": f.get('height'), "ext": f.get('ext')} for f in info.get('formats', []) if f.get('height')],
            "author": info.get('uploader')
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/download")
def download(url: str = Query(..., description="YouTube URL"), q: str = Query("1080", description="Max quality")):
    """Trigger download — Vercel run yt-dlp di background, return link file (untuk full download, pakai webhook atau poll)"""
    # Catat: Di serverless, download panjang bisa timeout. Solusi: Pakai queue (Celery + Redis, tapi ribet untuk free).
    # Untuk sederhana, return info + "Download started" — full file via /status/{id}
    video_id = str(uuid.uuid4())[:8]
    output_dir = Path("/tmp") / video_id
    output_dir.mkdir(exist_ok=True)
    
    ydl_opts = {
        'format': f'bestvideo[height<={q}]+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': str(output_dir / "%(title)s.%(ext)s"),
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        # Return file (kalau kecil; untuk besar, return URL S3 atau similar)
        return {"message": "Download selesai!", "file": filename, "title": info.get('title')}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
import os
os.environ['PYTHON_VERSION'] = '3.12'
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp
import os
import uuid
import asyncio
from pathlib import Path

app = FastAPI(title="yt-dlp Server Gratis - Render")

@app.get("/")
def home():
    return {"message": "Server yt-dlp aktif! Contoh: /download?url=https://youtu.be/dQw4w9WgXcQ&q=1080"}

@app.get("/download")
async def download(url: str = Query(..., description="YouTube URL"), q: str = Query("1080", description="Max quality, e.g. 1080, 720, best")):
    if not url.startswith("https://www.youtube.com/") and not url.startswith("https://youtu.be/"):
        return JSONResponse({"error": "URL harus YouTube!"}, status_code=400)
    
    video_id = str(uuid.uuid4())[:8]
    output_dir = Path("/tmp") / video_id
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "%(title)s.%(ext)s"
    
    ydl_opts = {
        'format': f'bestvideo[height<={q}]+bestaudio/best[height<={q}]',
        'merge_output_format': 'mp4',
        'outtmpl': str(output_path),
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        # Cari file MP4 yang sudah tergabung
        mp4_file = next((f for f in output_dir.iterdir() if f.suffix == '.mp4'), None)
        if mp4_file:
            filename = str(mp4_file)
        
        return FileResponse(
            filename, 
            media_type='video/mp4', 
            filename=f"{info.get('title', 'video')}.mp4",
            headers={"Content-Disposition": f"attachment; filename={info.get('title', 'video')}.mp4"}
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        # Hapus file setelah 10 menit (biar storage nggak penuh)
        asyncio.create_task(cleanup(output_dir))

async def cleanup(dir_path: Path):
    await asyncio.sleep(600)
    try:
        for file in dir_path.iterdir():
            file.unlink()
        dir_path.rmdir()
    except:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
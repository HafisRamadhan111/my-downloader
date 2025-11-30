from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import yt_dlp
import requests

app = FastAPI()

# Izinkan akses
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    url: str

@app.post("/api/download_info")
def download_info(item: Item):
    """Endpoint untuk mengambil metadata video (judul, thumbnail, dll)"""
    try:
        # Settingan yt-dlp agar ringan di Vercel (simulate=True hanya ambil info)
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'simulate': True, 
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(item.url, download=False)
            
            return JSONResponse(content={
                "status": "success",
                "title": info.get('title', 'Video Tanpa Judul'),
                "thumb": info.get('thumbnail'),
                # Kami TIDAK mengembalikan URL di sini. Kami menggunakan endpoint terpisah untuk streaming file.
                "platform": info.get('extractor_key')
            })

    except Exception as e:
        print(f"Error di endpoint info: {e}")
        return JSONResponse(status_code=400, content={"status": "error", "msg": str(e)})


@app.get("/api/stream_file")
async def stream_file(video_url: str, title: str = "video"):
    """Endpoint untuk mengalirkan file video melalui backend."""
    try:
        # Kita perlu menjalankan yt-dlp lagi di sini TANPA simulate=True untuk mendapatkan URL streaming yang valid
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            actual_stream_url = info.get('url')

        # Gunakan requests untuk streaming file eksternal
        req = requests.get(actual_stream_url, stream=True, allow_redirects=True)
        req.raise_for_status()

        # Fungsi generator untuk menghasilkan potongan (chunks) file
        def file_iterator():
            for chunk in req.iter_content(chunk_size=8192):
                yield chunk
        
        content_type = req.headers.get('Content-Type')
        
        # Atur Content-Disposition untuk memaksa pengunduhan dengan nama file tertentu
        filename = f"{title}.mp4" # Asumsikan format mp4
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': content_type or 'video/mp4'
        }

        return StreamingResponse(file_iterator(), headers=headers)

    except Exception as e:
        print(f"Error di endpoint stream: {e}")
        raise HTTPException(status_code=500, detail="Tidak dapat melakukan streaming file. Video mungkin terlalu besar atau link tidak valid.")


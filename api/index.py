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
    """Endpoint untuk mengambil metadata dan URL streaming aktual."""
    try:
        # Gunakan opsi format terbaik, dan JANGAN SIMULATE di sini
        ydl_opts = {
            'format': 'best[ext=mp4]/best', # Opsi yang lebih sederhana untuk kecepatan
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(item.url, download=False)
            
            # Dapatkan URL streaming yang sebenarnya
            actual_stream_url = info.get('url')

            return JSONResponse(content={
                "status": "success",
                "title": info.get('title', 'Video Tanpa Judul'),
                "thumb": info.get('thumbnail'),
                "stream_url": actual_stream_url, # <-- KEMBALIKAN URL ASLI DI SINI
                "platform": info.get('extractor_key')
            })

    except Exception as e:
        print(f"Error di endpoint info: {e}")
        return JSONResponse(status_code=400, content={"status": "error", "msg": str(e)})


@app.get("/api/stream_file")
async def stream_file(video_url: str, title: str = "video"):
    """Endpoint untuk mengalirkan file video melalui backend."""
    try:
        # Kita SUDAH punya actual_stream_url dari frontend. 
        # Kita TIDAK PERLU menjalankan yt-dlp lagi di sini. Ini menghemat waktu eksekusi Vercel.
        actual_stream_url = video_url 

        # Gunakan requests untuk streaming file eksternal
        req = requests.get(actual_stream_url, stream=True, allow_redirects=True)
        req.raise_for_status()

        # Fungsi generator untuk menghasilkan potongan (chunks) file
        def file_iterator():
            for chunk in req.iter_content(chunk_size=8192):
                yield chunk
        
        content_type = req.headers.get('Content-Type')
        
        # Atur Content-Disposition untuk memaksa pengunduhan dengan nama file tertentu
        filename = f"{title}.mp4" 
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': content_type or 'video/mp4'
        }

        return StreamingResponse(file_iterator(), headers=headers)

    except Exception as e:
        print(f"Error di endpoint stream: {e}")
        raise HTTPException(status_code=500, detail="Tidak dapat melakukan streaming file. Video mungkin terlalu besar atau link tidak valid.")

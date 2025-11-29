from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

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

@app.post("/api/download")
def download_video(item: Item):
    try:
        # Settingan yt-dlp agar ringan di Vercel
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            # Jangan download fisik, cuma ambil info
            'simulate': True, 
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(item.url, download=False)
            
            return {
                "status": "success",
                "title": info.get('title', 'Video Tanpa Judul'),
                "thumb": info.get('thumbnail'),
                "url": info.get('url'),
                "platform": info.get('extractor_key')
            }

    except Exception as e:
        return {"status": "error", "msg": str(e)}

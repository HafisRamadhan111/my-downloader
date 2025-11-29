from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

# Izinkan akses dari mana saja
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
        # Konfigurasi yt-dlp KHUSUS Vercel
        # Kita matikan cache dan download fisik agar tidak error "Read Only"
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'extract_flat': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Ambil info saja, jangan download filenya ke server Vercel
            info = ydl.extract_info(item.url, download=False)
            
            return {
                "status": "success",
                "title": info.get('title'),
                "thumb": info.get('thumbnail'),
                "url": info.get('url'), # Ini URL video asli
                "platform": info.get('extractor_key')
            }

    except Exception as e:
        return {"status": "error", "msg": str(e)}

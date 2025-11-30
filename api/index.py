from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

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
        # --- KONFIGURASI ANTI BLOKIR & TANPA FFMPEG ---
        ydl_opts = {
            # PENTING: Minta format mp4 yang audio+video sudah gabung.
            # Biasanya max 720p, tapi ini satu-satunya cara agar jalan di Vercel tanpa FFmpeg.
            'format': 'best[ext=mp4]/best', 
            
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            
            # --- PENYAMARAN (Agar dikira HP iPhone) ---
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'referer': 'https://www.google.com/',
            
            # Paksa ekstrak info tanpa download file fisik ke server
            'extract_flat': False, 
        }

        # Khusus TikTok, kadang butuh penanganan ekstra
        if "tiktok.com" in item.url:
             # Coba paksa mobile version
             pass 

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(item.url, download=False)
            
            # Logika pencarian URL terbaik
            download_url = info.get('url')
            
            # Fallback (Jaga-jaga jika URL utama kosong)
            if not download_url:
                # Coba cari di formats
                formats = info.get('formats', [])
                for f in formats:
                    if f.get('ext') == 'mp4' and f.get('acodec') != 'none':
                        download_url = f.get('url')
                        break

            return {
                "status": "success",
                "title": info.get('title', 'Video Found'),
                "thumb": info.get('thumbnail'),
                "url": download_url,
                "platform": info.get('extractor_key')
            }

    except Exception as e:
        # Tampilkan error detail untuk diagnosa
        return {"status": "error", "msg": f"Gagal: {str(e)}"}

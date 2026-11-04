# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import os
import re
import random
import asyncio
import aiohttp
from pathlib import Path

from py_yt import Playlist, VideosSearch

from anony import config, logger
from anony.helpers import Track, utils


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.cookie_dir = "Kanha/cookies"
        self.warned = False
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )
        self.iregex = re.compile(
            r"https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)"
            r"(?!/(watch\?v=[A-Za-z0-9_-]{11}|shorts/[A-Za-z0-9_-]{11}"
            r"|playlist\?list=PL[A-Za-z0-9_-]+|[A-Za-z0-9_-]{11}))\S*"
        )

    def get_cookies(self):
        if not self.checked:
            # ပင်မဖိုင်တွဲ (Root) ထဲမှာရှိတဲ့ cookies.txt ကို ဦးစွာရှာဖွေခြင်း
            root_cookie = "cookies.txt"
            if os.path.exists(root_cookie):
                self.cookies.append(root_cookie)
            
            # Kanha/cookies ဖိုင်တွဲထဲက cookies များကိုလည်း ဆက်လက်ရှာဖွေခြင်း
            if os.path.exists(self.cookie_dir):
                for file in os.listdir(self.cookie_dir):
                    if file.endswith(".txt"):
                        self.cookies.append(f"{self.cookie_dir}/{file}")
            self.checked = True

        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("Cookies are missing; downloads might fail.")
            return None
        return random.choice(self.cookies)

    async def save_cookies(self, urls: list[str]) -> None:
        logger.info("Saving cookies from urls...")
        os.makedirs(self.cookie_dir, exist_ok=True)
        async with aiohttp.ClientSession() as session:
            for url in urls:
                name = url.split("/")[-1]
                link = "https://batbin.me/raw/" + name
                async with session.get(link) as resp:
                    resp.raise_for_status()
                    with open(f"{self.cookie_dir}/{name}.txt", "wb") as fw:
                        fw.write(await resp.read())
        logger.info(f"Cookies saved in {self.cookie_dir}.")

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    def invalid(self, url: str) -> bool:
        return bool(re.match(self.iregex, url))

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        try:
            _search = VideosSearch(query, limit=1, with_live=False)
            results = await _search.next()
        except Exception:
            return None
        if results and results["result"]:
            data = results["result"][0]
            return Track(
                id=data.get("id"),
                channel_name=data.get("channel", {}).get("name"),
                duration=data.get("duration"),
                duration_sec=utils.to_seconds(data.get("duration")),
                message_id=m_id,
                title=data.get("title")[:25],
                thumbnail=data.get("thumbnails", [{}])[-1].get("url").split("?")[0],
                url=data.get("link"),
                view_count=data.get("viewCount", {}).get("short"),
                video=video,
            )
        return None

    async def get_related(self, video_id: str, title: str = "", video: bool = False) -> list[Track]:
        """Autoplay အတွက် နောက်ဆက်တွဲ သီချင်းများကို ရှာဖွေပေးခြင်း"""
        tracks = []
        try:
            query = title if title else f"songs {video_id}"
            _search = VideosSearch(query, limit=10, with_live=False)
            results = await _search.next()
            if results and results["result"]:
                for data in results["result"]:
                    if data.get("id") == video_id:
                        continue
                    track = Track(
                        id=data.get("id"),
                        channel_name=data.get("channel", {}).get("name", ""),
                        duration=data.get("duration"),
                        duration_sec=utils.to_seconds(data.get("duration")),
                        title=data.get("title", "")[:25],
                        thumbnail=data.get("thumbnails", [{}])[-1].get("url").split("?")[0],
                        url=data.get("link"),
                        view_count=data.get("viewCount", {}).get("short", ""),
                        video=video,
                    )
                    tracks.append(track)
        except Exception as e:
            logger.warning(f"Failed to fetch related tracks for autoplay: {e}")
        return tracks

    async def get_stream_url(self, video_id: str, video: bool = False) -> str | None:
        """Autoplay အတွက် ချက်ချင်း stream လုပ်နိုင်သော URL ကို ရယူပေးခြင်း"""
        try:
            if getattr(config, "YT_API_URL", None) and getattr(config, "YT_API_KEY", None):
                ep = "play/video" if video else "play/audio"
                return f"{config.YT_API_URL.rstrip('/')}/{ep}?id={video_id}&api_key={config.YT_API_KEY}"
        except Exception:
            pass
        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in plist["videos"][:limit]:
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails")[-1].get("url").split("?")[0],
                    url=data.get("link").split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                )
                tracks.append(track)
        except Exception:
            pass
        return tracks

    async def download(self, video_id: str, video: bool = False) -> str | None:
        ext = "mp4" if video else "webm"
        filename = f"downloads/{video_id}.{ext}"

        if Path(filename).exists() and os.path.getsize(filename) > 10000:
            return filename

        os.makedirs("downloads", exist_ok=True)
        stream_type = "video" if video else "audio"
        
        # API ကို ဦးစွာ သုံးပြီး ဒေါင်းလုဒ်လုပ်ရန် ကြိုးစားခြင်း
        api_url = "https://api.shrutibots.in/download"
        target_url = f"{self.base}{video_id}"
        
        params = {
            "url": target_url,
            "type": stream_type,
            "api_key": getattr(config, "CORE_API_KEY", "")
        }
        
        timeout = aiohttp.ClientTimeout(total=600 if video else 300)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params, timeout=timeout) as resp:
                    if resp.status == 200:
                        with open(filename, "wb") as fw:
                            async for chunk in resp.content.iter_chunked(131072):
                                fw.write(chunk)
                        if Path(filename).exists() and os.path.getsize(filename) > 10000:
                            return filename
                    
                    logger.warning(f"API download failed ({resp.status}) for {video_id}. Falling back to yt-dlp...")
        except Exception as ex:
            logger.warning(f"API download error: {ex}. Falling back to yt-dlp...")

        # API အဆင်မပြေပါက yt-dlp ဖြင့် အလိုအလျောက် ဆက်လက်ဒေါင်းလုဒ်လုပ်ခြင်း (Fallback)
        return await self._download_via_ytdlp(video_id, video)

    async def _download_via_ytdlp(self, video_id: str, video: bool = False) -> str | None:
        """API ကျရှုံးပါက yt-dlp ဖြင့် အစားထိုး ဒေါင်းလုဒ်လုပ်ပေးမည့် Method"""
        try:
            import yt_dlp
            ext = "mp4" if video else "webm"
            filename = f"downloads/{video_id}.{ext}"
            
            if Path(filename).exists() and os.path.getsize(filename) > 10000:
                return filename

            os.makedirs("downloads", exist_ok=True)
            
            ydl_opts = {
                "format": "bestvideo+bestaudio/best" if video else "bestaudio/best",
                "outtmpl": f"downloads/{video_id}.%(ext)s",
                "quiet": True,
                "no_warnings": True,
            }
            
            cookie_file = self.get_cookies()
            if cookie_file:
                ydl_opts["cookiefile"] = cookie_file

            def download_sync():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"{self.base}{video_id}", download=True)
                    return ydl.prepare_filename(info)

            loop = asyncio.get_running_loop()
            file_path = await loop.run_in_executor(None, download_sync)
            
            if file_path and Path(file_path).exists() and os.path.getsize(file_path) > 10000:
                return file_path
        except Exception as e:
            logger.warning(f"yt-dlp fallback failed: {e}")
        return None

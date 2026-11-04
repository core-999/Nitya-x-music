# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# Storage Engine for Telegram Dump Supergroup (-1003913556820) and 1TB VPS Storage Engine

import asyncio
import os
import aiohttp
from pathlib import Path
from pyrogram import errors as pg_errors

from anony import config, logger


class StorageEngine:
    def __init__(self):
        self.vps_url = getattr(config, "VPS_STORAGE_URL", "http://162.35.187.203:8000").rstrip("/")
        self.vps_key = getattr(config, "VPS_API_KEY", "anku_storage_vps_key_2026")
        self.dump_channel = getattr(config, "STORAGE_GROUP_ID", -1003893296556)
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": "Chips-Music-StorageEngine/3.0"}
            )
        return self._session

    async def check_vps_stream(self, video_id: str, is_video: bool = False) -> str | None:
        """Check if 1TB VPS Storage has the song ready to stream directly."""
        if not self.vps_url:
            return None
        ep = "play/video" if is_video else "play/audio"
        url = f"{self.vps_url}/{ep}?id={video_id}"
        try:
            session = await self._get_session()
            timeout = aiohttp.ClientTimeout(connect=2, total=4)
            async with session.head(url, timeout=timeout) as resp:
                if resp.status == 200:
                    logger.info(f"[VPS HIT] Direct stream URL ready for {video_id}")
                    return url
        except Exception:
            pass
        return None

    @staticmethod
    def is_valid_media(file_path: str, is_video: bool = False) -> bool:
        if not file_path or not Path(file_path).exists() or Path(file_path).stat().st_size <= 1024:
            return False
        try:
            import subprocess
            res = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(file_path)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            target = "video" if is_video else "audio"
            return target in res.stdout
        except Exception:
            return True

    async def download_from_vps(self, video_id: str, dest_path: str, is_video: bool = False) -> bool:
        """Download song from 1TB VPS Storage into local downloads folder."""
        # Fast local NVMe disk check if running directly on the VPS host
        local_vps_dir = Path("/var/music_storage")
        if local_vps_dir.exists():
            cand_ext = "mp4" if is_video else "mp3"
            for ext in ([cand_ext] if is_video else ["mp3", "webm", "m4a", "opus"]):
                src = local_vps_dir / f"{video_id}.{ext}"
                if src.exists() and src.stat().st_size > 1024:
                    if not self.is_valid_media(str(src), is_video):
                        logger.warning(f"[VPS DISK PURGE] Purging corrupt NVMe file with no audio: {src}")
                        try:
                            src.unlink(missing_ok=True)
                        except Exception:
                            pass
                        continue
                    Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
                    import shutil
                    shutil.copy2(src, dest_path)
                    logger.info(f"[VPS DISK HIT] Instant NVMe restore: {video_id} -> {dest_path}")
                    return True

        if not self.vps_url:
            return False
        ep = "play/video" if is_video else "play/audio"
        url = f"{self.vps_url}/{ep}?id={video_id}"
        try:
            session = await self._get_session()
            timeout = aiohttp.ClientTimeout(connect=2, total=8)
            async with session.get(url, timeout=timeout) as resp:
                if resp.status == 200:
                    tmp_dest = f"{dest_path}.tmp"
                    Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(tmp_dest, "wb") as f:
                        async for chunk in resp.content.iter_chunked(256 * 1024):
                            f.write(chunk)
                    if Path(tmp_dest).exists() and Path(tmp_dest).stat().st_size > 1024:
                        if self.is_valid_media(tmp_dest, is_video):
                            import os
                            os.replace(tmp_dest, dest_path)
                            logger.info(f"[VPS DOWNLOAD] Restored {video_id} to {dest_path}")
                            return True
                        else:
                            Path(tmp_dest).unlink(missing_ok=True)
                            logger.warning(f"[VPS DOWNLOAD CORRUPT] Discarded corrupt VPS download for {video_id}")
                else:
                    logger.debug(f"VPS does not have {video_id} yet (status {resp.status})")
        except Exception as e:
            logger.warning(f"VPS download failed for {video_id}: {type(e).__name__}: {e}")
        return False

    async def restore_from_telegram_dump(self, video_id: str, dest_path: str, is_video: bool = False) -> bool:
        """Restore song from Telegram Dump Supergroup (-1003913556820)."""
        from anony import app, db, userbot
        try:
            doc = await db.get_music_cache(video_id, is_video=is_video)
            if not doc:
                return False

            ch_id = doc.get("channel_id") or self.dump_channel
            msg_id = doc.get("message_id")
            file_id = doc.get("file_id")

            # 1. Attempt via app (bot) + message_id
            if msg_id and ch_id:
                try:
                    msg = await app.get_messages(ch_id, msg_id)
                    if msg and (msg.audio or msg.video or msg.document):
                        path = await app.download_media(msg, file_name=dest_path)
                        if path and Path(path).exists() and Path(path).stat().st_size > 1024:
                            if not self.is_valid_media(path, is_video):
                                logger.warning(f"[TG DUMP PURGE] Discarding corrupt TG dump file {path}")
                                Path(path).unlink(missing_ok=True)
                                return False
                            logger.info(f"[TG DUMP HIT] Restored {video_id} via Bot message {msg_id}")
                            return True
                except Exception as e:
                    logger.debug(f"Dump restore bot msg error: {e}")

            # 2. Attempt via app (bot) + file_id
            if file_id:
                try:
                    path = await app.download_media(file_id, file_name=dest_path)
                    if path and Path(path).exists() and Path(path).stat().st_size > 1024:
                        if not self.is_valid_media(path, is_video):
                            logger.warning(f"[TG DUMP PURGE] Discarding corrupt TG dump file {path}")
                            Path(path).unlink(missing_ok=True)
                            return False
                        logger.info(f"[TG DUMP HIT] Restored {video_id} via Bot file_id")
                        return True
                except Exception as e:
                    logger.debug(f"Dump restore bot file_id error: {e}")

            # 3. Attempt via assistant userbot + message_id
            if userbot.clients and msg_id and ch_id:
                try:
                    ub = userbot.clients[0]
                    msg = await ub.get_messages(ch_id, msg_id)
                    if msg and (msg.audio or msg.video or msg.document):
                        path = await ub.download_media(msg, file_name=dest_path)
                        if path and Path(path).exists() and Path(path).stat().st_size > 1024:
                            if not self.is_valid_media(path, is_video):
                                logger.warning(f"[TG DUMP PURGE] Discarding corrupt TG dump file {path}")
                                Path(path).unlink(missing_ok=True)
                                return False
                            logger.info(f"[TG DUMP HIT] Restored {video_id} via Assistant message {msg_id}")
                            return True
                except Exception as e:
                    logger.debug(f"Dump restore assistant msg error: {e}")

            # 4. Attempt via assistant userbot + file_id
            if userbot.clients and file_id:
                try:
                    ub = userbot.clients[0]
                    path = await ub.download_media(file_id, file_name=dest_path)
                    if path and Path(path).exists() and Path(path).stat().st_size > 1024:
                        if not self.is_valid_media(path, is_video):
                            logger.warning(f"[TG DUMP PURGE] Discarding corrupt TG dump file {path}")
                            Path(path).unlink(missing_ok=True)
                            return False
                        logger.info(f"[TG DUMP HIT] Restored {video_id} via Assistant file_id")
                        return True
                except Exception as e:
                    logger.debug(f"Dump restore assistant file_id error: {e}")

        except Exception as e:
            logger.warning(f"Telegram dump restore failed for {video_id}: {e}")
        return False

    async def upload_to_telegram_dump(
        self, file_path: str, video_id: str, title: str, duration: int = 0, is_video: bool = False
    ) -> None:
        """Upload newly downloaded song to Telegram Dump channel and save metadata."""
        from anony import app, db
        if not self.dump_channel or not Path(file_path).exists():
            return
        try:
            caption = f"🎵 **{title or video_id}**\n🆔 `{video_id}`"
            msg = None
            try:
                if is_video:
                    msg = await app.send_video(self.dump_channel, video=file_path, caption=caption)
                else:
                    msg = await app.send_audio(
                        self.dump_channel, audio=file_path, caption=caption, title=title or video_id, duration=duration
                    )
            except Exception as bot_err:
                logger.debug(f"Bot dump upload error ({bot_err}); trying assistant session...")
                from anony import userbot
                if userbot.clients:
                    ub = userbot.clients[0]
                    if is_video:
                        msg = await ub.send_video(self.dump_channel, video=file_path, caption=caption)
                    else:
                        msg = await ub.send_audio(
                            self.dump_channel, audio=file_path, caption=caption, title=title or video_id, duration=duration
                        )

            if msg and msg.id:
                file_id = ""
                if is_video and getattr(msg, "video", None):
                    file_id = msg.video.file_id
                elif getattr(msg, "audio", None):
                    file_id = msg.audio.file_id
                elif getattr(msg, "document", None):
                    file_id = msg.document.file_id

                await db.save_music_cache(
                    video_id=video_id,
                    title=title or video_id,
                    duration=duration,
                    file_path=file_path,
                    message_id=msg.id,
                    channel_id=self.dump_channel,
                    file_id=file_id,
                    is_video=is_video,
                )
                logger.info(f"[TG DUMP] Saved {video_id} to Dump Channel -> msg_id: {msg.id}")
        except Exception as e:
            logger.warning(f"Failed to upload {video_id} to Telegram Dump: {e}")

    async def upload_to_vps_storage(self, file_path: str, video_id: str, is_video: bool = False) -> None:
        """Upload newly downloaded song to 1TB VPS Storage."""
        if not Path(file_path).exists() or Path(file_path).stat().st_size < 10000:
            return

        # Fast local NVMe disk sync if running directly on the VPS host
        local_vps_dir = Path("/var/music_storage")
        if local_vps_dir.exists():
            cand_ext = "mp4" if is_video else "mp3"
            dst = local_vps_dir / f"{video_id}.{cand_ext}"
            if not dst.exists() or dst.stat().st_size <= 1024:
                import shutil
                shutil.copy2(file_path, dst)
                logger.info(f"[VPS LOCAL SYNC] Saved {video_id} directly to /var/music_storage")
                return

        if not self.vps_url:
            return
        try:
            session = await self._get_session()
            with open(file_path, "rb") as f:
                data = f.read()
            headers = {
                "Content-Type": "application/octet-stream",
                "X-API-Key": self.vps_key,
            }
            timeout = aiohttp.ClientTimeout(total=45)
            async with session.post(
                f"{self.vps_url}/upload?id={video_id}",
                data=data,
                headers=headers,
                timeout=timeout,
            ) as resp:
                if resp.status in (200, 201):
                    logger.info(f"[VPS UPLOAD] Synced {video_id} ({len(data)} bytes) to 1TB VPS Storage")
        except Exception as e:
            logger.debug(f"VPS upload failed for {video_id}: {e}")

    def persist_background(
        self, file_path: str, video_id: str, title: str, duration: int = 0, is_video: bool = False
    ) -> None:
        """Non-blocking background sync to both Telegram Dump and 1TB VPS."""
        async def _sync():
            await self.upload_to_telegram_dump(file_path, video_id, title, duration, is_video)
            await self.upload_to_vps_storage(file_path, video_id, is_video=is_video)

        asyncio.create_task(_sync())


storage_engine = StorageEngine()

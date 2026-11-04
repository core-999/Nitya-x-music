# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# Plugin for 1TB VPS Storage Engine & Telegram Dump Supergroup status

import asyncio
import urllib.request
import json
from pyrogram import filters, types

from anony import app, config

VPS_URL = getattr(config, "VPS_STORAGE_URL", "http://162.35.187.203:8000")


def get_progress_bar(used: float, total: float, length: int = 10) -> str:
    if total <= 0:
        return "░" * length
    ratio = min(max(used / total, 0.0), 1.0)
    filled = int(round(ratio * length))
    return "█" * filled + "░" * (length - filled)


async def fetch_vps_stats() -> dict | None:
    def _fetch():
        req = urllib.request.Request(f"{VPS_URL}/stats", headers={"User-Agent": "Chips-Music-StorageEngine/3.0"})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode())
        return None
    try:
        return await asyncio.to_thread(_fetch)
    except Exception:
        return None


def format_vps_text(data: dict | None) -> str:
    dump_id = getattr(config, "STORAGE_GROUP_ID", -1003913556820)
    if not data:
        return (
            "⚡ **1 TB VPS Music Storage Engine**\n\n"
            "🔴 **Server Status:** Connecting / Temporarily Busy\n"
            f"🌐 **Server Host:** `{VPS_URL}`\n"
            f"📁 **Telegram Dump Channel:** `{dump_id}`\n\n"
            "The background syncer and 1TB storage engine are operating."
        )

    disk_total = data.get("disk_total_gb", 0)
    disk_used = data.get("disk_used_gb", 0)
    disk_free = data.get("disk_free_gb", 0)
    cached_count = data.get("cached_songs_count", 0)
    tg_sync = data.get("telegram_sync") or {}

    bar = get_progress_bar(disk_used, disk_total, length=10)
    free_pct = (disk_free / disk_total * 100) if disk_total > 0 else 0

    sync_status = tg_sync.get("status", "idle")
    total_db = tg_sync.get("total_in_db", 0)
    downloaded = tg_sync.get("downloaded", 0)
    current_song = tg_sync.get("current_song", "None")
    spm = tg_sync.get("download_speed_songs_per_min", 0.0)
    est_hours = tg_sync.get("estimated_hours_remaining", 0.0)

    sync_icon = "🟢" if sync_status == "running" else ("✅" if sync_status == "completed" else "⚪")

    text = (
        "⚡ **1 TB VPS Music Storage & Song CDN Status**\n\n"
        f"🌐 **Server Status:** 🟢 **ONLINE** (`162.35.187.203:8000`)\n"
        f"📁 **Telegram Dump Supergroup:** `{dump_id}`\n\n"
        f"💾 **Storage Capacity:**\n"
        f" • **Disk Space:** `[{bar}]`\n"
        f" • **Used:** `{disk_used:.2f} GB` / `{disk_total:.2f} GB`\n"
        f" • **Free:** `{disk_free:.2f} GB` ({free_pct:.1f}% free)\n"
        f" • **Cached Songs:** `{cached_count:,}` songs cached on SSD\n\n"
        f"📡 **Telegram Dump Sync Engine:**\n"
        f" • **State:** {sync_icon} **{sync_status.upper()}**\n"
        f" • **Downloaded:** `{downloaded:,}` / `{total_db:,}` songs\n"
        f" • **Speed:** `{spm:.1f}` songs/min (~`{est_hours:.1f}`h remaining)\n"
        f" • **Syncing Song:** `{current_song[:30]}`\n\n"
        "✨ **0-ms Ultra-Fast Playback:** Every song is served directly from 1TB VPS or Telegram Dump without hitting YouTube rate limits."
    )
    return text


@app.on_message(filters.command(["vps", "storage"]) & ~app.bl_users)
async def vps_status_cmd(_, m: types.Message):
    sent = await m.reply_text("🔍 *Querying 1TB VPS Storage Engine & Telegram Dump...*")
    data = await fetch_vps_stats()
    text = format_vps_text(data)

    buttons = types.InlineKeyboardMarkup(
        [[types.InlineKeyboardButton("🔄 Refresh Stats", callback_data="refresh_vps_stats")]]
    )
    await sent.edit_text(text, reply_markup=buttons)


@app.on_callback_query(filters.regex("^refresh_vps_stats$"))
async def refresh_vps_callback(_, query: types.CallbackQuery):
    await query.answer("Fetching latest VPS stats...")
    data = await fetch_vps_stats()
    text = format_vps_text(data)
    buttons = types.InlineKeyboardMarkup(
        [[types.InlineKeyboardButton("🔄 Refresh Stats", callback_data="refresh_vps_stats")]]
    )
    try:
        await query.message.edit_text(text, reply_markup=buttons)
    except Exception:
        pass

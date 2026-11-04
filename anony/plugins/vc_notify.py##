# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import app, db, lang
from anony.helpers import buttons, can_manage_vc


@app.on_message(
    filters.command(["vcnotify", "vcjoin", "vcnotification"])
    & filters.group
    & ~app.bl_users
)
@lang.language()
@can_manage_vc
async def vc_notify_cmd(_, m: types.Message):
    chat_id = m.chat.id
    if len(m.command) >= 2:
        arg = m.command[1].lower()
        if arg in ["on", "enable", "true", "yes"]:
            await db.set_vc_notify(chat_id, True)
            return await m.reply_text(
                m.lang.get(
                    "vc_notify_on",
                    "<blockquote><b>✅ 𝖵𝖢 𝖩ᴏɪɴ 𝖭ᴏᴛɪғɪᴄᴀᴛɪᴏɴs ᴇɴᴀʙʟᴇᴅ ғᴏʀ ᴛʜɪs ᴄʜᴀᴛ.</b></blockquote>",
                )
            )
        elif arg in ["off", "disable", "false", "no"]:
            await db.set_vc_notify(chat_id, False)
            return await m.reply_text(
                m.lang.get(
                    "vc_notify_off",
                    "<blockquote><b>❌ 𝖵𝖢 𝖩ᴏɪɴ 𝖭ᴏᴛɪғɪᴄᴀᴛɪᴏɴs ᴅɪsᴀʙʟᴇᴅ ғᴏʀ ᴛʜɪs ᴄʜᴀᴛ.</b></blockquote>",
                )
            )

    status = await db.is_vc_notify(chat_id)
    st_text = (
        m.lang.get("vc_notify_enabled", "Enabled")
        if status
        else m.lang.get("vc_notify_disabled", "Disabled")
    )
    status_fmt = m.lang.get(
        "vc_notify_status",
        "<blockquote><b>𝖵𝖢 𝖩ᴏɪɴ 𝖭ᴏᴛɪғɪᴄᴀᴛɪᴏɴs :</b> <code>{}</code></blockquote>",
    )
    await m.reply_text(
        status_fmt.format(st_text),
        reply_markup=buttons.vc_notify_markup(chat_id, status),
    )


@app.on_callback_query(filters.regex(r"^vcnotify_toggle") & ~app.bl_users)
@lang.language()
@can_manage_vc
async def vc_notify_cb(_, query: types.CallbackQuery):
    args = query.data.split()
    chat_id = int(args[1])
    action = args[2]
    status = action == "enable"
    await db.set_vc_notify(chat_id, status)

    st_text = (
        query.lang.get("vc_notify_enabled", "Enabled")
        if status
        else query.lang.get("vc_notify_disabled", "Disabled")
    )
    status_fmt = query.lang.get(
        "vc_notify_status",
        "<blockquote><b>𝖵𝖢 𝖩ᴏɪɴ 𝖭ᴏᴛɪғɪᴄᴀᴛɪᴏɴs :</b> <code>{}</code></blockquote>",
    )
    await query.edit_message_text(
        status_fmt.format(st_text),
        reply_markup=buttons.vc_notify_markup(chat_id, status),
    )

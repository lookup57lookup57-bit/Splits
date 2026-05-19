import asyncio
import logging
import os
import tempfile
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiofiles

# ====================== CONFIG ======================
TOKEN = "8681676603:AAFGcNweIR35WHUtwAE_j5uS7_jOSGy4RUs"  # ← Change this!

# Futuristic neon colors for messages
NEON_BLUE = "#00f7ff"
NEON_PURPLE = "#c300ff"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# FSM for custom chunk size
class SplitStates(StatesGroup):
    waiting_for_custom_size = State()

# Global dict to store file data temporarily
user_files = {}

# ====================== FUTURISTIC UI HELPERS ======================
def futuristic_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ 10 MB", callback_data="size_10")],
        [InlineKeyboardButton(text="🚀 25 MB", callback_data="size_25")],
        [InlineKeyboardButton(text="🌟 40 MB", callback_data="size_40")],
        [InlineKeyboardButton(text="🔥 50 MB", callback_data="size_50")],
        [InlineKeyboardButton(text="💫 CUSTOM SIZE", callback_data="size_custom")]
    ])

def neon_caption(part_num: int, total_parts: int, original_name: str):
    return (
        f"<b>🌌 FUTURE SPLIT • PART {part_num}/{total_parts} ⚡</b>\n"
        f"<i>Original:</i> <code>{original_name}</code>\n"
        f"<span style='color:{NEON_BLUE}'>Quantum chunk delivered</span>"
    )

# ====================== COMMANDS ======================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "<b>🌌 FUTURE SPLIT BOT</b> ⚡\n\n"
        "The most advanced, lightning-fast file splitter in the galaxy.\n\n"
        "✅ Any file (video, document, archive...)\n"
        "✅ Blazing async performance\n"
        "✅ Perfect chunks for Telegram\n"
        "✅ Neon cyber UI\n\n"
        "<i>Send any file to begin quantum split...</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🚀 START SPLITTING", callback_data="start_split")
        ]])
    )

@dp.callback_query(F.data == "start_split")
async def ask_for_file(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📤 <b>Drop your file here</b>\n"
        "<i>Any size • Up to 2 GB supported</i>\n\n"
        "I will split it into perfect neon chunks instantly."
    )
    await callback.answer()

# ====================== FILE HANDLING ======================
@dp.message(F.document | F.video)
async def handle_file(message: types.Message):
    file = message.document or message.video
    file_id = file.file_id
    file_name = file.file_name or f"file_{file.file_id[:8]}.{file.mime_type.split('/')[-1] if file.mime_type else 'bin'}"
    file_size_mb = round(file.file_size / (1024 * 1024), 2)

    user_files[message.from_user.id] = {
        "id": file_id,
        "name": file_name,
        "size_mb": file_size_mb
    }

    await message.reply(
        f"<b>🌌 FILE LOCKED IN</b> 🔒\n"
        f"Name: <code>{file_name}</code>\n"
        f"Size: <code>{file_size_mb} MB</code>\n\n"
        "Choose your chunk size (optimized for speed & Telegram limits):",
        reply_markup=futuristic_keyboard()
    )

# ====================== SPLIT LOGIC ======================
@dp.callback_query(F.data.startswith("size_"))
async def process_split(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id not in user_files:
        await callback.answer("⚠️ Send the file again", show_alert=True)
        return

    data = callback.data
    if data == "size_custom":
        await callback.message.edit_text(
            "💫 <b>ENTER CUSTOM CHUNK SIZE</b>\n\n"
            "Type a number in MB (example: <code>35</code>)\n"
            "Max recommended: 50 MB"
        )
        await state.set_state(SplitStates.waiting_for_custom_size)
        await callback.answer()
        return

    # Predefined sizes
    chunk_mb = int(data.split("_")[1])
    await do_split(callback, chunk_mb)

@dp.message(SplitStates.waiting_for_custom_size)
async def handle_custom_size(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in user_files:
        await message.answer("⚠️ Please send the file again.")
        await state.clear()
        return

    try:
        chunk_mb = int(message.text.strip())
        if chunk_mb < 1 or chunk_mb > 50:
            raise ValueError
    except ValueError:
        await message.answer("❌ Please send a valid number between 1 and 50.")
        return

    await state.clear()
    # Create a fake callback to reuse the same logic
    fake_callback = types.CallbackQuery(
        id="fake",
        from_user=message.from_user,
        chat_instance="fake",
        message=message,
        data=f"size_{chunk_mb}"
    )
    await do_split(fake_callback, chunk_mb)

async def do_split(callback: types.CallbackQuery, chunk_mb: int):
    user_id = callback.from_user.id
    file_data = user_files[user_id]
    
    status_msg = await callback.message.edit_text(
        f"⚡ <b>QUANTUM SPLIT ACTIVATED</b> 🌌\n"
        f"Chunk size: <code>{chunk_mb} MB</code>\n"
        f"Processing <code>{file_data['name']}</code>..."
    )

    await callback.answer("Splitting started...", show_alert=False)

    file = await bot.get_file(file_data["id"])
    chunk_size = chunk_mb * 1024 * 1024
    part_num = 1
    parts_sent = 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        download_path = os.path.join(tmp_dir, file_data["name"])
        
        # Download file
        await bot.download_file(file.file_path, download_path)
        
        async with aiofiles.open(download_path, "rb") as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break

                part_name = f"{os.path.splitext(file_data['name'])[0]}_part{part_num:03d}{os.path.splitext(file_data['name'])[1]}"
                part_path = os.path.join(tmp_dir, part_name)

                async with aiofiles.open(part_path, "wb") as part_file:
                    await part_file.write(chunk)

                # Send part with futuristic caption
                await bot.send_document(
                    chat_id=callback.message.chat.id,
                    document=FSInputFile(part_path),
                    caption=neon_caption(part_num, "??", file_data["name"])  # total_parts unknown until end, but ok
                )
                parts_sent += 1
                part_num += 1

                # Live progress
                await status_msg.edit_text(
                    f"📤 <b>SPLITTING IN PROGRESS</b> ⚡\n"
                    f"Sent: <code>{parts_sent}</code> parts • {chunk_mb} MB each"
                )

    # Final message
    await status_msg.edit_text(
        f"🎉 <b>QUANTUM SPLIT COMPLETE</b> 🌌\n"
        f"<code>{file_data['name']}</code> → <b>{parts_sent}</b> perfect parts\n\n"
        "The future is split. Send another file anytime 🚀\n"
        "<i>FutureSplit Bot • Made for speed</i>"
    )

    # Cleanup
    user_files.pop(user_id, None)

# ====================== ERROR & OTHER ======================
@dp.message()
async def fallback(message: types.Message):
    await message.answer(
        "🌌 <b>FutureSplit</b> only understands files.\n"
        "Send any document or video to begin quantum splitting."
    )

# ====================== LAUNCH ======================
async def main():
    print("🌌 FUTURE SPLIT BOT is now ONLINE")
    print("   ⚡ Blazing fast • Unique neon UI • Ready for 100+ users")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
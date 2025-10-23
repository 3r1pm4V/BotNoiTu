import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ========================
# CẤU HÌNH BOT
# ========================
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Lấy token từ Replit Secret

# Đọc từ điển Vietlex
with open("vietlex_words.txt", "r", encoding="utf-8") as f:
    VIETLEX_WORDS = set(w.strip().lower() for w in f if w.strip())

# Dữ liệu game
games = {}  # group_id -> { 'current_word': str, 'players': {}, 'turn_order': [] }

# ========================
# HÀM TRỢ GIÚP
# ========================
def get_last_char(word: str) -> str:
    for c in reversed(word):
        if c.isalpha():
            return c
    return ""

# ========================
# LỆNH BẮT ĐẦU TRÒ CHƠI
# ========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👑 Chào mừng đến với trò *VUA TIẾNG VIỆT*! 👑\n\n"
        "Dùng /newgame để bắt đầu trò chơi mới.\n"
        "Gõ từ đầu tiên để bắt đầu chuỗi!"
    )

# ========================
# TẠO GAME MỚI
# ========================
async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    games[chat_id] = {
        "current_word": None,
        "players": {},
        "turn_order": [],
    }
    await update.message.reply_text("🎮 Trò chơi mới đã được khởi tạo! Ai cũng có thể nhập từ để bắt đầu.")

# ========================
# KIỂM TRA TỪ NGƯỜI CHƠI NHẬP
# ========================
async def handle_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    player = update.effective_user.first_name
    word = update.message.text.strip().lower()

    if chat_id not in games:
        await update.message.reply_text("❗ Chưa có trò chơi nào đang diễn ra. Gõ /newgame để bắt đầu.")
        return

    game = games[chat_id]

    # Kiểm tra hợp lệ
    if word not in VIETLEX_WORDS:
        await update.message.reply_text(f"❌ '{word}' không có trong từ điển Vietlex.")
        return

    # Kiểm tra chữ cái đầu có khớp chữ cuối không (nếu đã có current_word)
    if game["current_word"]:
        last_char = get_last_char(game["current_word"])
        if not word.startswith(last_char):
            await update.message.reply_text(
                f"⚠️ '{word}' phải bắt đầu bằng chữ '{last_char.upper()}' của từ '{game['current_word']}'."
            )
            return

    # Ghi điểm
    game["players"].setdefault(player, 0)
    game["players"][player] += 1
    game["current_word"] = word

    await update.message.reply_text(
        f"✅ '{word}' hợp lệ! ({player} được +1 điểm)\n\n👉 Người tiếp theo, hãy nhập từ bắt đầu bằng chữ '{get_last_char(word).upper()}'!"
    )

# ========================
# XEM BẢNG ĐIỂM
# ========================
async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        await update.message.reply_text("❗ Chưa có trò chơi nào đang diễn ra.")
        return

    players = games[chat_id]["players"]
    if not players:
        await update.message.reply_text("🏁 Chưa có ai ghi điểm.")
        return

    sorted_scores = sorted(players.items(), key=lambda x: x[1], reverse=True)
    text = "🏆 *BẢNG ĐIỂM HIỆN TẠI*\n"
    for i, (p, s) in enumerate(sorted_scores, start=1):
        text += f"{i}. {p}: {s} điểm\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ========================
# RESET GAME
# ========================
async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in games:
        del games[chat_id]
    await update.message.reply_text("🛑 Trò chơi đã kết thúc!")

# ========================
# CHẠY BOT
# ========================
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("newgame", new_game))
app.add_handler(CommandHandler("score", score))
app.add_handler(CommandHandler("endgame", end_game))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_word))

print("🤖 Bot is running...")
app.run_polling()

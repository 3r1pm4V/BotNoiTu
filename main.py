import os
import random
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)

# --------------------------------------------------------------------
# ĐỌC TOKEN từ biến môi trường (set trong Railway Variables)
# --------------------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ ERROR: Chưa có BOT_TOKEN trong biến môi trường Railway.")
    exit(1)

# --------------------------------------------------------------------
# NẠP TỪ ĐIỂN TỪ FILE vietlex_words.txt
# --------------------------------------------------------------------
WORDS = set()
try:
    with open("vietlex_words.txt", "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip().lower()
            if word:
                WORDS.add(word)
    print(f"✅ Đã tải {len(WORDS)} từ từ điển.")
except FileNotFoundError:
    print("⚠️ Không tìm thấy file vietlex_words.txt! Vui lòng thêm file này vào project.")
    WORDS = set()

# --------------------------------------------------------------------
# DỮ LIỆU GAME (lưu trong RAM)
# --------------------------------------------------------------------
games = {}  # chat_id -> { "current": str, "players": {user_id: score} }

# --------------------------------------------------------------------
# CÁC HÀM LỆNH BOT
# --------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 *Chào mừng đến với Vua Tiếng Việt!*\n\n"
        "🔹 /newgame - Bắt đầu trò chơi mới\n"
        "🔹 /join - Tham gia trò chơi\n"
        "🔹 /score - Xem bảng điểm\n\n"
        "Nhập một từ hợp lệ trong tiếng Việt để chơi!",
        parse_mode="Markdown"
    )

async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    games[chat_id] = {"current": "", "players": {}}
    await update.message.reply_text("🆕 Trò mới đã bắt đầu! Dùng /join để tham gia!")

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id not in games:
        await update.message.reply_text("⚠️ Chưa có trò chơi nào. Gõ /newgame để bắt đầu.")
        return

    games[chat_id]["players"].setdefault(user.id, 0)
    await update.message.reply_text(f"✅ {user.first_name} đã tham gia trò chơi!")

async def current_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in games or not games[chat_id]["current"]:
        await update.message.reply_text("📜 Chưa có từ nào. Nhập từ đầu tiên để bắt đầu!")
    else:
        await update.message.reply_text(
            f"Từ hiện tại là: *{games[chat_id]['current']}*", parse_mode="Markdown"
        )

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        await update.message.reply_text("❗ Chưa có trò chơi nào.")
        return

    players = games[chat_id]["players"]
    if not players:
        await update.message.reply_text("📊 Chưa có ai ghi điểm.")
        return

    leaderboard = "\n".join(
        [f"{i+1}. {context.bot.get_chat_member(chat_id, uid).user.first_name}: {score} điểm"
         for i, (uid, score) in enumerate(sorted(players.items(), key=lambda x: x[1], reverse=True))]
    )

    await update.message.reply_text(f"🏆 *Bảng điểm:*\n{leaderboard}", parse_mode="Markdown")

# --------------------------------------------------------------------
# NHẬN TỪ NGƯỜI CHƠI
# --------------------------------------------------------------------
async def handle_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    text = update.message.text.strip().lower()

    if chat_id not in games:
        return  # chưa có game

    game = games[chat_id]

    if text not in WORDS:
        await update.message.reply_text(f"❌ '{text}' không có trong từ điển!")
        return

    # Nếu là từ đầu tiên
    if not game["current"]:
        game["current"] = text
        game["players"].setdefault(user.id, 0)
        await update.message.reply_text(f"✅ Từ đầu tiên là '{text}'! Tiếp tục nào!")
        return

    last_char = game["current"][-1]
    if text[0] != last_char:
        await update.message.reply_text(f"⚠️ Từ '{text}' phải bắt đầu bằng chữ '{last_char}'!")
        return

    # Hợp lệ
    game["current"] = text
    game["players"][user.id] = game["players"].get(user.id, 0) + 1
    await update.message.reply_text(
        f"✅ {user.first_name} +1 điểm!\nTừ mới: *{text}*",
        parse_mode="Markdown"
    )

# --------------------------------------------------------------------
# MAIN APP CHO RAILWAY
# --------------------------------------------------------------------
def main():
    print("🚀 Bot Vua Tiếng Việt đang chạy trên Railway...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Lệnh chính
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newgame", new_game))
    app.add_handler(CommandHandler("join", join_game))
    app.add_handler(CommandHandler("current", current_word))
    app.add_handler(CommandHandler("score", score))

    # Tin nhắn văn bản
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_word))

    app.run_polling()

if __name__ == "__main__":
    main()

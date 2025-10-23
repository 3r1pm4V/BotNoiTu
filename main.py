import os
import random
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Đọc token từ biến môi trường
TOKEN = os.getenv("BOT_TOKEN")

# Đọc từ điển
WORDS = set()
with open("vietlex_words.txt", "r", encoding="utf-8") as f:
    for line in f:
        WORDS.add(line.strip().lower())

# Dữ liệu trò chơi
games = {}  # chat_id -> { "current": str, "players": {user_id: score} }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 Chào mừng đến với trò *Vua Tiếng Việt*!\n"
        "Gõ /newgame để bắt đầu trò mới hoặc /join để tham gia.",
        parse_mode="Markdown"
    )

async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    games[chat_id] = {
        "current": "",
        "players": {}
    }
    await update.message.reply_text("🆕 Trò mới bắt đầu! Ai cũng có thể /join để tham gia!")

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id not in games:
        await update.message.reply_text("❗ Chưa có trò chơi nào. Gõ /newgame để bắt đầu.")
        return

    games[chat_id]["players"].setdefault(user.id, 0)
    await update.message.reply_text(f"✅ {user.first_name} đã tham gia trò chơi!")

async def current_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in games or not games[chat_id]["current"]:
        await update.message.reply_text("📜 Chưa có từ nào. Hãy nhập từ đầu tiên!")
    else:
        await update.message.reply_text(f"Từ hiện tại là: *{games[chat_id]['current']}*", parse_mode="Markdown")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    text = update.message.text.strip().lower()

    if chat_id not in games:
        return  # chưa bắt đầu game

    game = games[chat_id]

    # Kiểm tra tính hợp lệ
    if text not in WORDS:
        await update.message.reply_text(f"❌ '{text}' không có trong từ điển!")
        return

    # Nếu chưa có từ đầu tiên → đặt từ đầu tiên
    if not game["current"]:
        game["current"] = text
        game["players"].setdefault(user.id, 0)
        await update.message.reply_text(f"✅ Từ đầu tiên là '{text}'. Tiếp tục nào!")
        return

    # Kiểm tra ký tự cuối và đầu
    last_char = game["current"][-1]
    if text[0] != last_char:
        await update.message.reply_text(f"⚠️ Từ '{text}' phải bắt đầu bằng chữ '{last_char}'!")
        return

    # Nếu hợp lệ
    game["current"] = text
    game["players"][user.id] = game["players"].get(user.id, 0) + 1
    await update.message.reply_text(
        f"✅ {user.first_name} được +1 điểm!\nTừ mới: *{text}*",
        parse_mode="Markdown"
    )

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        await update.message.reply_text("❗ Chưa có trò chơi nào.")
        return

    scores = games[chat_id]["players"]
    if not scores:
        await update.message.reply_text("📊 Chưa có ai ghi điểm.")
        return

    leaderboard = "\n".join(
        [f"{i+1}. {context.bot.get_chat_member(chat_id, uid).user.first_name}: {score} điểm"
         for i, (uid, score) in enumerate(sorted(scores.items(), key=lambda x: x[1], reverse=True))]
    )

    await update.message.reply_text(f"🏆 Bảng điểm:\n{leaderboard}")

# Chạy bot
if __name__ == "__main__":
    if not TOKEN:
        print("❌ Thiếu BOT_TOKEN. Vui lòng cấu hình biến môi trường.")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newgame", new_game))
    app.add_handler(CommandHandler("join", join_game))
    app.add_handler(CommandHandler("current", current_word))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 Bot đang chạy...")
    app.run_polling()

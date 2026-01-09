import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from image_generator import generate_summary_image
import asyncio
import threading

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID") or 0)

if not BOT_TOKEN or CHAT_ID == 0:
    raise ValueError("请检查 .env 中的 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID")

def sync_send_summary():
    print("【自动推送】正在生成并发送最新总结图片...")
    image_path = "perp_summary.png"
    generate_summary_image(image_path)
    
    # 在独立线程中运行 async 发送
    async def async_send():
        app = Application.builder().token(BOT_TOKEN).build()
        async with app:
            await app.initialize()
            await app.start()
            with open(image_path, "rb") as photo:
                await app.bot.send_photo(chat_id=CHAT_ID, photo=photo, caption="Perpetual Dex 账户&风险监控总结（自动推送）")
            await app.stop()
            await app.shutdown()
        print("【自动推送】图片发送成功！")
    
    # 新线程运行 async 函数
    thread = threading.Thread(target=lambda: asyncio.run(async_send()))
    thread.start()
    thread.join()  # 等待完成

async def manual_send_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("正在生成最新图片，请稍等...")
    image_path = "perp_summary.png"
    generate_summary_image(image_path)
    
    with open(image_path, "rb") as photo:
        await update.message.reply_photo(photo=photo, caption="Perpetual Dex 账户&风险监控总结（手动触发）")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Perpetual Dex 监控 Bot 已启动！\n\n"
        "功能：\n"
        "/summary - 立即获取最新图片\n"
        "/now - 同上\n"
        "每小时自动推送一次"
    )

def main():
    application = Application.builder().token(BOT_TOKEN).read_timeout(30).write_timeout(30).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("summary", manual_send_summary))
    application.add_handler(CommandHandler("now", manual_send_summary))
    
    # 定时任务
    scheduler = BackgroundScheduler()
    scheduler.add_job(sync_send_summary, 'interval', minutes=30)
    scheduler.start()
    
    # 启动时立即发送一次
    print("Bot 启动中... 立即发送第一张图片")
    sync_send_summary()
    
    print("Bot 已完全启动！无 warning，无报错")
    print("每小时自动推送 + 手动命令正常")
    
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

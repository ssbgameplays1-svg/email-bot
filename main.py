import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

SENDERS = [
    {
        "email": "ssb.gameplays1@gmail.com",
        "password": "mfgs vvjy cden uqjo"
    },
    {
        "email": "email2@gmail.com",
        "password": "رمز-اپ-دوم"
    }
]

EMAIL, SUBJECT, BODY, TIMES, CONFIRM = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام!\n\n"
        "دستورات:\n"
        "/send - شروع ارسال ایمیل\n"
        "/cancel - لغو عملیات"
    )

async def send_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("لطفا ایمیل گیرنده را وارد کن:")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if "@" not in email or "." not in email:
        await update.message.reply_text("ایمیل معتبر نیست. دوباره وارد کن:")
        return EMAIL
    context.user_data["email"] = email
    await update.message.reply_text("حالا موضوع ایمیل را بنویس:")
    return SUBJECT

async def get_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["subject"] = update.message.text
    await update.message.reply_text("حالا متن ایمیل را بنویس:")
    return BODY

async def get_body(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["body"] = update.message.text
    await update.message.reply_text("چند بار این ایمیل ارسال شود؟ (فقط عدد)")
    return TIMES

async def get_times(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or int(text) < 1:
        await update.message.reply_text("لطفا یک عدد معتبر وارد کن:")
        return TIMES

    times = int(text)
    context.user_data["times"] = times

    summary = (
        "تایید نهایی:\n\n"
        f"گیرنده: {context.user_data['email']}\n"
        f"موضوع: {context.user_data['subject']}\n"
        f"تعداد دفعات: {times}\n"
        f"تعداد حساب های ارسال کننده: {len(SENDERS)}\n\n"
        f"متن:\n{context.user_data['body']}\n\n"
        "اگر درست است /confirm را بفرست\n"
        "برای لغو /cancel"
    )
    await update.message.reply_text(summary)
    return CONFIRM

async def confirm_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    recipient = context.user_data["email"]
    subject = context.user_data["subject"]
    body = context.user_data["body"]
    times = context.user_data["times"]

    total_success = 0
    results = []

    for sender in SENDERS:
        sender_email = sender["email"]
        sender_pass = sender["password"]
        success = 0

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, sender_pass)

                for i in range(times):
                    msg = MIMEMultipart()
                    msg["From"] = sender_email
                    msg["To"] = recipient
                    msg["Subject"] = subject
                    msg.attach(MIMEText(body, "plain", "utf-8"))
                    server.sendmail(sender_email, recipient, msg.as_string())
                    success += 1

            results.append(f"موفق: {sender_email} - {success} بار")
            total_success += success

        except Exception as e:
            results.append(f"خطا در {sender_email}: {str(e)}")

    final_message = "نتیجه ارسال:\n\n" + "\n".join(results) + f"\n\nجمع کل: {total_success}"
    await update.message.reply_text(final_message)

    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END

def main():
    if not TELEGRAM_TOKEN:
        print("خطا: TELEGRAM_TOKEN تنظیم نشده")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("send", send_start)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & \~filters.COMMAND, get_email)],
            SUBJECT: [MessageHandler(filters.TEXT & \~filters.COMMAND, get_subject)],
            BODY: [MessageHandler(filters.TEXT & \~filters.COMMAND, get_body)],
            TIMES: [MessageHandler(filters.TEXT & \~filters.COMMAND, get_times)],
            CONFIRM: [CommandHandler("confirm", confirm_send)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CommandHandler("cancel", cancel))

    print("ربات روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()

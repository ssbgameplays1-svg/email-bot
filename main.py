import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# ====================== این ۳ مورد را عوض کن ======================
TELEGRAM_TOKEN = "8765400146:AAFFXaPXCJ-WjfWFjn7ULsnrnHz9gl_gDZs"
GMAIL_ADDRESS = "ssb.gameplays1@gmail.com"
GMAIL_APP_PASSWORD = "napg brid ifvg gfzf"
# =================================================================

# مراحل گفتگو
EMAIL, SUBJECT, BODY, TIMES, CONFIRM = range(5)

# ---------- دستور /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 👋\n\n"
        "من ربات ارسال ایمیل هستم.\n\n"
        "دستورات:\n"
        "/send → شروع ارسال ایمیل\n"
        "/cancel → لغو عملیات در هر مرحله"
    )

# ---------- شروع ارسال ----------
async def send_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("لطفاً **ایمیل گیرنده** را وارد کن:")
    return EMAIL

# ---------- گرفتن ایمیل ----------
async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    
    if "@" not in email or "." not in email:
        await update.message.reply_text("ایمیل معتبر نیست. لطفاً دوباره وارد کن:")
        return EMAIL
    
    context.user_data["email"] = email
    await update.message.reply_text("حالا **موضوع ایمیل** را بنویس:")
    return SUBJECT

# ---------- گرفتن موضوع ----------
async def get_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["subject"] = update.message.text
    await update.message.reply_text("حالا **متن ایمیل** را بنویس:")
    return BODY

# ---------- گرفتن متن ----------
async def get_body(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["body"] = update.message.text
    await update.message.reply_text("چند بار این ایمیل برای این همکار ارسال شود؟\n(فقط عدد وارد کن، مثلاً 1 یا 3)")
    return TIMES

# ---------- گرفتن تعداد دفعات ----------
async def get_times(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if not text.isdigit() or int(text) < 1:
        await update.message.reply_text("لطفاً یک عدد معتبر (بزرگ‌تر از صفر) وارد کن:")
        return TIMES
    
    times = int(text)
    context.user_data["times"] = times

    # نمایش خلاصه برای تأیید
    summary = (
        "🔍 تأیید نهایی:\n\n"
        f"گیرنده: {context.user_data['email']}\n"
        f"موضوع: {context.user_data['subject']}\n"
        f"تعداد دفعات ارسال: {times} بار\n\n"
        f"متن ایمیل:\n{context.user_data['body']}\n\n"
        "اگر همه چیز درست است، /confirm را بفرست.\n"
        "برای لغو /cancel را بفرست."
    )
    await update.message.reply_text(summary)
    return CONFIRM

# ---------- ارسال نهایی ----------
async def confirm_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = context.user_data["email"]
    subject = context.user_data["subject"]
    body = context.user_data["body"]
    times = context.user_data["times"]

    success_count = 0
    errors = []

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)

            for i in range(times):
                try:
                    msg = MIMEMultipart()
                    msg["From"] = GMAIL_ADDRESS
                    msg["To"] = email
                    msg["Subject"] = subject
                    msg.attach(MIMEText(body, "plain", "utf-8"))

                    server.sendmail(GMAIL_ADDRESS, email, msg.as_string())
                    success_count += 1
                except Exception as e:
                    errors.append(f"دفعه {i+1}: {str(e)}")

        if success_count == times:
            await update.message.reply_text(f"✅ ایمیل با موفقیت {times} بار ارسال شد!")
        else:
            await update.message.reply_text(
                f"⚠️ {success_count} بار ارسال شد از {times} بار.\n"
                f"خطاها:\n" + "\n".join(errors)
            )

    except Exception as e:
        await update.message.reply_text(f"❌ خطا در اتصال به جیمیل:\n{str(e)}")

    context.user_data.clear()
    return ConversationHandler.END

# ---------- لغو ----------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END

# ---------- اجرای ربات ----------
def main():
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

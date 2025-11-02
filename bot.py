import logging
import os
import database as db  
from dotenv import load_dotenv
from telegram import BotCommand
import telegram 
import datetime 
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
try:
    ADMIN_ID = int(os.getenv("ADMIN_ID"))
except (ValueError, TypeError):
    print("Error: Pastikan ADMIN_ID di file .env sudah benar (berisi angka).")
    exit()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

PILIH_MATKUL, DESKRIPSI, DEADLINE = range(3)
MATKUL_NAMA, MATKUL_HARI, MATKUL_JAM, MATKUL_RUANGAN = range(3, 7) 

def is_admin(user_id: int) -> bool:
    """Mengecek apakah user adalah admin."""
    return user_id == ADMIN_ID

MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📚 Cek Jadwal", "📝 Cek Tugas"],
        ["➕ Add Tugas", "✅ Tugas Selesai"],
        ["❓ Bantuan"]
    ],
    resize_keyboard=True
)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk command /start. Sekarang menampilkan Menu Utama."""
    user = update.effective_user
    await update.message.reply_html(
        f"Halo {user.mention_html()}! 👋\n\n"
        "Saya adalah bot pengingat tugas kuliahmu. Gunakan tombol di bawah untuk navigasi.",
        reply_markup=MAIN_MENU_KEYBOARD
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk command /help."""
    admin_text = ""
    if is_admin(update.effective_user.id):
        admin_text = (
            "\n\n<b>--- 👮 Perintah Admin ---</b>\n"
            "/clear_tugas - Menghapus SEMUA tugas.\n"
            "Tombol 'Hapus' di /cek_tugas."
        )

    await update.message.reply_html(
        "<b>Daftar Perintah</b>\n\n"
        "/start - Memulai bot\n"
        "/help - Menampilkan bantuan ini\n"
        "/cek_matkul - Menampilkan jadwal mata kuliah\n"
        "/cek_tugas - Menampilkan semua tugas yang belum selesai\n"
        "/add_tugas - Menambahkan tugas baru (interaktif)\n"
        "/cancel - Membatalkan proses penambahan tugas"
        f"{admin_text}"
    )

async def cek_matkul(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /cek_matkul. Menampilkan jadwal."""
    try:
        matkul_list = db.get_matkul()
        if not matkul_list:
            await update.message.reply_text("Belum ada data mata kuliah.")
            return

        message = "<b>Jadwal Mata Kuliah</b> 📚\n\n"
        for matkul in matkul_list:
            message += (
                f"<b>{matkul['nama']}</b>\n"
                f"  📅: {matkul['hari']}\n"
                f"  ⏰: {matkul['jam']}\n"
                f"  🏫: {matkul['ruangan']}\n"
                "--------------------\n"
            )
        
        await update.message.reply_html(message)

    except Exception as e:
        logger.error(f"Error di cek_matkul: {e}")
        await update.message.reply_text(f"Terjadi error: {e}")

async def cek_tugas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /cek_tugas. Menampilkan tugas dengan tombol inline."""
    try:
        tugas_list = db.get_tugas(status='pending')
        if not tugas_list:
            await update.message.reply_text("Hore! Tidak ada tugas yang pending. 🎉")
            return

        await update.message.reply_text("Berikut adalah daftar tugas yang belum selesai:")
        for tugas in tugas_list:
            task_id = tugas['id']
            message = (
                f"📚 <b>{tugas['matkul_nama']}</b>\n"
                f"📝: {tugas['deskripsi']}\n"
                f"⏳: <b>{tugas['deadline']}</b>"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Selesai", callback_data=f"done_{task_id}"),
                    InlineKeyboardButton("❌ Hapus", callback_data=f"delete_{task_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_html(message, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error di cek_tugas: {e}")
        await update.message.reply_text(f"Terjadi error: {e}")


async def tugas_selesai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /tugas_selesai. Menampilkan tugas yang sudah 'done'."""
    try:
        tugas_list = db.get_tugas(status='done')
        if not tugas_list:
            await update.message.reply_text("Belum ada tugas yang selesai. Semangat! 💪")
            return

        message = "<b>Daftar Tugas yang Sudah Selesai</b> ✅\n\n"
        for tugas in tugas_list:
            message += (
                f"📚 <b>{tugas['matkul_nama']}</b>\n"
                f"📝: {tugas['deskripsi']}\n"
                f"⏳: <i>{tugas['deadline']}</i>\n"
                "--------------------\n"
            )
        
        await update.message.reply_html(message)

    except Exception as e:
        logger.error(f"Error di tugas_selesai: {e}")
        await update.message.reply_text(f"Terjadi error: {e}")

async def del_matkul(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /del_matkul (Admin). Menampilkan matkul dengan tombol hapus."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Maaf, perintah ini hanya untuk admin. 👮")
        return
        
    try:
        matkul_list = db.get_matkul()
        if not matkul_list:
            await update.message.reply_text("Tidak ada mata kuliah untuk dihapus.")
            return

        await update.message.reply_text("Pilih mata kuliah yang ingin dihapus (HATI-HATI!):")
        for matkul in matkul_list:
            matkul_id = matkul['id']
            message = (
                f"<b>{matkul['nama']}</b>\n"
                f"({matkul['hari']}, {matkul['jam']}, {matkul['ruangan']})"
            )
            
            keyboard = [[
                InlineKeyboardButton("❌ Hapus Matkul Ini", callback_data=f"delmatkul_{matkul_id}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_html(message, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error di del_matkul: {e}")
        await update.message.reply_text(f"Terjadi error: {e}")


async def add_matkul_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Langkah 1: Memulai tambah matkul, meminta NAMA."""
    
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Maaf, perintah ini hanya untuk admin. 👮")
        return ConversationHandler.END

    await update.message.reply_text(
        "Oke, mari tambahkan mata kuliah baru.\n"
        "<b>Langkah 1:</b> Masukkan <b>Nama Mata Kuliah</b>?",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.HTML
    )
    return MATKUL_NAMA

async def matkul_nama(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Langkah 2: Menyimpan NAMA, meminta HARI."""
    context.user_data['matkul_nama'] = update.message.text
    
    keyboard = [
        ['Senin', 'Selasa', 'Rabu'],
        ['Kamis', 'Jumat', 'Sabtu'],
        ['/cancel']
    ]
    
    await update.message.reply_text(
        "Nama dicatat. <b>Langkah 2:</b> Pilih <b>Hari</b>?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )
    return MATKUL_HARI

async def matkul_hari(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Langkah 3: Menyimpan HARI, meminta JAM."""
    context.user_data['matkul_hari'] = update.message.text
    
    await update.message.reply_text(
        "Hari dicatat. <b>Langkah 3:</b> Masukkan <b>Jam</b>?\n"
        "(Contoh: <i>08:00 - 10:00</i>)",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.HTML
    )
    return MATKUL_JAM

async def matkul_jam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Langkah 4: Menyimpan JAM, meminta RUANGAN."""
    context.user_data['matkul_jam'] = update.message.text
    
    await update.message.reply_text(
        "Jam dicatat. <b>Langkah 4:</b> Masukkan <b>Ruangan</b>?",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.HTML
    )
    return MATKUL_RUANGAN

async def matkul_ruangan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Langkah 5: Menyimpan RUANGAN, simpan ke DB, dan selesai."""
    try:
        db.add_matkul(nama, hari, jam, ruangan)
        
        await update.message.reply_html(
            "<b>Mata Kuliah berhasil ditambahkan!</b> ✅\n\n"
            f"📚 <b>Nama:</b> {nama}\n"
            f"🏫 <b>Ruangan:</b> {ruangan}",
            reply_markup=MAIN_MENU_KEYBOARD
        )
    except Exception as e:
        logger.error(f"Error di matkul_ruangan (add_matkul): {e}")
        await update.message.reply_text(
            f"Gagal menyimpan mata kuliah: {e}",

            reply_markup=MAIN_MENU_KEYBOARD
        )
    finally:
        context.user_data.clear()
        return ConversationHandler.END
    

async def clear_tugas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /clear_tugas (Hanya Admin)."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Maaf, perintah ini hanya untuk admin. 👮")
        return

    try:
        db.clear_all_tugas()
        await update.message.reply_text("BERHASIL! Semua tugas telah dihapus dari database. 🗑️")
    except Exception as e:
        logger.error(f"Error di clear_tugas: {e}")
        await update.message.reply_text(f"Terjadi error saat menghapus tugas: {e}")

async def add_tugas_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Langkah 1: Memulai proses tambah tugas, meminta pilih matkul."""
    nama_matkul = db.get_nama_matkul()
    if not nama_matkul:
        await update.message.reply_text("Database mata kuliah kosong. Hubungi admin.")
        return ConversationHandler.END

    keyboard = [nama_matkul[i:i + 2] for i in range(0, len(nama_matkul), 2)]
    
    await update.message.reply_text(
        "Oke, mari tambahkan tugas baru.\n"
        "<b>Langkah 1:</b> Pilih mata kuliah.",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )
    return PILIH_MATKUL

async def pilih_matkul(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Langkah 2: Menyimpan matkul, meminta deskripsi tugas."""
    matkul = update.message.text
    context.user_data['matkul'] = matkul
    
    await update.message.reply_text(
        f"Matkul: <b>{matkul}</b>\n"
        "<b>Langkah 2:</b> Sekarang masukkan deskripsi tugasnya.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.HTML
    )
    return DESKRIPSI

async def deskripsi_tugas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Langkah 3: Menyimpan deskripsi, meminta deadline."""
    deskripsi = update.message.text
    context.user_data['deskripsi'] = deskripsi
    
    await update.message.reply_text(
        "Deskripsi dicatat.\n"
        "<b>Langkah 3:</b> Masukkan deadline.\n"
        "(Contoh: <i>Besok 23:59, Senin 15 Okt, 30/10/2025</i>)",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.HTML
    )
    return DEADLINE

async def deadline_tugas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Langkah 4: Menyimpan deadline, simpan ke DB, dan selesai."""
    deadline = update.message.text
    matkul = context.user_data['matkul']
    deskripsi = context.user_data['deskripsi']
    
    try:
        db.add_tugas(matkul, deskripsi, deadline)
        
        await update.message.reply_html(
            "<b>Tugas berhasil ditambahkan!</b> ✅\n\n"
            f"📚 <b>Matkul:</b> {matkul}\n"
            f"📝 <b>Tugas:</b> {deskripsi}\n"
            f"⏳ <b>Deadline:</b> {deadline}",
            reply_markup=MAIN_MENU_KEYBOARD 
        )
    except Exception as e:
        logger.error(f"Error di deadline_tugas (add_tugas): {e}")
        await update.message.reply_text(
            f"Gagal menyimpan tugas: {e}",
            reply_markup=MAIN_MENU_KEYBOARD
        )
    finally:
        context.user_data.clear()
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Membatalkan ConversationHandler dan kembali ke Menu Utama."""
    await update.message.reply_text(
        "Proses dibatalkan. Kembali ke menu utama.", 
        reply_markup=MAIN_MENU_KEYBOARD
    )
    context.user_data.clear()
    return ConversationHandler.END

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk semua tombol inline (Selesai, Hapus Tugas, Hapus Matkul)."""
    query = update.callback_query
    await query.answer()  

    data = query.data
    action, data_id_str = data.split('_', 1) 
    data_id = int(data_id_str)
    
    try:
        if action == "done":
            db.update_tugas_status(data_id, 'done')
            await query.edit_message_text(
                text=f"{query.message.text_html}\n\n--- <b>Status: ✅ SELESAI</b> ---", 
                parse_mode=ParseMode.HTML
            )
            
        elif action == "delete":
            if not is_admin(query.from_user.id):
                await query.answer("Maaf, hanya admin yang bisa menghapus tugas.", show_alert=True)
                return
                
            db.delete_tugas(data_id)
            await query.edit_message_text(
                text=f"{query.message.text_html}\n\n--- <b>Status: ❌ DIHAPUS ADMIN</b> ---", 
                parse_mode=ParseMode.HTML
            )
            
        elif action == "delmatkul":
            if not is_admin(query.from_user.id):
                await query.answer("Maaf, hanya admin yang bisa menghapus mata kuliah.", show_alert=True)
                return
            
            db.delete_matkul(data_id)
            await query.edit_message_text(
                text=f"{query.message.text_html}\n\n--- <b>Status: ❌ MATA KULIAH DIHAPUS</b> ---", 
                parse_mode=ParseMode.HTML
            )
            
    except Exception as e:
        logger.error(f"Error di button_callback: {e}")
        await query.answer(f"Terjadi error: {e}", show_alert=True)

async def setup_commands(application: Application) -> None:
    """Mengatur daftar perintah yang muncul di tombol Menu."""
    commands = [
        BotCommand("start", "🚀 Mulai bot"),
        BotCommand("cek_matkul", "📚 Lihat jadwal matkul"),
        BotCommand("cek_tugas", "📝 Lihat tugas pending"),
        BotCommand("tugas_selesai", "✅ Lihat tugas selesai"), 
        BotCommand("add_tugas", "➕ Tambah tugas baru"),
        BotCommand("help", "❓ Bantuan"),
    ]
    await application.bot.set_my_commands(commands)
    
    try:
        admin_commands = commands + [
            BotCommand("add_matkul", "🎓 TAMBAH MATKUL (Admin)"),   
            BotCommand("del_matkul", "🚫 HAPUS MATKUL (Admin)"),   
            BotCommand("clear_tugas", "🗑️ HAPUS SEMUA TUGAS (Admin)"),
        ]
        await application.bot.set_my_commands(admin_commands, scope=telegram.BotCommandScopeChat(chat_id=ADMIN_ID))
        logger.info(f"Perintah admin khusus diatur untuk ADMIN_ID: {ADMIN_ID}")
    except Exception as e:
        logger.warning(f"Gagal mengatur perintah admin (Mungkin ADMIN_ID salah?): {e}")

async def kirim_pengingat_harian(context: ContextTypes.DEFAULT_TYPE):
    """
    JOB Harian: Mengecek DB dan mengirim pengingat jika ada deadline dekat.
    Dijalankan setiap hari jam 8 pagi WIB (jam 1:00 UTC).
    """
    logger.info("JOB: Menjalankan pengecekan pengingat harian...")
    
    try:
        tugas_list = db.get_tugas(status='pending')
        if not tugas_list:
            logger.info("JOB: Tidak ada tugas pending, tidak ada pengingat dikirim.")
            return

        deadline_dekat = []
        for tugas in tugas_list:
            deadline_lower = tugas['deadline'].lower()
            if 'besok' in deadline_lower or 'hari ini' in deadline_lower:
                deadline_dekat.append(tugas)

        if deadline_dekat:
            message = "‼️ <b>PENGINGAT TUGAS HARIAN</b> ‼️\n\nHati-hati, ada tugas yang deadline-nya dekat:\n\n"
            for tugas in deadline_dekat:
                message += (
                    f"📚 <b>{tugas['matkul_nama']}</b>\n"
                    f"📝: {tugas['deskripsi']}\n"
                    f"⏳: <b>{tugas['deadline']}</b>\n"
                    "--------------------\n"
                )
            await context.bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode=ParseMode.HTML)
            logger.info(f"JOB: Berhasil mengirim pengingat untuk {len(deadline_dekat)} tugas.")
        else:
            logger.info("JOB: Ada tugas, tapi tidak ada yang deadline-nya 'besok' or 'hari ini'.")
            
    except Exception as e:
        logger.error(f"JOB: Gagal menjalankan kirim_pengingat_harian: {e}")


# --- Fungsi Main ---

def main() -> None:
    """Fungsi utama untuk setup dan menjalankan bot."""

    logger.info("Menginisialisasi database...")
    db.init_db()
    application = Application.builder().token(TOKEN).build()

    conv_handler_tugas = ConversationHandler(
        entry_points=[
            CommandHandler("add_tugas", add_tugas_start),
            MessageHandler(filters.TEXT & filters.Regex("^➕ Add Tugas$"), add_tugas_start)
        ],
        states={
            PILIH_MATKUL: [MessageHandler(filters.TEXT & ~filters.COMMAND, pilih_matkul)],
            DESKRIPSI: [MessageHandler(filters.TEXT & ~filters.COMMAND, deskripsi_tugas)],
            DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, deadline_tugas)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    conv_handler_matkul = ConversationHandler(
        entry_points=[CommandHandler("add_matkul", add_matkul_start)],
        states={
            MATKUL_NAMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, matkul_nama)],
            MATKUL_HARI: [MessageHandler(filters.TEXT & ~filters.COMMAND, matkul_hari)],
            MATKUL_JAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, matkul_jam)],
            MATKUL_RUANGAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, matkul_ruangan)],
        },
        fallbacks=[CommandHandler("cancel", cancel)], 
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cek_matkul", cek_matkul))
    application.add_handler(CommandHandler("cek_tugas", cek_tugas))
    application.add_handler(CommandHandler("clear_tugas", clear_tugas))
    application.add_handler(CommandHandler("tugas_selesai", tugas_selesai))
    application.add_handler(CommandHandler("del_matkul", del_matkul))
    application.add_handler(conv_handler_tugas)
    application.add_handler(conv_handler_matkul) 
    application.add_handler(CallbackQueryHandler(button_callback)) 
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📚 Cek Jadwal$"), cek_matkul))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📝 Cek Tugas$"), cek_tugas))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^✅ Tugas Selesai$"), tugas_selesai))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^❓ Bantuan$"), help_command))
    job_queue = application.job_queue
    job_queue.run_once(setup_commands, 0) 
    target_time = datetime.time(hour=1, minute=0, second=0) 
    job_queue.run_daily(kirim_pengingat_harian, time=target_time, days=(0, 1, 2, 3, 4, 5, 6))
    logger.info("Job pengingat harian diatur untuk jam 01:00 UTC (08:00 WIB).")


    logger.info("Bot mulai berjalan...")
    application.run_polling()


if __name__ == "__main__":
    main()
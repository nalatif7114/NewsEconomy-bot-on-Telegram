"""
📊 US Economic News Bot (High Impact ⭐⭐⭐)
Mengirim reminder berita ekonomi AS dengan impact tinggi setiap hari & minggu.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────── CONFIG ────────────────────────────
BOT_TOKEN       = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
SUBSCRIBERS_FILE = "subscribers.json"
WIB             = ZoneInfo("Asia/Jakarta")

IMPACT_EMOJI = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
DAY_ID = {
    "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
    "Thursday": "Kamis", "Friday": "Jumat",
    "Saturday": "Sabtu", "Sunday": "Minggu",
}

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ─────────────────────────── DATA ──────────────────────────────
def load_subscribers() -> list:
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE) as f:
            return json.load(f)
    return []


def save_subscribers(subs: list):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(subs, f, indent=2)


def fetch_this_week_events() -> list:
    """
    Ambil data kalender ekonomi minggu ini dari ForexFactory JSON feed.
    Filter hanya USD + High Impact.
    """
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return [
            e for e in data
            if e.get("country") == "USD" and e.get("impact") == "High"
        ]
    except Exception as exc:
        logger.error(f"Gagal fetch ForexFactory: {exc}")
        return []


def parse_event_dt(event: dict) -> datetime | None:
    """Parse tanggal event ke datetime WIB."""
    raw = event.get("date", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"):
        try:
            return datetime.strptime(raw, fmt).astimezone(WIB)
        except ValueError:
            continue
    return None


# ─────────────────────────── FORMATTERS ────────────────────────
def header_banner() -> str:
    return (
        "╔══════════════════════════════╗\n"
        "║  🇺🇸  US ECONOMIC CALENDAR   ║\n"
        "║       ⭐⭐⭐  HIGH IMPACT      ║\n"
        "╚══════════════════════════════╝"
    )


def format_event_row(dt_wib: datetime, event: dict) -> str:
    time_str  = dt_wib.strftime("%H:%M WIB")
    name      = event.get("title", "Unknown")
    forecast  = event.get("forecast") or "—"
    previous  = event.get("previous") or "—"
    actual    = event.get("actual")

    row = f"  🔴 `{time_str}` *{name}*\n"
    if actual:
        row += f"       Actual: `{actual}` | Forecast: `{forecast}` | Prev: `{previous}`\n"
    else:
        row += f"       Forecast: `{forecast}` | Prev: `{previous}`\n"
    return row


def format_weekly(events: list) -> str:
    if not events:
        return (
            "⚠️ *Tidak ada event USD High Impact minggu ini.*\n"
            "_Data mungkin belum tersedia. Coba lagi nanti._"
        )

    # Group by date
    grouped: dict[str, list] = {}
    for ev in events:
        dt = parse_event_dt(ev)
        if not dt:
            continue
        key = dt.strftime("%Y-%m-%d")
        grouped.setdefault(key, []).append((dt, ev))

    now_str = datetime.now(WIB).strftime("%d/%m/%Y %H:%M WIB")
    lines = [
        header_banner(),
        "",
        f"📅 *Rekap Minggu: {_week_range_str()}*",
        f"🕐 _Update: {now_str}_",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    for date_key in sorted(grouped):
        day_events = sorted(grouped[date_key], key=lambda x: x[0])
        dt0 = day_events[0][0]
        day_en  = dt0.strftime("%A")
        day_id  = DAY_ID.get(day_en, day_en)
        date_lbl = dt0.strftime(f"{day_id}, %d %b %Y")

        lines.append(f"📌 *{date_lbl}*")
        for dt_wib, ev in day_events:
            lines.append(format_event_row(dt_wib, ev))
        lines.append("")

    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🔴 High Impact = Potensi volatilitas sangat tinggi",
        "⚠️ _Selalu pasang risk management sebelum news release!_",
    ]
    return "\n".join(lines)


def format_daily(events: list, target_dt: datetime) -> str:
    day_en  = target_dt.strftime("%A")
    day_id  = DAY_ID.get(day_en, day_en)
    date_lbl = target_dt.strftime(f"{day_id}, %d %b %Y")

    today_events = [
        (dt, ev)
        for ev in events
        if (dt := parse_event_dt(ev)) and dt.date() == target_dt.date()
    ]
    today_events.sort(key=lambda x: x[0])

    if not today_events:
        return (
            f"✅ *Tidak ada event USD High Impact hari ini*\n"
            f"_{date_lbl}_\n\n"
            "Aman untuk trading tanpa gangguan berita besar. 🟢"
        )

    lines = [
        f"🔔 *DAILY REMINDER — {date_lbl}*",
        "⭐⭐⭐ High Impact USD Events",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]
    for dt_wib, ev in today_events:
        lines.append(format_event_row(dt_wib, ev))

    lines += [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "⚠️ *Waspada volatilitas tinggi saat rilis!*",
        "_Gunakan SL yang proper dan jangan overlot._",
    ]
    return "\n".join(lines)


def _week_range_str() -> str:
    now = datetime.now(WIB)
    start = now - timedelta(days=now.weekday())          # Senin
    end   = start + timedelta(days=4)                    # Jumat
    return f"{start.strftime('%d')}–{end.strftime('%d %b %Y')}"


# ─────────────────────────── HANDLERS ──────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subs = load_subscribers()

    if chat_id not in subs:
        subs.append(chat_id)
        save_subscribers(subs)
        text = (
            "✅ *Selamat datang! Kamu sudah subscribe.*\n\n"
            "Kamu akan otomatis menerima:\n"
            "• 📅 *Rekap mingguan* setiap Senin pukul 07:00 WIB\n"
            "• 🔔 *Reminder harian* setiap hari pukul 07:30 WIB\n"
            "  _(hanya dikirim jika ada event hari itu)_\n\n"
            "📌 *Commands:*\n"
            "/week — Lihat event minggu ini\n"
            "/today — Lihat event hari ini\n"
            "/stop — Berhenti berlangganan\n"
            "/help — Bantuan"
        )
    else:
        text = (
            "ℹ️ Kamu sudah terdaftar!\n\n"
            "/week — Event minggu ini\n"
            "/today — Event hari ini\n"
            "/stop — Unsubscribe"
        )

    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_stop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subs = load_subscribers()
    if chat_id in subs:
        subs.remove(chat_id)
        save_subscribers(subs)
        await update.message.reply_text(
            "❌ Kamu telah *unsubscribe*.\n"
            "Ketik /start untuk subscribe lagi kapan saja.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("Kamu belum terdaftar. Ketik /start untuk mulai.")


async def cmd_week(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ _Mengambil data kalender ekonomi minggu ini..._", parse_mode="Markdown")
    events = fetch_this_week_events()
    text = format_weekly(events)
    await msg.edit_text(text, parse_mode="Markdown")


async def cmd_today(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ _Mengambil data hari ini..._", parse_mode="Markdown")
    events = fetch_this_week_events()
    now_wib = datetime.now(WIB)
    text = format_daily(events, now_wib)
    await msg.edit_text(text, parse_mode="Markdown")


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *BANTUAN BOT EKONOMI US*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "*Commands:*\n"
        "/start — Subscribe dan mulai terima reminder\n"
        "/stop  — Berhenti berlangganan\n"
        "/week  — Tampilkan event USD ⭐⭐⭐ minggu ini\n"
        "/today — Tampilkan event USD ⭐⭐⭐ hari ini\n"
        "/help  — Tampilkan pesan ini\n\n"
        "*Jadwal Otomatis:*\n"
        "🕖 Senin 07:00 WIB — Rekap mingguan\n"
        "🕖 Setiap hari 07:30 WIB — Reminder harian\n\n"
        "*Sumber data:* ForexFactory.com\n"
        "*Filter:* USD + High Impact (⭐⭐⭐) only"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ─────────────────────────── SCHEDULED JOBS ────────────────────
async def job_weekly_recap(bot: Bot):
    """Kirim rekap mingguan ke semua subscriber (Senin 07:00 WIB)."""
    logger.info("📅 Menjalankan job rekap mingguan...")
    subs = load_subscribers()
    if not subs:
        return
    events = fetch_this_week_events()
    text = format_weekly(events)
    for chat_id in subs:
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
            await asyncio.sleep(0.1)   # avoid rate limit
        except Exception as exc:
            logger.warning(f"Gagal kirim ke {chat_id}: {exc}")


async def job_daily_reminder(bot: Bot):
    """Kirim reminder harian (setiap hari 07:30 WIB, skip jika tidak ada event)."""
    now_wib = datetime.now(WIB)
    logger.info(f"🔔 Menjalankan daily reminder untuk {now_wib.strftime('%A %d %b')}...")
    subs = load_subscribers()
    if not subs:
        return
    events = fetch_this_week_events()
    text = format_daily(events, now_wib)

    # Hanya kirim jika ada event hari ini
    if "Tidak ada event" in text:
        logger.info("Tidak ada event hari ini, skip pengiriman.")
        return

    for chat_id in subs:
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
            await asyncio.sleep(0.1)
        except Exception as exc:
            logger.warning(f"Gagal kirim ke {chat_id}: {exc}")


# ─────────────────────────── MAIN ──────────────────────────────
def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Set BOT_TOKEN di file .env terlebih dahulu!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stop",  cmd_stop))
    app.add_handler(CommandHandler("week",  cmd_week))
    app.add_handler(CommandHandler("today", cmd_today))
    app.add_handler(CommandHandler("help",  cmd_help))

    # Scheduler
    scheduler = AsyncIOScheduler(timezone="Asia/Jakarta")

    # Senin 07:00 WIB — rekap mingguan
    scheduler.add_job(
        job_weekly_recap,
        trigger="cron",
        day_of_week="mon",
        hour=7,
        minute=0,
        args=[app.bot],
        id="weekly_recap",
    )

    # Setiap hari 07:30 WIB — reminder harian
    scheduler.add_job(
        job_daily_reminder,
        trigger="cron",
        day_of_week="mon-fri",   # hanya weekday (market buka)
        hour=7,
        minute=30,
        args=[app.bot],
        id="daily_reminder",
    )

    scheduler.start()
    logger.info("✅ Bot started! Scheduler aktif.")
    logger.info("   📅 Weekly recap : Senin 07:00 WIB")
    logger.info("   🔔 Daily reminder: Senin–Jumat 07:30 WIB")

    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()

# 📊 US Economic News Bot — High Impact ⭐⭐⭐

Bot Telegram yang otomatis mengirim reminder berita ekonomi AS dengan dampak tinggi (3 bintang).

- Fitur
- 📅 **Rekap mingguan** setiap Senin pukul 07:00 WIB
- 🔔 **Reminder harian** Senin–Jumat pukul 07:30 WIB *(hanya jika ada event hari itu)*
- 🔍 Filter khusus **USD + High Impact** dari ForexFactory
- ℹ️ Menampilkan: Nama event, waktu WIB, Forecast, Previous, Actual

## Commands Bot
| Command | Fungsi |
|---------|--------|
| `/start` | Subscribe & mulai terima reminder |
| `/stop`  | Berhenti berlangganan |
| `/week`  | Lihat event USD ⭐⭐⭐ minggu ini |
| `/today` | Lihat event USD ⭐⭐⭐ hari ini |
| `/help`  | Bantuan |

---

## Setup & Instalasi

### 1. Buat Bot di Telegram
1. Buka Telegram, cari **@BotFather**
2. Ketik `/newbot`
3. Ikuti instruksi, beri nama dan username bot
4. Salin **token** yang diberikan (format: `123456:ABC-xxx...`)

### 2. Install Python (versi 3.11+)
```bash
python --version   # cek versi, harus 3.11+
```

### 3. Clone / Download file ini
Taruh semua file dalam satu folder, misal `econ_bot/`

### 4. Buat Virtual Environment (disarankan)
```bash
cd econ_bot
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### 5. Install dependencies
```bash
pip install -r requirements.txt
```

### 6. Konfigurasi token
```bash
# Salin file contoh
cp .env.example .env

# Edit .env, isi BOT_TOKEN dengan token dari BotFather
```

Isi file `.env`:
```
BOT_TOKEN=1234567890:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 7. Jalankan bot
```bash
python bot.py
```

Seharusnya muncul output:
```
✅ Bot started! Scheduler aktif.
   📅 Weekly recap : Senin 07:00 WIB
   🔔 Daily reminder: Senin–Jumat 07:30 WIB
```

### 8. Test bot
- Buka bot kamu di Telegram
- Ketik `/start` → Subscribe
- Ketik `/week` → Test ambil data minggu ini
- Ketik `/today` → Test data hari ini

---

## Menjalankan 24/7

### Opsi A: VPS / Server Linux (disarankan)

Gunakan `screen` agar bot tetap jalan setelah terminal ditutup:
```bash
screen -S econbot
python bot.py
# Tekan Ctrl+A lalu D untuk detach
```

Atau buat systemd service:
```ini
# /etc/systemd/system/econbot.service
[Unit]
Description=US Economic News Telegram Bot
After=network.target

[Service]
WorkingDirectory=/path/to/econ_bot
ExecStart=/path/to/econ_bot/venv/bin/python bot.py
Restart=always
User=ubuntu

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable econbot
sudo systemctl start econbot
```

### Opsi B: Railway / Render (gratis)
- Upload ke GitHub repository
- Deploy di [Railway.app](https://railway.app) atau [Render.com](https://render.com)
- Set environment variable `BOT_TOKEN`
- Start command: `python bot.py`

### Opsi C: PC rumah (tidak disarankan untuk 24/7)

---

## Sumber Data
- **ForexFactory** JSON feed (`nfs.faireconomy.media`)
- Update otomatis setiap minggu dari sumber

## Catatan
- Data tersedia mulai Minggu malam untuk minggu berikutnya
- Waktu ditampilkan dalam **WIB (UTC+7)**
- Hanya event **USD + High Impact** yang ditampilkan

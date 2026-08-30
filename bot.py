import os
import re
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

import config
from excel_manager import ExcelManager

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("MoneyTrackingBot")

def get_bot_em(user_id: Optional[int] = None) -> ExcelManager:
    """
    Get ExcelManager mapped to the primary user's private account.
    """
    target_user = config.TELEGRAM_PRIMARY_USER_ID or "mghazalinurrahman939@gmail.com"
    return ExcelManager(user_id=target_user)

# Indonesian Word Numbers Map
TEXT_NUMS = {
    "nol": 0, "satu": 1, "se": 1, "dua": 2, "tiga": 3, "empat": 4,
    "lima": 5, "enam": 6, "tujuh": 7, "delapan": 8, "sembilan": 9,
    "sepuluh": 10, "sebelas": 11, "setengah": 0.5
}

# -------------------------------------------------------------
# AUTH & NUMBER PARSING HELPERS
# -------------------------------------------------------------
def is_user_allowed(user_id: int) -> bool:
    if not config.ALLOWED_TELEGRAM_USERS:
        return True
    return user_id in config.ALLOWED_TELEGRAM_USERS

def format_idr(amount: float) -> str:
    return f"Rp {amount:,.0f}".replace(",", ".")

def extract_amount_and_clean_text(text: str) -> Tuple[float, str]:
    s = text.lower().strip()
    s = re.sub(r"^(rp\.?|\$)\s*", "", s)
    s = re.sub(r"[\.,]00(\s|$)", " ", s)

    total = 0.0
    matched_spans = []

    # 1. Match 'X juta' / 'X jt'
    juta_regex = r"([0-9\.\,]+|satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|sepuluh|sebelas|setengah)\s*(juta|jt)"
    for m in re.finditer(juta_regex, s):
        val_raw = m.group(1).replace(",", ".")
        val = TEXT_NUMS.get(val_raw, float(val_raw) if val_raw.replace(".", "").isdigit() else 1.0)
        total += val * 1_000_000
        matched_spans.append(m.span())

    # 2. Match 'X ratus ribu' or 'X ratus'
    ratus_regex = r"([0-9\.\,]+|se|satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan)\s*(ratus)\s*(ribu|rb)?"
    for m in re.finditer(ratus_regex, s):
        val_raw = m.group(1).replace(",", ".")
        val = TEXT_NUMS.get(val_raw, float(val_raw) if val_raw.replace(".", "").isdigit() else 1.0)
        is_ribu = bool(m.group(3))
        multiplier = 100_000 if is_ribu else 100
        total += val * multiplier
        matched_spans.append(m.span())

    # 3. Match 'X puluh ribu'
    puluh_regex = r"([0-9\.\,]+|se|satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan)\s*(puluh)\s*(ribu|rb)?"
    for m in re.finditer(puluh_regex, s):
        val_raw = m.group(1).replace(",", ".")
        val = TEXT_NUMS.get(val_raw, float(val_raw) if val_raw.replace(".", "").isdigit() else 1.0)
        is_ribu = bool(m.group(3))
        multiplier = 10_000 if is_ribu else 10
        total += val * multiplier
        matched_spans.append(m.span())

    # 4. Match 'X ribu' or 'X rb' or 'X k'
    ribu_regex = r"([0-9\.\,]+|se|satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|sepuluh|sebelas)\s*(ribu|rb|k)"
    for m in re.finditer(ribu_regex, s):
        val_raw = m.group(1).replace(",", ".")
        if "." in val_raw:
            cleaned_dots = val_raw.replace(".", "").replace(",", "")
            if len(cleaned_dots) >= 4:
                val = float(cleaned_dots)
                total += val
                matched_spans.append(m.span())
                continue
        val = TEXT_NUMS.get(val_raw, float(val_raw) if val_raw.replace(".", "").isdigit() else 1.0)
        total += val * 1_000
        matched_spans.append(m.span())

    # 5. Direct plain numbers
    if total == 0:
        plain_regex = r"([0-9]+[\.0-9\,]*)"
        for m in re.finditer(plain_regex, s):
            raw_num = m.group(1)
            raw_num = re.sub(r"[\.,]00$", "", raw_num)
            cleaned = raw_num.replace(".", "").replace(",", "")
            if cleaned.isdigit() and len(cleaned) >= 2:
                total += float(cleaned)
                matched_spans.append(m.span())
                break

    cleaned_text = s
    for start, end in sorted(matched_spans, reverse=True):
        cleaned_text = cleaned_text[:start] + " " + cleaned_text[end:]
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

    return total, cleaned_text

def parse_add_installment(text: str) -> Optional[dict]:
    text_clean = text.strip()
    
    if "cicilan" not in text_clean.lower():
        return None

    tenor_match = re.search(r"(?:tenor|selama)?\s*([0-9]+)\s*(?:bln|bulan)\b", text_clean, re.IGNORECASE)
    if not tenor_match:
        return None
    tenor = int(tenor_match.group(1))

    body = text_clean

    due_day = 10
    due_match = re.search(r"(?:jatuh\s+tempo|tempo|due|tgl|tanggal)\s*(?:setiap\s+)?(?:tgl|tanggal)?\s*([0-9]{1,2})\b", body, re.IGNORECASE)
    if due_match:
        val = int(due_match.group(1))
        if 1 <= val <= 31:
            due_day = val
            body = body[:due_match.start()] + " " + body[due_match.end():]

    body = body[:tenor_match.start()] + " " + body[tenor_match.end():]
    body = re.sub(r"\s+", " ", body).strip()

    amount, name_and_provider = extract_amount_and_clean_text(body)
    if not amount or amount <= 0 or tenor <= 0:
        return None

    name_and_provider = re.sub(r"\b(tambah\s+cicilan|tambah|cicilan|sebesar|sebanyak|senilai|selama|tenor|jatuh tempo|tempo|tanggal|tgl|setiap|di|ke|untuk|buat)\b", "", name_and_provider, flags=re.IGNORECASE).strip()
    name_and_provider = re.sub(r"\s+", " ", name_and_provider).strip()

    provider = "Finance / Bank"
    p_match = re.search(r"\[(.*?)\]", name_and_provider)
    if p_match:
        provider = p_match.group(1).strip()
        name_and_provider = name_and_provider.replace(p_match.group(0), "").strip()

    nama = name_and_provider.strip().title() or "Cicilan"
    total = amount * tenor
    return {
        "nama": nama,
        "penyedia": provider,
        "cicilan_bulanan": amount,
        "tenor": tenor,
        "tgl_jatuh_tempo": due_day,
        "total_pinjaman": total
    }

def parse_text_transaction(
    text: str,
    master_wallets: list,
    master_cats: list,
    active_installments: list = None
) -> Optional[dict]:
    raw_lower = text.lower().strip()

    amount, rest = extract_amount_and_clean_text(raw_lower)
    if not amount or amount <= 0:
        return None

    income_keywords = [
        "uang masuk", "masuk", "pemasukan", "pemasukkan", "income", "in",
        "dividen", "profit", "cuan", "jual saham", "jual crypto", "jual emas",
        "gaji", "terima", "dapat", "tf masuk", "transfer masuk", "topup"
    ]
    expense_keywords = [
        "uang pengeluaran", "pengeluaran", "keluar", "expense", "out",
        "bayar", "cicilan", "angsuran", "beli saham", "beli crypto", "beli emas",
        "beli", "belanja", "tarik", "kredit", "bayar hutang", "utang"
    ]

    is_income = False
    is_expense = False

    for kw in income_keywords:
        if kw in raw_lower:
            is_income = True
            break

    for kw in expense_keywords:
        if kw in raw_lower:
            is_expense = True
            break

    if is_income and not is_expense:
        tipe = "Pemasukan"
    elif is_expense and not is_income:
        tipe = "Pengeluaran"
    elif "uang masuk" in raw_lower or "masuk" in raw_lower:
        tipe = "Pemasukan"
    elif "uang pengeluaran" in raw_lower or "keluar" in raw_lower or "bayar" in raw_lower or "cicilan" in raw_lower:
        tipe = "Pengeluaran"
    else:
        tipe = "Pengeluaran"

    action_words = [
        "uang masuk", "uang pengeluaran", "pemasukan", "pemasukkan", "pengeluaran",
        "masuk", "keluar", "income", "expense", "bayar", "in", "out"
    ]
    cleaned_desc = rest
    for aw in action_words:
        cleaned_desc = re.sub(rf"\b{re.escape(aw)}\b", "", cleaned_desc, flags=re.IGNORECASE).strip()

    filler_words = ["sebesar", "sebanyak", "senilai", "di", "ke", "dari", "pada", "buat", "untuk", "via", "lewat"]
    for fw in filler_words:
        cleaned_desc = re.sub(rf"\b{re.escape(fw)}\b", "", cleaned_desc, flags=re.IGNORECASE).strip()

    chosen_wallet = "Cash / Tunai"
    
    wallet_match = re.search(r"\[(.*?)\]", cleaned_desc)
    if wallet_match:
        w_cand = wallet_match.group(1).strip()
        cleaned_desc = cleaned_desc.replace(wallet_match.group(0), "").strip()
        chosen_wallet = w_cand
    else:
        words = cleaned_desc.split()
        found_wallet = None
        for i, word in enumerate(words):
            w_clean = word.lower().replace("[", "").replace("]", "")
            for mw in master_wallets:
                if mw.lower() == w_clean or w_clean == mw.lower().split()[0]:
                    found_wallet = mw
                    words.pop(i)
                    break
            if found_wallet:
                break
        
        if found_wallet:
            chosen_wallet = found_wallet
            cleaned_desc = " ".join(words).strip()
        elif words and words[-1].lower() in ["seabank", "bca", "mandiri", "bri", "bni", "jago", "gopay", "ovo", "dana", "shopeepay", "cash", "tunai"]:
            raw_w = words.pop(-1)
            chosen_wallet = "SeaBank" if raw_w.lower() == "seabank" else raw_w.upper()
            cleaned_desc = " ".join(words).strip()

    cleaned_desc = re.sub(r"\s+", " ", cleaned_desc).strip()

    chosen_cat = "Gaji" if tipe == "Pemasukan" else "Lain-lain"
    linked_installment_id = None

    desc_check = (cleaned_desc + " " + raw_lower).lower()

    if re.search(r"\b(saham|dividen|crypto|kripto|bitcoin|btc|eth|emas|reksa dana|reksadana|investasi|cuan|trading)\b", desc_check):
        if tipe == "Pemasukan":
            chosen_cat = "Investasi / Dividen"
        else:
            chosen_cat = "Investasi & Aset"
    elif re.search(r"\b(cicilan|angsuran|kpr|leasing|pinjol|paylater|hutang|utang|kredit)\b", desc_check):
        chosen_cat = "Cicilan & Hutang"
        if active_installments:
            for inst in active_installments:
                if inst["nama"].lower() in desc_check or inst["penyedia"].lower() in desc_check:
                    linked_installment_id = inst["id_cicilan"]
                    break
    elif re.search(r"\b(makan|minum|kopi|cafe|kafe|resto|warteg|lunch|dinner|sarapan|jajan|snack|gofood|grabfood)\b", desc_check):
        chosen_cat = "Makanan & Minuman"
    elif re.search(r"\b(bensin|pertalite|pertamax|solar|gojek|grab|maxim|tol|parkir|servis|service|oli)\b", desc_check):
        chosen_cat = "Transportasi & Bensin"
    elif re.search(r"\b(gaji|salary|bonus|thr|upah|freelance|proyek|project)\b", desc_check):
        chosen_cat = "Gaji"
    elif re.search(r"\b(belanja|supermarket|indomaret|alfamart|pasar|sembako|sabun|shopee|tokopedia)\b", desc_check):
        chosen_cat = "Belanja Bulanan"
    elif re.search(r"\b(listrik|pln|air|pdam|wifi|indihome|pulsa|paket|kuota|iuran|bpjs|sewa|kontrakan)\b", desc_check):
        chosen_cat = "Tagihan & Utilitas"

    if not cleaned_desc:
        if chosen_cat == "Cicilan & Hutang":
            cleaned_desc = f"Bayar Cicilan ({chosen_wallet})"
        elif chosen_cat == "Investasi / Dividen":
            cleaned_desc = f"Uang Masuk Investasi/Saham ({chosen_wallet})"
        else:
            cleaned_desc = f"{tipe} {chosen_wallet}"

    final_desc = cleaned_desc.capitalize()

    return {
        "tipe": tipe,
        "jumlah": amount,
        "keterangan": final_desc,
        "kategori": chosen_cat,
        "akun": chosen_wallet,
        "id_cicilan": linked_installment_id
    }

# -------------------------------------------------------------
# COMMAND HANDLERS
# -------------------------------------------------------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if not is_user_allowed(user_id):
        await update.message.reply_text(
            f"⛔ *Akses Ditolak*\n\nUser ID Telegram Anda (`{user_id}`) belum terdaftar di whitelist.\n"
            f"Buka Web Dashboard di tab *Pengaturan & Bot* untuk mengizinkan akun Anda.",
            parse_mode="Markdown",
        )
        return

    welcome_text = (
        f"👋 Halo, *{user.first_name}*!\n\n"
        f"Bot Telegram Anda terhubung langsung ke akun privat Google Anda: *{config.TELEGRAM_PRIMARY_USER_ID}*.\n\n"
        f"📌 *Contoh Format Catat:*\n"
        f"• `pemasukan sebesar 1.4 juta di seabank`\n"
        f"• `cicilan sebesar 103.333 ribu selama 12 bulan jatuh tempo setiap tanggal 10`\n"
        f"• `uang masuk saham 500 ribu bca`\n"
        f"• `keluar 50rb makan siang`\n\n"
        f"📌 *Perintah Menu:*\n"
        f"• `/rekap` : Ringkasan bulanan\n"
        f"• `/saldo` : Cek saldo seluruh rekening & dompet\n"
        f"• `/aset` : Cek portofolio saham, crypto & emas\n"
        f"• `/cicilan` : Lihat daftar cicilan & jatuh tempo\n"
        f"• `/id` : Cek User ID Telegram Anda"
    )

    keyboard = [
        [
            InlineKeyboardButton("📊 Rekap Bulan Ini", callback_data="btn_rekap"),
            InlineKeyboardButton("💰 Cek Saldo", callback_data="btn_saldo"),
        ],
        [
            InlineKeyboardButton("📈 Portofolio Aset", callback_data="btn_aset"),
            InlineKeyboardButton("💳 Daftar Cicilan", callback_data="btn_cicilan"),
        ],
        [
            InlineKeyboardButton("🕒 5 Transaksi Terakhir", callback_data="btn_history"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, context)

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"🆔 *User ID Telegram Anda:* `{user_id}`\n\n"
        f"Gunakan ID ini pada setting keamanan di Web Dashboard atau `.env`.",
        parse_mode="Markdown"
    )

async def cmd_rekap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user_allowed(user_id):
        return

    em = get_bot_em(user_id)
    now = datetime.now()
    summary = em.get_monthly_summary(month=now.month, year=now.year)
    
    month_names = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    periode = f"{month_names[summary['month']]} {summary['year']}"

    rekap_text = (
        f"📊 *REKAP KEUANGAN BULAN {periode.upper()}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 *Pemasukan:* {format_idr(summary['total_income'])}\n"
        f"🔴 *Pengeluaran:* {format_idr(summary['total_expense'])}\n"
        f"💳 *Beban Cicilan:* {format_idr(summary['active_installment_burden'])}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ *Net Cashflow:* *{format_idr(summary['net_cashflow'])}*\n\n"
        f"🏷 *Top Pengeluaran Kategori:*\n"
    )

    if summary["category_breakdown"]:
        for kat, amt in sorted(summary["category_breakdown"].items(), key=lambda x: x[1], reverse=True)[:5]:
            rekap_text += f" • {kat}: {format_idr(amt)}\n"
    else:
        rekap_text += " • _Belum ada pengeluaran_\n"

    rekap_text += f"\n💎 *Total Net Worth:* {format_idr(summary['total_net_worth'])}"

    if update.message:
        await update.message.reply_text(rekap_text, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(rekap_text, parse_mode="Markdown")

async def cmd_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user_allowed(user_id):
        return

    em = get_bot_em(user_id)
    summary = em.get_monthly_summary()
    balances = summary.get("wallet_balances", {})

    saldo_text = "💰 *ESTIMASI SALDO REKENING & DOMPET*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    total = 0
    for wallet, amt in balances.items():
        total += amt
        saldo_text += f"• *{wallet}*: {format_idr(amt)}\n"
    
    saldo_text += f"━━━━━━━━━━━━━━━━━━━━━━\n💵 *Total Kas Cair:* *{format_idr(total)}*"

    if update.message:
        await update.message.reply_text(saldo_text, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(saldo_text, parse_mode="Markdown")

async def cmd_aset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user_allowed(user_id):
        return

    em = get_bot_em(user_id)
    assets = em.get_assets()
    if not assets:
        msg = "📈 Belum ada portofolio aset yang tercatat.\nTambahkan aset saham, crypto, atau emas via Web Dashboard."
        if update.message:
            await update.message.reply_text(msg)
        elif update.callback_query:
            await update.callback_query.message.reply_text(msg)
        return

    total_val = sum(a["nilai_saat_ini"] for a in assets)
    total_cost = sum(a["total_modal"] for a in assets)
    total_pnl = total_val - total_cost
    ret_pct = round((total_pnl / total_cost * 100), 2) if total_cost > 0 else 0.0
    pnl_sign = "+" if total_pnl >= 0 else ""

    text = (
        f"📈 *PORTOFOLIO ASET & INVESTASI*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 *Total Nilai Pasar:* *{format_idr(total_val)}*\n"
        f"📥 *Total Modal Masuk:* {format_idr(total_cost)}\n"
        f"🚀 *Floating PnL:* *{pnl_sign}{format_idr(total_pnl)} ({pnl_sign}{ret_pct}%)*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 *Rincian Aset:*\n"
    )

    for a in assets:
        sign = "+" if a["pnl"] >= 0 else ""
        text += (
            f"• *{a['nama']}* ({a['kategori']})\n"
            f"   {a['platform']} • {a['unit']}\n"
            f"   Nilai: *{format_idr(a['nilai_saat_ini'])}* ({sign}{a['return_pct']}%)\n\n"
        )

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")

async def cmd_cicilan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user_allowed(user_id):
        return

    em = get_bot_em(user_id)
    installments = em.get_installments(status="Aktif")
    if not installments:
        msg = "🎉 *Selamat!* Tidak ada cicilan aktif saat ini.\nKetik: `cicilan sebesar 103.333 ribu selama 12 bulan jatuh tempo setiap tanggal 10` untuk mendaftarkan cicilan baru."
        if update.message:
            await update.message.reply_text(msg, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.message.reply_text(msg, parse_mode="Markdown")
        return

    msg = "💳 *DAFTAR CICILAN AKTIF*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    keyboard = []

    for inst in installments:
        msg += (
            f"📌 *{inst['nama']}* ({inst['penyedia']})\n"
            f" • Cicilan: *{format_idr(inst['cicilan_bulanan'])}/bln*\n"
            f" • Progress: Bulan ke-*{inst['cicilan_ke']}* dari *{inst['tenor']}* ({inst['progress_pct']}%)\n"
            f" • Sisa Hutang: {format_idr(inst['sisa_hutang'])}\n"
            f" • Sisa Tenor: *{inst['sisa_tenor']} Bulan*\n"
            f" • 📅 *Jatuh Tempo: Setiap tanggal {inst['tgl_jatuh_tempo']}*\n\n"
        )
        keyboard.append([
            InlineKeyboardButton(
                f"✅ Bayar {inst['nama']} ({format_idr(inst['cicilan_bulanan'])})",
                callback_data=f"pay_{inst['id_cicilan']}"
            )
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)

async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user_allowed(user_id):
        return

    em = get_bot_em(user_id)
    trxs = em.get_transactions()[:5]
    if not trxs:
        msg = "Belum ada riwayat transaksi."
        if update.message:
            await update.message.reply_text(msg)
        elif update.callback_query:
            await update.callback_query.message.reply_text(msg)
        return

    msg = "🕒 *5 TRANSAKSI TERAKHIR*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for t in trxs:
        icon = "🟢" if t["tipe"] == "Pemasukan" else "🔴"
        msg += (
            f"{icon} *{format_idr(t['jumlah'])}* ({t['kategori']})\n"
            f"   _{t['tanggal']}_ • {t['akun']} • {t['keterangan'] or '-'}\n\n"
        )

    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode="Markdown")

# -------------------------------------------------------------
# MESSAGE & CALLBACK HANDLERS
# -------------------------------------------------------------
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user_allowed(user_id):
        await update.message.reply_text(
            f"⛔ User ID Anda (`{user_id}`) belum diizinkan.\n"
            f"Buka Web Dashboard di tab *Pengaturan & Bot* untuk mengizinkan akun Anda.",
            parse_mode="Markdown"
        )
        return

    em = get_bot_em(user_id)
    text = update.message.text.strip()

    # 1. Check if it is an installment registration
    add_inst = parse_add_installment(text)
    if add_inst:
        try:
            created_inst = em.add_installment(
                nama=add_inst["nama"],
                penyedia=add_inst["penyedia"],
                total_pinjaman=add_inst["total_pinjaman"],
                cicilan_bulanan=add_inst["cicilan_bulanan"],
                tenor=add_inst["tenor"],
                cicilan_ke=0,
                tgl_jatuh_tempo=add_inst["tgl_jatuh_tempo"]
            )
            msg = (
                f"✅ *CICILAN BARU BERHASIL DIDAFTARKAN!*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 *Nama Cicilan:* {created_inst['nama']}\n"
                f"🏦 *Penyedia:* {created_inst['penyedia']}\n"
                f"💵 *Cicilan / Bulan:* *{format_idr(created_inst['cicilan_bulanan'])}*\n"
                f"⏳ *Tenor:* {created_inst['tenor']} Bulan\n"
                f"💰 *Total Pokok Pinjaman:* {format_idr(created_inst['total_pinjaman'])}\n"
                f"📅 *Jatuh Tempo:* Setiap tanggal *{created_inst['tgl_jatuh_tempo']}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💾 _Tersimpan di Sheet Cicilan & Dashboard. Untuk bayar cicilan tiap bulan, ketik: `bayar cicilan {created_inst['nama']}` atau via menu `/cicilan`._"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
            return
        except Exception as e:
            await update.message.reply_text(f"❌ Gagal menambah cicilan: {str(e)}")
            return

    # 2. Regular Transaction parsing
    master = em.get_master_data()
    all_cats = master["income_categories"] + master["expense_categories"]
    wallets = master["wallets"]
    active_installments = em.get_installments(status="Aktif")

    parsed = parse_text_transaction(text, wallets, all_cats, active_installments)
    if not parsed:
        await update.message.reply_text(
            "❓ Format pesan belum dikenali.\n\n"
            "Contoh format yang didukung:\n"
            "• `pemasukan sebesar 1.4 juta di seabank`\n"
            "• `cicilan sebesar 103.333 ribu selama 12 bulan jatuh tempo setiap tanggal 10`\n"
            "• `uang masuk saham 500 ribu bca`\n"
            "• `keluar 50rb makan siang`\n\n"
            "Ketik `/help` untuk panduan lengkap.",
            parse_mode="Markdown"
        )
        return

    today_str = datetime.now().strftime("%Y-%m-%d")

    installment_note = ""
    if parsed.get("id_cicilan"):
        try:
            pay_res = em.pay_installment(
                installment_id=parsed["id_cicilan"],
                payment_date=today_str,
                wallet=parsed["akun"],
                note=parsed["keterangan"]
            )
            inst = pay_res["installment"]
            installment_note = f"\n💳 *Status Cicilan:* Bulan ke-{inst['cicilan_ke']} dari {inst['tenor']} (Sisa {inst['sisa_tenor']} bln / {format_idr(inst['sisa_hutang'])})"
        except Exception:
            em.add_transaction(
                tanggal=today_str,
                tipe=parsed["tipe"],
                kategori=parsed["kategori"],
                akun=parsed["akun"],
                jumlah=parsed["jumlah"],
                keterangan=parsed["keterangan"],
            )
    else:
        em.add_transaction(
            tanggal=today_str,
            tipe=parsed["tipe"],
            kategori=parsed["kategori"],
            akun=parsed["akun"],
            jumlah=parsed["jumlah"],
            keterangan=parsed["keterangan"],
        )

    reply_msg = (
        f"✅ *{parsed['tipe'].upper()} BERHASIL DICATAT!*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 *Jumlah:* *{format_idr(parsed['jumlah'])}*\n"
        f"🏷 *Kategori:* {parsed['kategori']}\n"
        f"🏦 *Akun/Dompet:* {parsed['akun']}\n"
        f"📝 *Keterangan:* {parsed['keterangan']}\n"
        f"📅 *Tanggal:* {today_str}"
        f"{installment_note}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💾 _Tersimpan di Akun ({config.TELEGRAM_PRIMARY_USER_ID}) & Dashboard Web!_"
    )
    await update.message.reply_text(reply_msg, parse_mode="Markdown")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if not is_user_allowed(user_id):
        await query.answer("Akses Ditolak", show_alert=True)
        return

    await query.answer()
    em = get_bot_em(user_id)

    data = query.data
    if data == "btn_rekap":
        await cmd_rekap(update, context)
    elif data == "btn_saldo":
        await cmd_saldo(update, context)
    elif data == "btn_aset":
        await cmd_aset(update, context)
    elif data == "btn_cicilan":
        await cmd_cicilan(update, context)
    elif data == "btn_history":
        await cmd_history(update, context)
    elif data.startswith("pay_"):
        inst_id = data.replace("pay_", "")
        try:
            res = em.pay_installment(
                installment_id=inst_id,
                wallet="BCA",
                note="Pembayaran cicilan via Telegram Bot"
            )
            inst = res["installment"]
            msg = (
                f"✅ *PEMBAYARAN CICILAN BERHASIL DICATAT!*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 *Cicilan:* {inst['nama']}\n"
                f"💵 *Nominal:* {format_idr(inst['cicilan_bulanan'])}\n"
                f"📈 *Progress Sekarang:* Bulan ke-*{inst['cicilan_ke']}* dari *{inst['tenor']}*\n"
                f"⏳ *Sisa Tenor:* {inst['sisa_tenor']} Bulan\n"
                f"💰 *Sisa Pokok:* {format_idr(inst['sisa_hutang'])}\n"
                f"📅 *Jatuh Tempo:* Setiap tanggal {inst['tgl_jatuh_tempo']}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💾 _Transaksi pengeluaran otomatis dicatat di Excel._"
            )
            await query.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await query.message.reply_text(f"❌ Gagal memproses cicilan: {str(e)}")

# -------------------------------------------------------------
# BOT FACTORY
# -------------------------------------------------------------
def create_bot_app() -> Optional[Application]:
    token = config.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning("[TelegramBot] TELEGRAM_BOT_TOKEN is not set.")
        return None

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("rekap", cmd_rekap))
    app.add_handler(CommandHandler("saldo", cmd_saldo))
    app.add_handler(CommandHandler("aset", cmd_aset))
    app.add_handler(CommandHandler("investasi", cmd_aset))
    app.add_handler(CommandHandler("cicilan", cmd_cicilan))
    app.add_handler(CommandHandler("history", cmd_history))

    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    return app

if __name__ == "__main__":
    bot_app = create_bot_app()
    if bot_app:
        print("[TelegramBot] Running Telegram Bot polling...")
        bot_app.run_polling()
    else:
        print("[TelegramBot] TELEGRAM_BOT_TOKEN is not set in .env")

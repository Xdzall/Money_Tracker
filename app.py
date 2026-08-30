import os
import asyncio
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

import config
from excel_manager import ExcelManager
from bot import create_bot_app

# --- Lifespan Context Manager for Telegram Bot 24/7 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    bot_app = None
    config.reload_config()
    token = config.TELEGRAM_BOT_TOKEN
    if token:
        try:
            print(f"🤖 [Telegram Bot] Memulai bot polling di background 24/7...")
            bot_app = create_bot_app()
            if bot_app:
                await bot_app.initialize()
                await bot_app.start()
                await bot_app.updater.start_polling()
                print("✅ [Telegram Bot] Bot aktif dan siap menerima pesan!")
        except Exception as e:
            print(f"⚠️  [Telegram Bot] Startup error: {e}")
    else:
        print("ℹ️  [Telegram Bot] Token belum terpasang.")
    
    yield
    
    # Clean shutdown
    if bot_app:
        try:
            print("🛑 [Telegram Bot] Menghentikan bot polling...")
            await bot_app.updater.stop()
            await bot_app.stop()
            await bot_app.shutdown()
        except Exception as e:
            print(f"⚠️  [Telegram Bot] Shutdown error: {e}")

app = FastAPI(
    title="Money Tracking App & Dashboard",
    version="1.3.0",
    lifespan=lifespan
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

em = ExcelManager()

# --- Pydantic Models for Validation ---
class TransactionCreate(BaseModel):
    tanggal: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    tipe: str = "Pengeluaran" # "Pemasukan" or "Pengeluaran"
    kategori: str
    akun: str = "BCA"
    jumlah: float = Field(gt=0, description="Nominal transaksi harus lebih dari 0")
    keterangan: Optional[str] = ""

class InstallmentCreate(BaseModel):
    nama: str
    penyedia: str = "Bank/Multifinance"
    total_pinjaman: float = Field(gt=0)
    cicilan_bulanan: float = Field(gt=0)
    tenor: int = Field(gt=0, description="Total tenor dalam bulan")
    cicilan_ke: int = Field(default=0, ge=0)
    tgl_jatuh_tempo: int = Field(default=1, ge=1, le=31)

class InstallmentPayRequest(BaseModel):
    payment_date: Optional[str] = None
    wallet: str = "BCA"
    note: Optional[str] = ""

class AssetCreate(BaseModel):
    nama: str
    kategori: str = "Saham" # Saham, Crypto, Emas, Reksa Dana, Lainnya
    platform: str = "Ajaib"
    unit: str = "1"
    total_modal: float = Field(gt=0, description="Modal pembelian total dalam Rp")
    nilai_saat_ini: float = Field(gt=0, description="Estimasi nilai pasar saat ini dalam Rp")
    catatan: Optional[str] = ""

class AssetUpdate(BaseModel):
    nilai_saat_ini: Optional[float] = None
    unit: Optional[str] = None
    total_modal: Optional[float] = None
    catatan: Optional[str] = None

class MasterItemCreate(BaseModel):
    name: str
    tipe: Optional[str] = "Pengeluaran"

class TelegramConfigSave(BaseModel):
    bot_token: str
    allowed_users: Optional[str] = ""

# --- Web UI Route ---
@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"now": datetime.now()}
    )

# --- API Endpoints: Summary & Transactions ---
@app.get("/api/summary")
async def get_summary(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000, le=2100)
):
    try:
        data = em.get_monthly_summary(month=month, year=year)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transactions")
async def list_transactions(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    tipe: Optional[str] = Query(None),
    kategori: Optional[str] = Query(None),
    akun: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    try:
        transactions = em.get_transactions(
            month=month, year=year, tipe=tipe, kategori=kategori, akun=akun, search=search
        )
        return {"status": "success", "count": len(transactions), "data": transactions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transactions")
async def create_transaction(item: TransactionCreate):
    try:
        trx = em.add_transaction(
            tanggal=item.tanggal,
            tipe=item.tipe,
            kategori=item.kategori,
            akun=item.akun,
            jumlah=item.jumlah,
            keterangan=item.keterangan or "",
        )
        return {"status": "success", "message": "Transaksi berhasil disimpan", "data": trx}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/transactions/{trx_id}")
async def remove_transaction(trx_id: str):
    success = em.delete_transaction(trx_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    return {"status": "success", "message": "Transaksi berhasil dihapus"}

# --- API Endpoints: Installments / Cicilan ---
@app.get("/api/installments")
async def list_installments(status: Optional[str] = Query(None)):
    try:
        data = em.get_installments(status=status)
        return {"status": "success", "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/installments")
async def create_installment(item: InstallmentCreate):
    try:
        res = em.add_installment(
            nama=item.nama,
            penyedia=item.penyedia,
            total_pinjaman=item.total_pinjaman,
            cicilan_bulanan=item.cicilan_bulanan,
            tenor=item.tenor,
            cicilan_ke=item.cicilan_ke,
            tgl_jatuh_tempo=item.tgl_jatuh_tempo,
        )
        return {"status": "success", "message": "Data cicilan berhasil ditambahkan", "data": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/installments/{installment_id}/pay")
async def pay_installment_endpoint(installment_id: str, req: InstallmentPayRequest):
    try:
        res = em.pay_installment(
            installment_id=installment_id,
            payment_date=req.payment_date,
            wallet=req.wallet,
            note=req.note or ""
        )
        return {"status": "success", "message": "Pembayaran cicilan berhasil dicatat", "data": res}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/installments/{installment_id}")
async def remove_installment(installment_id: str):
    success = em.delete_installment(installment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Data cicilan tidak ditemukan")
    return {"status": "success", "message": "Data cicilan berhasil dihapus"}

# --- API Endpoints: Assets & Investments (Saham, Crypto, Emas) ---
@app.get("/api/assets")
async def list_assets(kategori: Optional[str] = Query(None)):
    try:
        data = em.get_assets(kategori=kategori)
        return {"status": "success", "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assets")
async def create_asset(item: AssetCreate):
    try:
        res = em.add_asset(
            nama=item.nama,
            kategori=item.kategori,
            platform=item.platform,
            unit=item.unit,
            total_modal=item.total_modal,
            nilai_saat_ini=item.nilai_saat_ini,
            catatan=item.catatan or "",
        )
        return {"status": "success", "message": "Aset berhasil ditambahkan", "data": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/assets/{asset_id}")
async def update_asset_endpoint(asset_id: str, item: AssetUpdate):
    try:
        res = em.update_asset(
            asset_id=asset_id,
            nilai_saat_ini=item.nilai_saat_ini,
            unit=item.unit,
            total_modal=item.total_modal,
            catatan=item.catatan,
        )
        return {"status": "success", "message": "Nilai aset berhasil diperbarui", "data": res}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/assets/{asset_id}")
async def remove_asset(asset_id: str):
    success = em.delete_asset(asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Data aset tidak ditemukan")
    return {"status": "success", "message": "Data aset berhasil dihapus"}

# --- API Endpoints: Master Data & Export ---
@app.get("/api/master-data")
async def get_master_data():
    try:
        data = em.get_master_data()
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/master-data/category")
async def add_master_category(item: MasterItemCreate):
    try:
        success = em.add_master_category(type_str=item.tipe or "Pengeluaran", name=item.name)
        if success:
            return {"status": "success", "message": "Kategori berhasil ditambahkan"}
        raise HTTPException(status_code=400, detail="Gagal menambahkan kategori")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/master-data/wallet")
async def add_master_wallet(item: MasterItemCreate):
    try:
        success = em.add_master_wallet(name=item.name)
        if success:
            return {"status": "success", "message": "Akun/Dompet berhasil ditambahkan"}
        raise HTTPException(status_code=400, detail="Gagal menambahkan dompet")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/export")
async def export_excel():
    if not os.path.exists(config.EXCEL_FILE):
        raise HTTPException(status_code=404, detail="File Excel belum tersedia")
    return FileResponse(
        path=config.EXCEL_FILE,
        filename="MoneyTracking.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.get("/api/system-info")
async def system_info():
    token = config.TELEGRAM_BOT_TOKEN
    masked_token = f"{token[:8]}...{token[-5:]}" if len(token) > 15 else ("(Terisi)" if token else "")
    return {
        "excel_file": config.EXCEL_FILE,
        "telegram_bot_configured": bool(token),
        "telegram_bot_token_masked": masked_token,
        "allowed_users": config.ALLOWED_TELEGRAM_USERS,
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.post("/api/settings/telegram")
async def save_telegram_config(item: TelegramConfigSave):
    try:
        config.save_env_settings(item.bot_token, item.allowed_users or "")
        return {
            "status": "success",
            "message": "Konfigurasi Bot Telegram berhasil disimpan ke .env! Restart aplikasi jika ingin langsung terhubung."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=config.WEB_HOST, port=config.WEB_PORT, reload=True)

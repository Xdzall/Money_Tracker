import os
import time
import json
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

import jwt
import httpx
from fastapi import FastAPI, HTTPException, Query, Request, Response, Depends, Cookie
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

import config
from excel_manager import ExcelManager
from bot import create_bot_app

# --- JWT Session Helper ---
JWT_ALGORITHM = "HS256"

def create_session_token(user_data: dict) -> str:
    payload = {
        "sub": user_data.get("id"),
        "email": user_data.get("email"),
        "name": user_data.get("name"),
        "picture": user_data.get("picture"),
        "exp": datetime.utcnow() + timedelta(days=30),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, config.SESSION_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_session_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, config.SESSION_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "picture": payload.get("picture"),
        }
    except Exception:
        return None

def get_current_user_from_request(request: Request) -> Optional[dict]:
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1].strip()
    if token:
        return decode_session_token(token)
    return None

def get_required_user_em(request: Request) -> ExcelManager:
    user = get_current_user_from_request(request)
    if not user or not user.get("id"):
        raise HTTPException(
            status_code=401,
            detail="Silakan login terlebih dahulu untuk mengakses data keuangan Anda."
        )
    return ExcelManager(user_id=user["id"])

def get_user_excel_manager(request: Request) -> ExcelManager:
    return get_required_user_em(request)

from multi_bot_manager import bot_manager

# --- Lifespan Context Manager for Multi-Bot Telegram 24/7 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    config.reload_config()
    print("🤖 [MultiBotManager] Memulai bot telegram semua pengguna di background...")
    await bot_manager.start_all_bots()
    
    yield
    
    print("🛑 [MultiBotManager] Menghentikan semua bot telegram...")
    await bot_manager.stop_all_bots()

app = FastAPI(
    title="Money Tracking App & Multi-User Dashboard",
    version="2.2.0",
    lifespan=lifespan
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

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

class DemoLoginRequest(BaseModel):
    email: str
    name: Optional[str] = ""

# --- Web UI Route ---
@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    user = get_current_user_from_request(request)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"now": datetime.now(), "user": user}
    )

# --- Authentication Routes: Google OAuth 2.0 & Session ---
@app.get("/api/auth/google/url")
async def get_google_auth_url(request: Request):
    if not config.GOOGLE_CLIENT_ID:
        return {
            "status": "error",
            "message": "Google Client ID belum dikonfigurasi di server.",
            "google_configured": False
        }
    
    base_url = config.APP_BASE_URL or str(request.base_url).rstrip("/")
    if "https://" not in base_url and "localhost" not in base_url and "127.0.0.1" not in base_url:
        base_url = base_url.replace("http://", "https://")

    redirect_uri = f"{base_url}/api/auth/google/callback"
    
    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account"
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return {
        "status": "success",
        "url": url,
        "google_configured": True
    }

@app.get("/api/auth/google/callback")
async def google_auth_callback(code: Optional[str] = None, error: Optional[str] = None, request: Request = None):
    if error or not code:
        return RedirectResponse(url="/?auth_error=" + (error or "no_code"))

    base_url = config.APP_BASE_URL or str(request.base_url).rstrip("/")
    if "https://" not in base_url and "localhost" not in base_url and "127.0.0.1" not in base_url:
        base_url = base_url.replace("http://", "https://")

    redirect_uri = f"{base_url}/api/auth/google/callback"

    try:
        async with httpx.AsyncClient() as client:
            token_res = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": config.GOOGLE_CLIENT_ID,
                    "client_secret": config.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                timeout=10.0
            )
            token_json = token_res.json()
            access_token = token_json.get("access_token")
            if not access_token:
                return RedirectResponse(url="/?auth_error=token_exchange_failed")

            user_res = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0
            )
            user_json = user_res.json()

        email = user_json.get("email", "").strip().lower()
        name = user_json.get("name") or (email.split("@")[0] if email else "User")
        picture = user_json.get("picture", "")
        user_id = config.canonical_user_id(email or user_json.get("id"))

        user_data = {
            "id": user_id,
            "email": email or user_id,
            "name": name,
            "picture": picture
        }

        # Initialize user's personal Excel file immediately
        ExcelManager(user_id=user_id)

        session_token = create_session_token(user_data)
        response = RedirectResponse(url=f"/?login=success&token={session_token}")
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=30 * 86400, # 30 days
            httponly=True,
            samesite="lax",
            secure=bool("https://" in base_url)
        )
        return response
    except Exception as e:
        print(f"[Auth] Google OAuth Error: {e}")
        return RedirectResponse(url=f"/?auth_error=exception_{urllib.parse.quote(str(e))}")

@app.post("/api/auth/demo-login")
async def demo_login(req: DemoLoginRequest, response: Response):
    raw_ident = req.email.strip()
    if not raw_ident:
        raise HTTPException(status_code=400, detail="Username atau email harus diisi")

    user_id = config.canonical_user_id(raw_ident)
    email = user_id
    name = req.name.strip() or raw_ident.split("@")[0].title()

    user_data = {
        "id": user_id,
        "email": email,
        "name": name,
        "picture": f"https://ui-avatars.com/api/?name={urllib.parse.quote(name)}&background=4f46e5&color=fff"
    }

    # Initialize user's personal Excel file
    ExcelManager(user_id=user_id)

    session_token = create_session_token(user_data)
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=30 * 86400,
        httponly=True,
        samesite="lax"
    )
    return {
        "status": "success",
        "message": f"Login berhasil sebagai {name}",
        "user": user_data,
        "token": session_token
    }

@app.get("/api/auth/me")
async def get_current_user_profile(request: Request):
    user = get_current_user_from_request(request)
    google_configured = bool(config.GOOGLE_CLIENT_ID and config.GOOGLE_CLIENT_SECRET)
    if user:
        return {
            "status": "success",
            "is_authenticated": True,
            "user": user,
            "google_configured": google_configured
        }
    return {
        "status": "success",
        "is_authenticated": False,
        "user": None,
        "google_configured": google_configured
    }

@app.post("/api/auth/logout")
async def logout_user(response: Response):
    response.delete_cookie("session_token")
    return {"status": "success", "message": "Logout berhasil"}

# --- API Endpoints: Summary & Transactions ---
@app.get("/api/summary")
async def get_summary(
    request: Request,
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000, le=2100)
):
    em = get_required_user_em(request)
    try:
        data = em.get_monthly_summary(month=month, year=year)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transactions")
async def list_transactions(
    request: Request,
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    tipe: Optional[str] = Query(None),
    kategori: Optional[str] = Query(None),
    akun: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    em = get_required_user_em(request)
    try:
        transactions = em.get_transactions(
            month=month, year=year, tipe=tipe, kategori=kategori, akun=akun, search=search
        )
        return {"status": "success", "count": len(transactions), "data": transactions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transactions")
async def create_transaction(item: TransactionCreate, request: Request):
    em = get_required_user_em(request)
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
async def remove_transaction(trx_id: str, request: Request):
    em = get_required_user_em(request)
    success = em.delete_transaction(trx_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    return {"status": "success", "message": "Transaksi berhasil dihapus"}

# --- API Endpoints: Installments / Cicilan ---
@app.get("/api/installments")
async def list_installments(request: Request, status: Optional[str] = Query(None)):
    em = get_required_user_em(request)
    try:
        data = em.get_installments(status=status)
        return {"status": "success", "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/installments")
async def create_installment(item: InstallmentCreate, request: Request):
    em = get_required_user_em(request)
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
async def pay_installment_endpoint(installment_id: str, req: InstallmentPayRequest, request: Request):
    em = get_required_user_em(request)
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
async def remove_installment(installment_id: str, request: Request):
    em = get_required_user_em(request)
    success = em.delete_installment(installment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Data cicilan tidak ditemukan")
    return {"status": "success", "message": "Data cicilan berhasil dihapus"}

# --- API Endpoints: Assets & Investments (Saham, Crypto, Emas) ---
@app.get("/api/assets")
async def list_assets(request: Request, kategori: Optional[str] = Query(None)):
    em = get_required_user_em(request)
    try:
        data = em.get_assets(kategori=kategori)
        return {"status": "success", "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assets")
async def create_asset(item: AssetCreate, request: Request):
    em = get_required_user_em(request)
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
async def update_asset_endpoint(asset_id: str, item: AssetUpdate, request: Request):
    em = get_required_user_em(request)
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
async def remove_asset(asset_id: str, request: Request):
    em = get_required_user_em(request)
    success = em.delete_asset(asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Data aset tidak ditemukan")
    return {"status": "success", "message": "Data aset berhasil dihapus"}

# --- API Endpoints: Master Data & Export ---
@app.get("/api/master-data")
async def get_master_data(request: Request):
    em = get_required_user_em(request)
    try:
        data = em.get_master_data()
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/master-data/category")
async def add_master_category(item: MasterItemCreate, request: Request):
    em = get_required_user_em(request)
    try:
        success = em.add_master_category(type_str=item.tipe or "Pengeluaran", name=item.name)
        if success:
            return {"status": "success", "message": "Kategori berhasil ditambahkan"}
        raise HTTPException(status_code=400, detail="Gagal menambahkan kategori")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/master-data/wallet")
async def add_master_wallet(item: MasterItemCreate, request: Request):
    em = get_required_user_em(request)
    try:
        success = em.add_master_wallet(name=item.name)
        if success:
            return {"status": "success", "message": "Akun/Dompet berhasil ditambahkan"}
        raise HTTPException(status_code=400, detail="Gagal menambahkan dompet")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/export")
async def export_excel(request: Request):
    em = get_required_user_em(request)
    if not os.path.exists(em.file_path):
        raise HTTPException(status_code=404, detail="File Excel belum tersedia")
    return FileResponse(
        path=em.file_path,
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
        "google_oauth_configured": bool(config.GOOGLE_CLIENT_ID and config.GOOGLE_CLIENT_SECRET),
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# --- Android App Download Endpoint ---
@app.get("/download/android")
@app.get("/api/download/android")
async def download_android_apk():
    apk_path = os.path.join("static", "downloads", "MoneyTracker.apk")
    if os.path.exists(apk_path):
        return FileResponse(
            path=apk_path,
            filename="MoneyTracker.apk",
            media_type="application/vnd.android.package-archive"
        )
    # If APK not yet compiled, provide direct download of the Android project package / guide
    zip_path = os.path.join("static", "downloads", "MoneyTracker-Android.zip")
    if os.path.exists(zip_path):
        return FileResponse(
            path=zip_path,
            filename="MoneyTracker-Android.zip",
            media_type="application/zip"
        )
    return RedirectResponse(url="/?download=android")

class UserBotConfigRequest(BaseModel):
    bot_token: str
    telegram_user_id: Optional[int] = None

@app.get("/api/user/bot-config")
async def get_user_bot_status(request: Request):
    user = get_current_user_from_request(request)
    if not user or not user.get("id"):
        raise HTTPException(status_code=401, detail="Harus login terlebih dahulu")
    data = bot_manager.get_user_bot_config(user["id"])
    return {"status": "success", "data": data}

@app.post("/api/user/bot-config")
async def save_user_bot_config_endpoint(req: UserBotConfigRequest, request: Request):
    user = get_current_user_from_request(request)
    if not user or not user.get("id"):
        raise HTTPException(status_code=401, detail="Harus login terlebih dahulu")
    
    token = req.bot_token.strip()
    if not token:
        raise HTTPException(status_code=400, detail="Token Bot Telegram tidak boleh kosong")

    bot_manager.save_user_bot_config(user["id"], token, req.telegram_user_id)
    started = await bot_manager.start_user_bot(user["id"], token, req.telegram_user_id)
    if not started:
        raise HTTPException(status_code=400, detail="Token bot tidak valid atau gagal terhubung ke Telegram API. Periksa kembali token Anda.")
    
    return {"status": "success", "message": "Bot Telegram pribadi Anda berhasil diaktifkan dan berjalan 24/7!"}

@app.post("/api/user/bot-config/disconnect")
async def disconnect_user_bot_endpoint(request: Request):
    user = get_current_user_from_request(request)
    if not user or not user.get("id"):
        raise HTTPException(status_code=401, detail="Harus login terlebih dahulu")
    
    await bot_manager.stop_user_bot(user["id"])
    bot_manager.delete_user_bot_config(user["id"])
    return {"status": "success", "message": "Bot Telegram berhasil diputuskan."}

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

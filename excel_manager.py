import os
import shutil
import uuid
import threading
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from config import (
    EXCEL_FILE,
    BACKUP_DIR,
    DEFAULT_INCOME_CATEGORIES,
    DEFAULT_EXPENSE_CATEGORIES,
    DEFAULT_WALLETS,
)

# Global lock for safe concurrent writes from Web & Telegram Bot
_excel_lock = threading.Lock()

class ExcelManager:
    def __init__(self, file_path: str = EXCEL_FILE, backup_dir: str = BACKUP_DIR):
        self.file_path = Path(file_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_workbook_initialized()

    def _create_backup(self):
        """Create a rotating backup copy of the Excel file."""
        if self.file_path.exists() and self.file_path.stat().st_size > 0:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"MoneyTracking_{timestamp}.xlsx"
            try:
                shutil.copy2(self.file_path, backup_file)
                # Keep only latest 10 backups
                backups = sorted(self.backup_dir.glob("MoneyTracking_*.xlsx"))
                if len(backups) > 10:
                    for old_bk in backups[:-10]:
                        old_bk.unlink(missing_ok=True)
            except Exception as e:
                print(f"[ExcelManager] Backup warning: {e}")

    def _get_styles(self):
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        regular_font = Font(name="Calibri", size=11, color="0F172A")
        bold_font = Font(name="Calibri", size=11, bold=True, color="0F172A")
        
        thin_border = Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0"),
        )
        return header_fill, header_font, regular_font, bold_font, thin_border

    def _ensure_workbook_initialized(self):
        with _excel_lock:
            wb = None
            needs_init = False
            if not self.file_path.exists() or self.file_path.stat().st_size == 0:
                wb = openpyxl.Workbook()
                needs_init = True
            else:
                try:
                    wb = openpyxl.load_workbook(self.file_path)
                except Exception:
                    wb = openpyxl.Workbook()
                    needs_init = True

            header_fill, header_font, _, _, thin_border = self._get_styles()

            # 1. Sheet: Transaksi
            if "Transaksi" not in wb.sheetnames:
                ws_trx = wb.create_sheet("Transaksi")
                headers = ["ID", "Tanggal", "Tipe", "Kategori", "Akun", "Jumlah (Rp)", "Keterangan", "ID_Cicilan"]
                ws_trx.append(headers)
                for col_idx, h in enumerate(headers, 1):
                    cell = ws_trx.cell(row=1, column=col_idx)
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                ws_trx.freeze_panes = "A2"
                needs_init = True
            
            # 2. Sheet: Cicilan
            if "Cicilan" not in wb.sheetnames:
                ws_cicilan = wb.create_sheet("Cicilan")
                headers = [
                    "ID_Cicilan", "Nama Cicilan", "Penyedia/Bank", "Total Pinjaman",
                    "Cicilan per Bulan", "Tenor (Bulan)", "Cicilan Ke-", "Sisa Tenor",
                    "Sisa Hutang", "Tgl Jatuh Tempo", "Status"
                ]
                ws_cicilan.append(headers)
                for col_idx, h in enumerate(headers, 1):
                    cell = ws_cicilan.cell(row=1, column=col_idx)
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                ws_cicilan.freeze_panes = "A2"
                needs_init = True

            # 3. Sheet: Aset_Investasi (Saham, Crypto, Emas, dll)
            if "Aset_Investasi" not in wb.sheetnames:
                ws_assets = wb.create_sheet("Aset_Investasi")
                headers = [
                    "ID_Aset", "Nama Aset", "Kategori", "Platform", "Jumlah Unit",
                    "Total Modal (Rp)", "Nilai Saat Ini (Rp)", "Untung/Rugi (Rp)",
                    "Return (%)", "Catatan"
                ]
                ws_assets.append(headers)
                for col_idx, h in enumerate(headers, 1):
                    cell = ws_assets.cell(row=1, column=col_idx)
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                ws_assets.freeze_panes = "A2"
                needs_init = True

            # 4. Sheet: Master_Data
            if "Master_Data" not in wb.sheetnames:
                ws_master = wb.create_sheet("Master_Data")
                ws_master.append(["Kategori Pemasukan", "Kategori Pengeluaran", "Daftar Akun/Dompet"])
                for col_idx in range(1, 4):
                    cell = ws_master.cell(row=1, column=col_idx)
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")

                # Populate defaults
                max_len = max(len(DEFAULT_INCOME_CATEGORIES), len(DEFAULT_EXPENSE_CATEGORIES), len(DEFAULT_WALLETS))
                for i in range(max_len):
                    inc = DEFAULT_INCOME_CATEGORIES[i] if i < len(DEFAULT_INCOME_CATEGORIES) else ""
                    exp = DEFAULT_EXPENSE_CATEGORIES[i] if i < len(DEFAULT_EXPENSE_CATEGORIES) else ""
                    wlt = DEFAULT_WALLETS[i] if i < len(DEFAULT_WALLETS) else ""
                    ws_master.append([inc, exp, wlt])
                needs_init = True

            # Remove default empty "Sheet" if other sheets exist
            if "Sheet" in wb.sheetnames and len(wb.sheetnames) > 1:
                del wb["Sheet"]
                needs_init = True

            # Auto-adjust column widths
            for sheet in wb.worksheets:
                for col in sheet.columns:
                    col_letter = get_column_letter(col[0].column)
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    sheet.column_dimensions[col_letter].width = max(max_len + 4, 12)

            if needs_init:
                self._create_backup()
                wb.save(self.file_path)
            wb.close()

    def get_master_data(self) -> Dict[str, List[str]]:
        with _excel_lock:
            wb = openpyxl.load_workbook(self.file_path, data_only=True)
            if "Master_Data" not in wb.sheetnames:
                wb.close()
                return {
                    "income_categories": DEFAULT_INCOME_CATEGORIES,
                    "expense_categories": DEFAULT_EXPENSE_CATEGORIES,
                    "wallets": DEFAULT_WALLETS,
                }
            ws = wb["Master_Data"]
            incomes, expenses, wallets = [], [], []
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[0] and str(row[0]).strip():
                    incomes.append(str(row[0]).strip())
                if len(row) > 1 and row[1] and str(row[1]).strip():
                    expenses.append(str(row[1]).strip())
                if len(row) > 2 and row[2] and str(row[2]).strip():
                    wallets.append(str(row[2]).strip())
            wb.close()
            return {
                "income_categories": incomes or DEFAULT_INCOME_CATEGORIES,
                "expense_categories": expenses or DEFAULT_EXPENSE_CATEGORIES,
                "wallets": wallets or DEFAULT_WALLETS,
            }

    def add_master_category(self, type_str: str, name: str) -> bool:
        name = name.strip()
        if not name:
            return False
        with _excel_lock:
            self._create_backup()
            wb = openpyxl.load_workbook(self.file_path)
            ws = wb["Master_Data"]
            col = 1 if type_str.lower() == "pemasukan" else 2
            
            for row in range(2, ws.max_row + 1):
                if str(ws.cell(row=row, column=col).value or "").strip().lower() == name.lower():
                    wb.close()
                    return True
            
            target_row = None
            for row in range(2, ws.max_row + 2):
                if not ws.cell(row=row, column=col).value:
                    target_row = row
                    break
            if not target_row:
                target_row = ws.max_row + 1

            ws.cell(row=target_row, column=col, value=name)
            wb.save(self.file_path)
            wb.close()
            return True

    def add_master_wallet(self, name: str) -> bool:
        name = name.strip()
        if not name:
            return False
        with _excel_lock:
            self._create_backup()
            wb = openpyxl.load_workbook(self.file_path)
            ws = wb["Master_Data"]
            col = 3
            for row in range(2, ws.max_row + 1):
                if str(ws.cell(row=row, column=col).value or "").strip().lower() == name.lower():
                    wb.close()
                    return True
            
            target_row = None
            for row in range(2, ws.max_row + 2):
                if not ws.cell(row=row, column=col).value:
                    target_row = row
                    break
            if not target_row:
                target_row = ws.max_row + 1

            ws.cell(row=target_row, column=col, value=name)
            wb.save(self.file_path)
            wb.close()
            return True

    # -------------------------------------------------------------
    # TRANSACTIONS
    # -------------------------------------------------------------
    def add_transaction(
        self,
        tanggal: str,
        tipe: str,
        kategori: str,
        akun: str,
        jumlah: float,
        keterangan: str = "",
        id_cicilan: Optional[str] = None,
    ) -> Dict[str, Any]:
        if isinstance(tanggal, (datetime, date)):
            tgl_str = tanggal.strftime("%Y-%m-%d")
        else:
            try:
                if "/" in str(tanggal):
                    dt = datetime.strptime(str(tanggal), "%d/%m/%Y")
                else:
                    dt = datetime.strptime(str(tanggal), "%Y-%m-%d")
                tgl_str = dt.strftime("%Y-%m-%d")
            except Exception:
                tgl_str = datetime.now().strftime("%Y-%m-%d")

        trx_id = f"TRX-{datetime.now().strftime('%y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        tipe_formatted = "Pemasukan" if "masuk" in tipe.lower() or "income" in tipe.lower() else "Pengeluaran"
        
        with _excel_lock:
            self._create_backup()
            wb = openpyxl.load_workbook(self.file_path)
            ws = wb["Transaksi"]
            
            new_row = ws.max_row + 1
            row_data = [
                trx_id,
                tgl_str,
                tipe_formatted,
                kategori.strip(),
                akun.strip(),
                float(jumlah),
                keterangan.strip(),
                id_cicilan or ""
            ]
            ws.append(row_data)

            _, _, regular_font, _, thin_border = self._get_styles()
            for col_idx in range(1, 9):
                cell = ws.cell(row=new_row, column=col_idx)
                cell.font = regular_font
                cell.border = thin_border
                if col_idx == 6:
                    cell.number_format = "#,##0"
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx in [1, 2, 3, 5, 8]:
                    cell.alignment = Alignment(horizontal="center")
                else:
                    cell.alignment = Alignment(horizontal="left")

            wb.save(self.file_path)
            wb.close()

        if kategori:
            self.add_master_category(tipe_formatted, kategori)
        if akun:
            self.add_master_wallet(akun)

        return {
            "id": trx_id,
            "tanggal": tgl_str,
            "tipe": tipe_formatted,
            "kategori": kategori,
            "akun": akun,
            "jumlah": float(jumlah),
            "keterangan": keterangan,
            "id_cicilan": id_cicilan or ""
        }

    def get_transactions(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None,
        tipe: Optional[str] = None,
        kategori: Optional[str] = None,
        akun: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        transactions = []
        with _excel_lock:
            wb = openpyxl.load_workbook(self.file_path, data_only=True)
            if "Transaksi" not in wb.sheetnames:
                wb.close()
                return []
            ws = wb["Transaksi"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue
                trx_id = str(row[0])
                tgl_val = row[1]
                if isinstance(tgl_val, datetime):
                    tgl_str = tgl_val.strftime("%Y-%m-%d")
                elif isinstance(tgl_val, date):
                    tgl_str = tgl_val.strftime("%Y-%m-%d")
                else:
                    tgl_str = str(tgl_val or "")

                trx_tipe = str(row[2] or "Pengeluaran")
                trx_kat = str(row[3] or "")
                trx_akun = str(row[4] or "")
                try:
                    trx_jumlah = float(row[5] or 0)
                except (ValueError, TypeError):
                    trx_jumlah = 0.0
                trx_ket = str(row[6] or "")
                trx_cicilan = str(row[7] or "")

                if tgl_str:
                    try:
                        trx_dt = datetime.strptime(tgl_str[:10], "%Y-%m-%d")
                        if month and trx_dt.month != int(month):
                            continue
                        if year and trx_dt.year != int(year):
                            continue
                    except Exception:
                        pass

                if tipe and tipe.lower() != "semua" and trx_tipe.lower() != tipe.lower():
                    continue
                if kategori and kategori.lower() != "semua" and trx_kat.lower() != kategori.lower():
                    continue
                if akun and akun.lower() != "semua" and trx_akun.lower() != akun.lower():
                    continue
                if search:
                    q = search.lower()
                    if q not in trx_ket.lower() and q not in trx_kat.lower() and q not in trx_akun.lower() and q not in trx_id.lower():
                        continue

                transactions.append({
                    "id": trx_id,
                    "tanggal": tgl_str,
                    "tipe": trx_tipe,
                    "kategori": trx_kat,
                    "akun": trx_akun,
                    "jumlah": trx_jumlah,
                    "keterangan": trx_ket,
                    "id_cicilan": trx_cicilan,
                })
            wb.close()

        transactions.sort(key=lambda x: (x["tanggal"], x["id"]), reverse=True)
        return transactions

    def delete_transaction(self, trx_id: str) -> bool:
        with _excel_lock:
            self._create_backup()
            wb = openpyxl.load_workbook(self.file_path)
            ws = wb["Transaksi"]
            row_to_delete = None
            for row in range(2, ws.max_row + 1):
                if str(ws.cell(row=row, column=1).value or "").strip() == trx_id.strip():
                    row_to_delete = row
                    break
            
            if row_to_delete:
                ws.delete_rows(row_to_delete)
                wb.save(self.file_path)
                wb.close()
                return True
            wb.close()
            return False

    # -------------------------------------------------------------
    # CICILAN / INSTALLMENTS
    # -------------------------------------------------------------
    def add_installment(
        self,
        nama: str,
        penyedia: str,
        total_pinjaman: float,
        cicilan_bulanan: float,
        tenor: int,
        cicilan_ke: int = 0,
        tgl_jatuh_tempo: int = 1,
    ) -> Dict[str, Any]:
        c_id = f"CICIL-{datetime.now().strftime('%y%m%d%H%M%S')}-{uuid.uuid4().hex[:3].upper()}"
        sisa_tenor = max(0, int(tenor) - int(cicilan_ke))
        sisa_hutang = float(cicilan_bulanan) * sisa_tenor
        status = "Lunas" if sisa_tenor == 0 else "Aktif"

        with _excel_lock:
            self._create_backup()
            wb = openpyxl.load_workbook(self.file_path)
            ws = wb["Cicilan"]
            
            new_row = ws.max_row + 1
            row_data = [
                c_id,
                nama.strip(),
                penyedia.strip(),
                float(total_pinjaman),
                float(cicilan_bulanan),
                int(tenor),
                int(cicilan_ke),
                int(sisa_tenor),
                float(sisa_hutang),
                int(tgl_jatuh_tempo),
                status
            ]
            ws.append(row_data)

            _, _, regular_font, _, thin_border = self._get_styles()
            for col_idx in range(1, 12):
                cell = ws.cell(row=new_row, column=col_idx)
                cell.font = regular_font
                cell.border = thin_border
                if col_idx in [4, 5, 9]:
                    cell.number_format = "#,##0"
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx in [1, 6, 7, 8, 10, 11]:
                    cell.alignment = Alignment(horizontal="center")
                else:
                    cell.alignment = Alignment(horizontal="left")

            wb.save(self.file_path)
            wb.close()

        return {
            "id_cicilan": c_id,
            "nama": nama,
            "penyedia": penyedia,
            "total_pinjaman": float(total_pinjaman),
            "cicilan_bulanan": float(cicilan_bulanan),
            "tenor": int(tenor),
            "cicilan_ke": int(cicilan_ke),
            "sisa_tenor": int(sisa_tenor),
            "sisa_hutang": float(sisa_hutang),
            "tgl_jatuh_tempo": int(tgl_jatuh_tempo),
            "status": status,
        }

    def get_installments(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        installments = []
        with _excel_lock:
            wb = openpyxl.load_workbook(self.file_path, data_only=True)
            if "Cicilan" not in wb.sheetnames:
                wb.close()
                return []
            ws = wb["Cicilan"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue
                c_id = str(row[0])
                nama = str(row[1] or "")
                penyedia = str(row[2] or "")
                tot_pinjaman = float(row[3] or 0)
                cicilan_bln = float(row[4] or 0)
                tenor = int(row[5] or 0)
                cicilan_ke = int(row[6] or 0)
                sisa_tenor = int(row[7] or max(0, tenor - cicilan_ke))
                sisa_hutang = float(row[8] or (cicilan_bln * sisa_tenor))
                tgl_tempo = int(row[9] or 1)
                st = str(row[10] or ("Lunas" if sisa_tenor <= 0 else "Aktif"))

                if status and status.lower() != "semua" and st.lower() != status.lower():
                    continue

                installments.append({
                    "id_cicilan": c_id,
                    "nama": nama,
                    "penyedia": penyedia,
                    "total_pinjaman": tot_pinjaman,
                    "cicilan_bulanan": cicilan_bln,
                    "tenor": tenor,
                    "cicilan_ke": cicilan_ke,
                    "sisa_tenor": sisa_tenor,
                    "sisa_hutang": sisa_hutang,
                    "tgl_jatuh_tempo": tgl_tempo,
                    "status": st,
                    "progress_pct": round((cicilan_ke / tenor * 100), 1) if tenor > 0 else 100.0,
                })
            wb.close()
        return installments

    def pay_installment(
        self,
        installment_id: str,
        payment_date: Optional[str] = None,
        wallet: str = "BCA",
        note: str = ""
    ) -> Dict[str, Any]:
        target_row = None
        inst_data = None
        
        with _excel_lock:
            self._create_backup()
            wb = openpyxl.load_workbook(self.file_path)
            ws = wb["Cicilan"]
            for row in range(2, ws.max_row + 1):
                if str(ws.cell(row=row, column=1).value or "").strip() == installment_id.strip():
                    target_row = row
                    nama = str(ws.cell(row=row, column=2).value or "")
                    cicilan_bln = float(ws.cell(row=row, column=5).value or 0)
                    tenor = int(ws.cell(row=row, column=6).value or 0)
                    cicilan_ke = int(ws.cell(row=row, column=7).value or 0)
                    
                    new_ke = cicilan_ke + 1
                    new_sisa_tenor = max(0, tenor - new_ke)
                    new_sisa_hutang = float(cicilan_bln * new_sisa_tenor)
                    new_status = "Lunas" if new_sisa_tenor == 0 else "Aktif"

                    ws.cell(row=row, column=7, value=new_ke)
                    ws.cell(row=row, column=8, value=new_sisa_tenor)
                    ws.cell(row=row, column=9, value=new_sisa_hutang)
                    ws.cell(row=row, column=11, value=new_status)

                    inst_data = {
                        "id_cicilan": installment_id,
                        "nama": nama,
                        "cicilan_bulanan": cicilan_bln,
                        "tenor": tenor,
                        "cicilan_ke": new_ke,
                        "sisa_tenor": new_sisa_tenor,
                        "sisa_hutang": new_sisa_hutang,
                        "status": new_status,
                    }
                    break
            
            wb.save(self.file_path)
            wb.close()

        if not target_row or not inst_data:
            raise ValueError(f"Cicilan dengan ID {installment_id} tidak ditemukan.")

        pay_date = payment_date or datetime.now().strftime("%Y-%m-%d")
        trx_note = note.strip() or f"Bayar cicilan {inst_data['nama']} (Bulan ke-{inst_data['cicilan_ke']}/{inst_data['tenor']})"
        trx = self.add_transaction(
            tanggal=pay_date,
            tipe="Pengeluaran",
            kategori="Cicilan & Hutang",
            akun=wallet,
            jumlah=inst_data["cicilan_bulanan"],
            keterangan=trx_note,
            id_cicilan=installment_id
        )

        return {
            "installment": inst_data,
            "transaction": trx
        }

    def delete_installment(self, installment_id: str) -> bool:
        with _excel_lock:
            self._create_backup()
            wb = openpyxl.load_workbook(self.file_path)
            ws = wb["Cicilan"]
            row_to_delete = None
            for row in range(2, ws.max_row + 1):
                if str(ws.cell(row=row, column=1).value or "").strip() == installment_id.strip():
                    row_to_delete = row
                    break
            
            if row_to_delete:
                ws.delete_rows(row_to_delete)
                wb.save(self.file_path)
                wb.close()
                return True
            wb.close()
            return False

    # -------------------------------------------------------------
    # ASSET & INVESTASI (Saham, Crypto, Emas, dll)
    # -------------------------------------------------------------
    def add_asset(
        self,
        nama: str,
        kategori: str,
        platform: str,
        unit: str,
        total_modal: float,
        nilai_saat_ini: float,
        catatan: str = ""
    ) -> Dict[str, Any]:
        asset_id = f"AST-{datetime.now().strftime('%y%m%d%H%M%S')}-{uuid.uuid4().hex[:3].upper()}"
        modal = float(total_modal)
        nilai = float(nilai_saat_ini)
        pnl = nilai - modal
        return_pct = round((pnl / modal * 100), 2) if modal > 0 else 0.0

        with _excel_lock:
            self._create_backup()
            wb = openpyxl.load_workbook(self.file_path)
            ws = wb["Aset_Investasi"]

            new_row = ws.max_row + 1
            row_data = [
                asset_id,
                nama.strip(),
                kategori.strip(),
                platform.strip(),
                str(unit).strip(),
                modal,
                nilai,
                pnl,
                return_pct,
                catatan.strip()
            ]
            ws.append(row_data)

            _, _, regular_font, _, thin_border = self._get_styles()
            for col_idx in range(1, 11):
                cell = ws.cell(row=new_row, column=col_idx)
                cell.font = regular_font
                cell.border = thin_border
                if col_idx in [6, 7, 8]:
                    cell.number_format = "#,##0"
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx == 9:
                    cell.number_format = "0.00"
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx in [1, 3, 4, 5]:
                    cell.alignment = Alignment(horizontal="center")
                else:
                    cell.alignment = Alignment(horizontal="left")

            wb.save(self.file_path)
            wb.close()

        return {
            "id_aset": asset_id,
            "nama": nama,
            "kategori": kategori,
            "platform": platform,
            "unit": unit,
            "total_modal": modal,
            "nilai_saat_ini": nilai,
            "pnl": pnl,
            "return_pct": return_pct,
            "catatan": catatan
        }

    def get_assets(self, kategori: Optional[str] = None) -> List[Dict[str, Any]]:
        assets = []
        with _excel_lock:
            wb = openpyxl.load_workbook(self.file_path, data_only=True)
            if "Aset_Investasi" not in wb.sheetnames:
                wb.close()
                return []
            ws = wb["Aset_Investasi"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue
                a_id = str(row[0])
                nama = str(row[1] or "")
                kat = str(row[2] or "Lainnya")
                plat = str(row[3] or "")
                unit = str(row[4] or "")
                modal = float(row[5] or 0)
                nilai = float(row[6] or 0)
                pnl = float(row[7] or (nilai - modal))
                ret_pct = float(row[8] or (round((pnl / modal * 100), 2) if modal > 0 else 0.0))
                note = str(row[9] or "")

                if kategori and kategori.lower() != "semua" and kat.lower() != kategori.lower():
                    continue

                assets.append({
                    "id_aset": a_id,
                    "nama": nama,
                    "kategori": kat,
                    "platform": plat,
                    "unit": unit,
                    "total_modal": modal,
                    "nilai_saat_ini": nilai,
                    "pnl": pnl,
                    "return_pct": ret_pct,
                    "catatan": note
                })
            wb.close()
        return assets

    def update_asset(
        self,
        asset_id: str,
        nilai_saat_ini: Optional[float] = None,
        unit: Optional[str] = None,
        total_modal: Optional[float] = None,
        catatan: Optional[str] = None
    ) -> Dict[str, Any]:
        updated_data = None
        with _excel_lock:
            self._create_backup()
            wb = openpyxl.load_workbook(self.file_path)
            ws = wb["Aset_Investasi"]
            for row in range(2, ws.max_row + 1):
                if str(ws.cell(row=row, column=1).value or "").strip() == asset_id.strip():
                    nama = str(ws.cell(row=row, column=2).value or "")
                    kat = str(ws.cell(row=row, column=3).value or "")
                    plat = str(ws.cell(row=row, column=4).value or "")
                    
                    cur_unit = unit if unit is not None else str(ws.cell(row=row, column=5).value or "")
                    cur_modal = float(total_modal if total_modal is not None else (ws.cell(row=row, column=6).value or 0))
                    cur_nilai = float(nilai_saat_ini if nilai_saat_ini is not None else (ws.cell(row=row, column=7).value or 0))
                    cur_note = catatan if catatan is not None else str(ws.cell(row=row, column=10).value or "")
                    
                    pnl = cur_nilai - cur_modal
                    ret_pct = round((pnl / cur_modal * 100), 2) if cur_modal > 0 else 0.0

                    ws.cell(row=row, column=5, value=cur_unit)
                    ws.cell(row=row, column=6, value=cur_modal)
                    ws.cell(row=row, column=7, value=cur_nilai)
                    ws.cell(row=row, column=8, value=pnl)
                    ws.cell(row=row, column=9, value=ret_pct)
                    ws.cell(row=row, column=10, value=cur_note)

                    updated_data = {
                        "id_aset": asset_id,
                        "nama": nama,
                        "kategori": kat,
                        "platform": plat,
                        "unit": cur_unit,
                        "total_modal": cur_modal,
                        "nilai_saat_ini": cur_nilai,
                        "pnl": pnl,
                        "return_pct": ret_pct,
                        "catatan": cur_note
                    }
                    break
            
            wb.save(self.file_path)
            wb.close()

        if not updated_data:
            raise ValueError(f"Aset dengan ID {asset_id} tidak ditemukan.")
        return updated_data

    def delete_asset(self, asset_id: str) -> bool:
        with _excel_lock:
            self._create_backup()
            wb = openpyxl.load_workbook(self.file_path)
            ws = wb["Aset_Investasi"]
            row_to_delete = None
            for row in range(2, ws.max_row + 1):
                if str(ws.cell(row=row, column=1).value or "").strip() == asset_id.strip():
                    row_to_delete = row
                    break
            
            if row_to_delete:
                ws.delete_rows(row_to_delete)
                wb.save(self.file_path)
                wb.close()
                return True
            wb.close()
            return False

    # -------------------------------------------------------------
    # MONTHLY SUMMARY & KPI METRICS
    # -------------------------------------------------------------
    def get_monthly_summary(self, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
        today = datetime.now()
        target_month = int(month) if month else today.month
        target_year = int(year) if year else today.year

        all_transactions = self.get_transactions()
        
        month_income = 0.0
        month_expense = 0.0
        category_breakdown: Dict[str, float] = {}
        wallet_balances: Dict[str, float] = {}

        master_data = self.get_master_data()
        for w in master_data["wallets"]:
            wallet_balances[w] = 0.0

        for t in all_transactions:
            tgl_str = t["tanggal"]
            tipe = t["tipe"]
            kat = t["kategori"] or "Lain-lain"
            akun = t["akun"] or "Cash / Tunai"
            amt = t["jumlah"]

            if akun not in wallet_balances:
                wallet_balances[akun] = 0.0
            if tipe == "Pemasukan":
                wallet_balances[akun] += amt
            else:
                wallet_balances[akun] -= amt

            try:
                dt = datetime.strptime(tgl_str[:10], "%Y-%m-%d")
                if dt.month == target_month and dt.year == target_year:
                    if tipe == "Pemasukan":
                        month_income += amt
                    else:
                        month_expense += amt
                        category_breakdown[kat] = category_breakdown.get(kat, 0.0) + amt
            except Exception:
                pass

        # Installments
        installments = self.get_installments()
        active_installments = [i for i in installments if i["status"] == "Aktif"]
        total_monthly_installment_burden = sum(i["cicilan_bulanan"] for i in active_installments)
        total_outstanding_debt = sum(i["sisa_hutang"] for i in active_installments)

        # Assets & Investments
        assets = self.get_assets()
        total_asset_value = sum(a["nilai_saat_ini"] for a in assets)
        total_asset_cost = sum(a["total_modal"] for a in assets)
        total_asset_pnl = total_asset_value - total_asset_cost
        total_asset_return_pct = round((total_asset_pnl / total_asset_cost * 100), 2) if total_asset_cost > 0 else 0.0

        asset_category_breakdown: Dict[str, float] = {}
        for a in assets:
            k = a["kategori"] or "Lainnya"
            asset_category_breakdown[k] = asset_category_breakdown.get(k, 0.0) + a["nilai_saat_ini"]

        net_cashflow = month_income - month_expense
        total_liquid_cash = sum(wallet_balances.values())
        total_net_worth = total_liquid_cash + total_asset_value - total_outstanding_debt

        # Monthly Trend (last 6 months)
        monthly_trend = []
        for i in range(5, -1, -1):
            m = target_month - i
            y = target_year
            while m <= 0:
                m += 12
                y -= 1
            
            inc_sum = 0.0
            exp_sum = 0.0
            for t in all_transactions:
                try:
                    dt = datetime.strptime(t["tanggal"][:10], "%Y-%m-%d")
                    if dt.month == m and dt.year == y:
                        if t["tipe"] == "Pemasukan":
                            inc_sum += t["jumlah"]
                        else:
                            exp_sum += t["jumlah"]
                except Exception:
                    pass

            month_names = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
            monthly_trend.append({
                "period": f"{month_names[m]} {str(y)[2:]}",
                "income": inc_sum,
                "expense": exp_sum,
                "net": inc_sum - exp_sum,
            })

        return {
            "month": target_month,
            "year": target_year,
            "total_income": month_income,
            "total_expense": month_expense,
            "net_cashflow": net_cashflow,
            "total_liquid_cash": total_liquid_cash,
            "total_net_worth": total_net_worth,
            "active_installment_burden": total_monthly_installment_burden,
            "total_outstanding_debt": total_outstanding_debt,
            "total_asset_value": total_asset_value,
            "total_asset_cost": total_asset_cost,
            "total_asset_pnl": total_asset_pnl,
            "total_asset_return_pct": total_asset_return_pct,
            "asset_category_breakdown": asset_category_breakdown,
            "category_breakdown": category_breakdown,
            "wallet_balances": wallet_balances,
            "monthly_trend": monthly_trend,
            "active_installments_count": len(active_installments),
            "assets_count": len(assets),
        }

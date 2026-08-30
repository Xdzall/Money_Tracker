// Money Tracking Web Dashboard Client Logic

let currentMonth = new Date().getMonth() + 1;
let currentYear = new Date().getFullYear();
let currentTransactionType = "Pengeluaran";
let masterData = { income_categories: [], expense_categories: [], wallets: [] };

let categoryDonutChart = null;
let cashflowBarChart = null;
let assetDonutChart = null;
let searchDebounceTimer = null;

// Currency Formatter
function formatIDR(amount) {
    return new Intl.NumberFormat("id-ID", {
        style: "currency",
        currency: "IDR",
        maximumFractionDigits: 0,
    }).format(amount || 0);
}

// Format Date YYYY-MM-DD to DD MMM YYYY
function formatDateIndo(dateStr) {
    if (!dateStr) return "-";
    const parts = dateStr.split("-");
    if (parts.length !== 3) return dateStr;
    const months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];
    return `${parseInt(parts[2])} ${months[parseInt(parts[1]) - 1]} ${parts[0]}`;
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", async () => {
    document.getElementById("monthSelect").value = currentMonth;
    document.getElementById("yearSelect").value = currentYear;
    document.getElementById("inputDate").value = new Date().toISOString().split("T")[0];
    document.getElementById("payInstDate").value = new Date().toISOString().split("T")[0];

    await checkAuthStatus();
    await loadMasterData();
    await checkBotStatus();
    await refreshAll();
});

function onPeriodChange() {
    currentMonth = parseInt(document.getElementById("monthSelect").value);
    currentYear = parseInt(document.getElementById("yearSelect").value);
    refreshAll();
}

async function refreshAll() {
    await loadSummary();
    await loadTransactions();
    await loadInstallments();
    await loadAssets();
}

// -------------------------------------------------------------
// TAB SWITCHING (Desktop + Mobile Navigation)
// -------------------------------------------------------------
function switchTab(tabId) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
    const target = document.getElementById(tabId);
    if (target) target.classList.remove("hidden");

    // Desktop Tab Buttons
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.classList.remove("border-brand-600", "text-brand-600", "font-bold");
        btn.classList.add("border-transparent", "text-slate-500", "font-medium");
    });
    const activeNav = document.getElementById("nav-" + tabId);
    if (activeNav) {
        activeNav.classList.remove("border-transparent", "text-slate-500", "font-medium");
        activeNav.classList.add("border-brand-600", "text-brand-600", "font-bold");
    }

    // Mobile Bottom Bar Buttons
    document.querySelectorAll(".mobile-nav-btn").forEach(btn => {
        btn.classList.remove("text-brand-600");
        btn.classList.add("text-slate-400");
        const span = btn.querySelector("span");
        if (span) {
            span.classList.remove("font-bold");
            span.classList.add("font-medium");
        }
    });
    const activeMobileNav = document.getElementById("mobile-nav-" + tabId);
    if (activeMobileNav) {
        activeMobileNav.classList.remove("text-slate-400");
        activeMobileNav.classList.add("text-brand-600");
        const span = activeMobileNav.querySelector("span");
        if (span) {
            span.classList.remove("font-medium");
            span.classList.add("font-bold");
        }
    }

    // Scroll to top smoothly
    window.scrollTo({ top: 0, behavior: 'smooth' });

    setTimeout(() => {
        if (categoryDonutChart) categoryDonutChart.resize();
        if (cashflowBarChart) cashflowBarChart.resize();
        if (assetDonutChart) assetDonutChart.resize();
        lucide.createIcons();
    }, 60);
}

// -------------------------------------------------------------
// MASTER DATA & CATEGORIES
// -------------------------------------------------------------
async function loadMasterData() {
    try {
        const res = await fetch("/api/master-data");
        const json = await res.json();
        if (json.status === "success") {
            masterData = json.data;
            populateCategoryDropdowns();
            renderSettingsChips();
        }
    } catch (e) {
        console.error("Error loading master data:", e);
    }
}

function populateCategoryDropdowns() {
    const inputCat = document.getElementById("inputCategory");
    const inputWal = document.getElementById("inputWallet");
    const payWal = document.getElementById("payInstWallet");
    const filterCat = document.getElementById("filterCategory");
    const filterWal = document.getElementById("filterWallet");

    const cats = currentTransactionType === "Pemasukan" 
        ? masterData.income_categories 
        : masterData.expense_categories;
    
    inputCat.innerHTML = cats.map(c => `<option value="${c}">${c}</option>`).join("");

    const walletOpts = masterData.wallets.map(w => `<option value="${w}">${w}</option>`).join("");
    inputWal.innerHTML = walletOpts;
    payWal.innerHTML = walletOpts;

    const allCats = [...new Set([...masterData.income_categories, ...masterData.expense_categories])];
    filterCat.innerHTML = `<option value="Semua">Semua Kategori</option>` + 
        allCats.map(c => `<option value="${c}">${c}</option>`).join("");
    filterWal.innerHTML = `<option value="Semua">Semua Akun</option>` + 
        masterData.wallets.map(w => `<option value="${w}">${w}</option>`).join("");
}

function renderSettingsChips() {
    const expChips = document.getElementById("expenseCategoryChips");
    const incChips = document.getElementById("incomeCategoryChips");
    const walChips = document.getElementById("walletChips");

    expChips.innerHTML = masterData.expense_categories.map(c => 
        `<span class="px-2.5 py-1 text-[11px] bg-rose-50 text-rose-700 border border-rose-200/80 rounded-xl font-bold">${c}</span>`
    ).join("");

    incChips.innerHTML = masterData.income_categories.map(c => 
        `<span class="px-2.5 py-1 text-[11px] bg-emerald-50 text-emerald-700 border border-emerald-200/80 rounded-xl font-bold">${c}</span>`
    ).join("");

    walChips.innerHTML = masterData.wallets.map(w => 
        `<span class="px-2.5 py-1 text-[11px] bg-slate-100 text-slate-700 border border-slate-200 rounded-xl font-bold">${w}</span>`
    ).join("");
}

async function submitNewCategory() {
    const type = document.getElementById("newCatType").value;
    const name = document.getElementById("newCatName").value.trim();
    if (!name) return showToast("Nama kategori tidak boleh kosong", "error");

    try {
        const res = await fetch("/api/master-data/category", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, tipe: type })
        });
        const json = await res.json();
        if (json.status === "success") {
            showToast("Kategori berhasil ditambahkan!", "success");
            document.getElementById("newCatName").value = "";
            await loadMasterData();
        } else {
            showToast(json.detail || "Gagal menambah kategori", "error");
        }
    } catch (e) {
        showToast("Terjadi kesalahan koneksi", "error");
    }
}

async function submitNewWallet() {
    const name = document.getElementById("newWalletName").value.trim();
    if (!name) return showToast("Nama akun/dompet tidak boleh kosong", "error");

    try {
        const res = await fetch("/api/master-data/wallet", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name })
        });
        const json = await res.json();
        if (json.status === "success") {
            showToast("Akun/Bank berhasil ditambahkan!", "success");
            document.getElementById("newWalletName").value = "";
            await loadMasterData();
        } else {
            showToast(json.detail || "Gagal menambah bank", "error");
        }
    } catch (e) {
        showToast("Terjadi kesalahan koneksi", "error");
    }
}

// -------------------------------------------------------------
// SUMMARY & CHARTS
// -------------------------------------------------------------
async function loadSummary() {
    try {
        const res = await fetch(`/api/summary?month=${currentMonth}&year=${currentYear}`);
        const json = await res.json();
        if (json.status === "success") {
            const data = json.data;
            
            document.getElementById("cardIncome").innerText = formatIDR(data.total_income);
            document.getElementById("cardExpense").innerText = formatIDR(data.total_expense);
            document.getElementById("cardInstallment").innerText = formatIDR(data.active_installment_burden);
            document.getElementById("cardInstallmentSub").innerText = `${data.active_installments_count} cicilan aktif`;
            
            document.getElementById("cardNetWorth").innerText = formatIDR(data.total_net_worth);
            document.getElementById("dashTotalCash").innerText = formatIDR(data.total_liquid_cash);
            document.getElementById("dashAssetTotalVal").innerText = formatIDR(data.total_asset_value);
            
            const dashPnlEl = document.getElementById("dashAssetPnl");
            const pnlSign = data.total_asset_pnl >= 0 ? "+" : "";
            dashPnlEl.innerText = `${pnlSign}${formatIDR(data.total_asset_pnl)} (${pnlSign}${data.total_asset_return_pct}%)`;
            dashPnlEl.className = data.total_asset_pnl >= 0 ? "font-extrabold text-emerald-600 text-xs" : "font-extrabold text-rose-600 text-xs";

            const assetBreakdownContainer = document.getElementById("dashAssetBreakdownContainer");
            const assetCats = Object.entries(data.asset_category_breakdown || {});
            if (assetCats.length === 0) {
                assetBreakdownContainer.innerHTML = `<p class="text-slate-400 text-[11px]">Belum ada data aset.</p>`;
            } else {
                assetBreakdownContainer.innerHTML = assetCats.map(([cat, val]) => `
                    <div class="flex items-center justify-between py-1 border-b border-slate-50 text-[11px]">
                        <span class="text-slate-600 font-medium">${cat}:</span>
                        <span class="font-bold text-slate-900">${formatIDR(val)}</span>
                    </div>
                `).join("");
            }

            renderWalletBalances(data.wallet_balances);
            renderCategoryDonut(data.category_breakdown);
            renderCashflowBar(data.monthly_trend);
        }
    } catch (e) {
        console.error("Error loading summary:", e);
    }
}

function renderWalletBalances(balances) {
    const container = document.getElementById("walletListContainer");
    const items = Object.entries(balances || {});
    
    if (items.length === 0) {
        container.innerHTML = `<p class="text-xs text-slate-400">Belum ada akun terdaftar</p>`;
        return;
    }

    container.innerHTML = items.map(([name, bal]) => `
        <div class="flex items-center justify-between p-2.5 rounded-2xl bg-slate-50/80 border border-slate-100 hover:bg-slate-100/70 transition">
            <div class="flex items-center gap-2.5">
                <div class="w-7 h-7 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-extrabold text-[11px]">
                    ${name.substring(0, 2).toUpperCase()}
                </div>
                <span class="text-xs font-bold text-slate-800">${name}</span>
            </div>
            <span class="text-xs font-extrabold ${bal < 0 ? 'text-rose-600' : 'text-slate-900'}">${formatIDR(bal)}</span>
        </div>
    `).join("");
}

function renderCategoryDonut(breakdown) {
    const canvas = document.getElementById("categoryDonutChart");
    const noExpText = document.getElementById("noExpenseText");
    const labels = Object.keys(breakdown || {});
    const values = Object.values(breakdown || {});

    if (values.length === 0 || values.reduce((a, b) => a + b, 0) === 0) {
        canvas.classList.add("hidden");
        noExpText.classList.remove("hidden");
        if (categoryDonutChart) {
            categoryDonutChart.destroy();
            categoryDonutChart = null;
        }
        return;
    }

    canvas.classList.remove("hidden");
    noExpText.classList.add("hidden");

    const bgColors = [
        '#6366f1', '#f43f5e', '#10b981', '#f59e0b', '#06b6d4',
        '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#64748b'
    ];

    if (categoryDonutChart) {
        categoryDonutChart.data.labels = labels;
        categoryDonutChart.data.datasets[0].data = values;
        categoryDonutChart.data.datasets[0].backgroundColor = bgColors.slice(0, labels.length);
        categoryDonutChart.update();
    } else {
        const ctx = canvas.getContext("2d");
        categoryDonutChart = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: bgColors.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: '#ffffff',
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            boxWidth: 10,
                            font: { size: 11, family: 'Plus Jakarta Sans' },
                            padding: 8
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return ` ${context.label}: ${formatIDR(context.raw)}`;
                            }
                        }
                    }
                },
                cutout: "68%"
            }
        });
    }
}

function renderCashflowBar(monthlyTrend) {
    const canvas = document.getElementById("cashflowBarChart");
    if (!monthlyTrend || monthlyTrend.length === 0) return;

    const periods = monthlyTrend.map(m => m.period);
    const incomes = monthlyTrend.map(m => m.income);
    const expenses = monthlyTrend.map(m => m.expense);

    if (cashflowBarChart) {
        cashflowBarChart.data.labels = periods;
        cashflowBarChart.data.datasets[0].data = incomes;
        cashflowBarChart.data.datasets[1].data = expenses;
        cashflowBarChart.update();
    } else {
        const ctx = canvas.getContext("2d");
        cashflowBarChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: periods,
                datasets: [
                    {
                        label: "Pemasukan",
                        data: incomes,
                        backgroundColor: "#10b981",
                        borderRadius: 8,
                    },
                    {
                        label: "Pengeluaran",
                        data: expenses,
                        backgroundColor: "#f43f5e",
                        borderRadius: 8,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { display: false }, ticks: { font: { family: 'Plus Jakarta Sans', size: 10 } } },
                    y: {
                        grid: { color: "#f8fafc" },
                        ticks: {
                            font: { family: 'Plus Jakarta Sans', size: 10 },
                            callback: function(value) {
                                if (value >= 1000000) return (value / 1000000) + ' Jt';
                                if (value >= 1000) return (value / 1000) + ' Rb';
                                return value;
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: "top",
                        align: "end",
                        labels: { boxWidth: 10, font: { size: 11, family: 'Plus Jakarta Sans' } }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return ` ${context.dataset.label}: ${formatIDR(context.raw)}`;
                            }
                        }
                    }
                }
            }
        });
    }
}

// -------------------------------------------------------------
// TRANSACTIONS (Desktop Table & Mobile Cards)
// -------------------------------------------------------------
function setTransactionType(type) {
    currentTransactionType = type;
    const btnExp = document.getElementById("btnTypeExpense");
    const btnInc = document.getElementById("btnTypeIncome");

    if (type === "Pengeluaran") {
        btnExp.className = "py-2.5 text-xs font-bold rounded-xl transition bg-white text-rose-600 shadow-sm";
        btnInc.className = "py-2.5 text-xs font-bold rounded-xl transition text-slate-500 hover:text-slate-700";
    } else {
        btnInc.className = "py-2.5 text-xs font-bold rounded-xl transition bg-white text-emerald-600 shadow-sm";
        btnExp.className = "py-2.5 text-xs font-bold rounded-xl transition text-slate-500 hover:text-slate-700";
    }

    populateCategoryDropdowns();
}

function debounceSearch() {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(loadTransactions, 300);
}

async function loadTransactions() {
    const tipe = document.getElementById("filterType").value;
    const kategori = document.getElementById("filterCategory").value;
    const akun = document.getElementById("filterWallet").value;
    const search = document.getElementById("filterSearch").value;

    let url = `/api/transactions?month=${currentMonth}&year=${currentYear}`;
    if (tipe !== "Semua") url += `&tipe=${encodeURIComponent(tipe)}`;
    if (kategori !== "Semua") url += `&kategori=${encodeURIComponent(kategori)}`;
    if (akun !== "Semua") url += `&akun=${encodeURIComponent(akun)}`;
    if (search.trim()) url += `&search=${encodeURIComponent(search.trim())}`;

    try {
        const res = await fetch(url);
        const json = await res.json();
        const tbody = document.getElementById("transactionTableBody");
        const mobileList = document.getElementById("mobileTransactionList");
        const emptyState = document.getElementById("emptyTransactionsState");

        if (json.status === "success" && json.data.length > 0) {
            emptyState.classList.add("hidden");
            
            // 1. Render Desktop Table Body
            tbody.innerHTML = json.data.map(t => {
                const isIncome = t.tipe === "Pemasukan";
                return `
                    <tr class="hover:bg-slate-50/80 transition">
                        <td class="py-3 px-4 text-slate-600 font-bold whitespace-nowrap">${formatDateIndo(t.tanggal)}</td>
                        <td class="py-3 px-4">
                            <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-[11px] font-extrabold ${isIncome ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}">
                                ${isIncome ? '↓' : '↑'} ${t.kategori || t.tipe}
                            </span>
                        </td>
                        <td class="py-3 px-4 text-slate-600 font-bold whitespace-nowrap">
                            <span class="px-2.5 py-1 bg-slate-100 rounded-xl text-[11px] font-bold">${t.akun || 'Cash'}</span>
                        </td>
                        <td class="py-3 px-4 text-slate-700 max-w-xs truncate font-medium">
                            ${t.keterangan || '-'}
                            ${t.id_cicilan ? `<span class="ml-1 text-[10px] bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded-lg border border-amber-200">Cicilan</span>` : ''}
                        </td>
                        <td class="py-3 px-4 text-right font-black whitespace-nowrap ${isIncome ? 'text-emerald-600' : 'text-rose-600'}">
                            ${isIncome ? '+' : '-'} ${formatIDR(t.jumlah)}
                        </td>
                        <td class="py-3 px-4 text-center">
                            <button onclick="deleteTransaction('${t.id}')" class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition" title="Hapus">
                                <i data-lucide="trash-2" class="w-4 h-4"></i>
                            </button>
                        </td>
                    </tr>
                `;
            }).join("");

            // 2. Render Mobile Card List (Fintech Mobile Style)
            mobileList.innerHTML = json.data.map(t => {
                const isIncome = t.tipe === "Pemasukan";
                return `
                    <div class="bg-white p-3.5 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between gap-3 active:bg-slate-50 transition">
                        <div class="flex items-center gap-3 min-w-0">
                            <div class="w-10 h-10 rounded-2xl ${isIncome ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'} flex items-center justify-center shrink-0">
                                <i data-lucide="${isIncome ? 'arrow-down-left' : 'arrow-up-right'}" class="w-5 h-5"></i>
                            </div>
                            <div class="min-w-0">
                                <h4 class="text-xs font-extrabold text-slate-900 truncate">${t.keterangan || t.kategori}</h4>
                                <div class="flex items-center gap-1.5 mt-0.5 text-[10px] text-slate-400 font-medium">
                                    <span>${formatDateIndo(t.tanggal)}</span>
                                    <span>•</span>
                                    <span class="font-bold text-slate-600">${t.akun || 'Cash'}</span>
                                    ${t.id_cicilan ? `<span class="bg-amber-50 text-amber-700 px-1 py-0.2 rounded text-[9px] font-bold">Cicilan</span>` : ''}
                                </div>
                            </div>
                        </div>
                        <div class="text-right shrink-0 flex items-center gap-2">
                            <div>
                                <p class="text-xs font-black ${isIncome ? 'text-emerald-600' : 'text-rose-600'}">
                                    ${isIncome ? '+' : '-'} ${formatIDR(t.jumlah)}
                                </p>
                                <span class="text-[10px] font-semibold text-slate-400">${t.kategori}</span>
                            </div>
                            <button onclick="deleteTransaction('${t.id}')" class="text-slate-300 hover:text-rose-600 p-1">
                                <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                            </button>
                        </div>
                    </div>
                `;
            }).join("");

        } else {
            tbody.innerHTML = "";
            mobileList.innerHTML = "";
            emptyState.classList.remove("hidden");
        }
        lucide.createIcons();
    } catch (e) {
        console.error("Error loading transactions:", e);
    }
}

async function submitTransaction(e) {
    e.preventDefault();
    const tanggal = document.getElementById("inputDate").value;
    const kategori = document.getElementById("inputCategory").value;
    const akun = document.getElementById("inputWallet").value;
    const jumlah = parseFloat(document.getElementById("inputAmount").value);
    const keterangan = document.getElementById("inputNote").value;

    if (!jumlah || jumlah <= 0) return showToast("Nominal harus lebih dari 0", "error");

    try {
        const res = await fetch("/api/transactions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                tanggal,
                tipe: currentTransactionType,
                kategori,
                akun,
                jumlah,
                keterangan
            })
        });
        const json = await res.json();
        if (json.status === "success") {
            showToast("Transaksi berhasil dicatat ke Excel!", "success");
            closeModal("modalTransaction");
            document.getElementById("inputAmount").value = "";
            document.getElementById("inputNote").value = "";
            await refreshAll();
        } else {
            showToast(json.detail || "Gagal menyimpan transaksi", "error");
        }
    } catch (e) {
        showToast("Terjadi kesalahan koneksi", "error");
    }
}

let isDeletingTrx = false;
async function deleteTransaction(trxId) {
    if (isDeletingTrx) return;
    if (!confirm("Apakah Anda yakin ingin menghapus transaksi ini dari Excel?")) return;

    isDeletingTrx = true;
    try {
        const res = await fetch(`/api/transactions/${trxId}`, { method: "DELETE" });
        const json = await res.json();
        if (res.status === 200 || json.status === "success") {
            showToast("Transaksi berhasil dihapus", "success");
        } else if (res.status === 404) {
            showToast("Transaksi sudah terhapus, data diperbarui", "info");
        } else {
            showToast(json.detail || "Gagal menghapus transaksi", "error");
        }
        await refreshAll();
    } catch (e) {
        showToast("Koneksi diperbarui", "info");
        await refreshAll();
    } finally {
        isDeletingTrx = false;
    }
}

// -------------------------------------------------------------
// ASSETS & INVESTASI (Saham, Crypto, Emas)
// -------------------------------------------------------------
async function loadAssets() {
    const filterCat = document.getElementById("filterAssetCategory") ? document.getElementById("filterAssetCategory").value : "Semua";
    let url = "/api/assets";
    if (filterCat && filterCat !== "Semua") url += `?kategori=${encodeURIComponent(filterCat)}`;

    try {
        const res = await fetch(url);
        const json = await res.json();
        const container = document.getElementById("assetsCardsContainer");
        const emptyState = document.getElementById("emptyAssetsState");
        const badge = document.getElementById("badgeAssetsCount");

        if (json.status === "success") {
            const list = json.data;
            badge.innerText = list.length;

            const totalVal = list.reduce((a, b) => a + b.nilai_saat_ini, 0);
            const totalCost = list.reduce((a, b) => a + b.total_modal, 0);
            const totalPnl = totalVal - totalCost;
            const retPct = totalCost > 0 ? ((totalPnl / totalCost) * 100).toFixed(2) : 0;

            document.getElementById("cardAssetTotalVal").innerText = formatIDR(totalVal);
            document.getElementById("cardAssetTotalCost").innerText = formatIDR(totalCost);
            
            const pnlCard = document.getElementById("cardAssetPnl");
            const pnlSub = document.getElementById("cardAssetPnlSub");
            const pnlSign = totalPnl >= 0 ? "+" : "";
            pnlCard.innerText = `${pnlSign}${formatIDR(totalPnl)}`;
            pnlCard.className = totalPnl >= 0 ? "text-xl sm:text-2xl font-black text-emerald-600 mt-1" : "text-xl sm:text-2xl font-black text-rose-600 mt-1";
            pnlSub.innerText = `Return: ${pnlSign}${retPct}%`;
            pnlSub.className = totalPnl >= 0 ? "text-[10px] font-bold text-emerald-600 mt-0.5" : "text-[10px] font-bold text-rose-600 mt-0.5";

            renderAssetDonut(list);

            if (list.length === 0) {
                container.innerHTML = "";
                emptyState.classList.remove("hidden");
                return;
            }

            emptyState.classList.add("hidden");
            container.innerHTML = list.map(a => {
                const isProfit = a.pnl >= 0;
                const sign = isProfit ? "+" : "";
                
                let catBadgeClass = "bg-purple-100 text-purple-800";
                if (a.kategori === "Crypto") catBadgeClass = "bg-amber-100 text-amber-800";
                else if (a.kategori === "Emas") catBadgeClass = "bg-yellow-100 text-yellow-800";
                else if (a.kategori === "Reksa Dana") catBadgeClass = "bg-emerald-100 text-emerald-800";

                return `
                    <div class="bg-white p-4 rounded-3xl border border-slate-200/80 shadow-sm space-y-3 relative hover:border-slate-300 transition">
                        <div class="flex items-start justify-between">
                            <div>
                                <div class="flex items-center gap-2">
                                    <h4 class="font-extrabold text-slate-900 text-sm">${a.nama}</h4>
                                    <span class="px-2 py-0.5 text-[10px] font-bold rounded-full ${catBadgeClass}">${a.kategori}</span>
                                </div>
                                <p class="text-xs text-slate-500 font-medium mt-0.5">${a.platform} • <span class="font-bold text-slate-700">${a.unit}</span></p>
                            </div>
                            <button onclick="deleteAsset('${a.id_aset}')" class="text-slate-400 hover:text-rose-600 p-1" title="Hapus Aset">
                                <i data-lucide="trash-2" class="w-4 h-4"></i>
                            </button>
                        </div>

                        <div class="grid grid-cols-2 gap-2 p-3 bg-slate-50/90 rounded-2xl text-xs">
                            <div>
                                <p class="text-[10px] font-bold text-slate-400 uppercase">Modal Beli</p>
                                <p class="font-bold text-slate-700">${formatIDR(a.total_modal)}</p>
                            </div>
                            <div>
                                <p class="text-[10px] font-bold text-slate-400 uppercase">Nilai Terkini</p>
                                <p class="font-black text-slate-900">${formatIDR(a.nilai_saat_ini)}</p>
                            </div>
                            <div class="col-span-2 pt-1 border-t border-slate-200/60 flex items-center justify-between">
                                <span class="text-[11px] text-slate-500 font-medium">Profit / Loss:</span>
                                <span class="font-black text-xs ${isProfit ? 'text-emerald-600' : 'text-rose-600'}">
                                    ${sign}${formatIDR(a.pnl)} (${sign}${a.return_pct}%)
                                </span>
                            </div>
                        </div>

                        ${a.catatan ? `<p class="text-[11px] text-slate-500 italic truncate font-medium">💬 ${a.catatan}</p>` : ''}

                        <button onclick="openEditAssetModal('${a.id_aset}', '${a.nama}', '${a.platform}', '${a.unit}', ${a.nilai_saat_ini}, '${a.catatan || ''}')" class="w-full py-2.5 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-2xl transition flex items-center justify-center gap-1.5 active:scale-98">
                            <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                            <span>Update Nilai Pasar</span>
                        </button>
                    </div>
                `;
            }).join("");

            lucide.createIcons();
        }
    } catch (e) {
        console.error("Error loading assets:", e);
    }
}

function renderAssetDonut(assets) {
    const canvas = document.getElementById("assetDonutChart");
    const noText = document.getElementById("noAssetText");
    if (!canvas) return;

    const breakdown = {};
    assets.forEach(a => {
        const k = a.kategori || "Lainnya";
        breakdown[k] = (breakdown[k] || 0) + a.nilai_saat_ini;
    });

    const labels = Object.keys(breakdown);
    const values = Object.values(breakdown);

    if (values.length === 0 || values.reduce((a, b) => a + b, 0) === 0) {
        canvas.classList.add("hidden");
        noText.classList.remove("hidden");
        if (assetDonutChart) {
            assetDonutChart.destroy();
            assetDonutChart = null;
        }
        return;
    }

    canvas.classList.remove("hidden");
    noText.classList.add("hidden");

    const bgColors = ['#8b5cf6', '#f59e0b', '#eab308', '#10b981', '#06b6d4', '#ec4899'];

    if (assetDonutChart) {
        assetDonutChart.data.labels = labels;
        assetDonutChart.data.datasets[0].data = values;
        assetDonutChart.data.datasets[0].backgroundColor = bgColors.slice(0, labels.length);
        assetDonutChart.update();
    } else {
        const ctx = canvas.getContext("2d");
        assetDonutChart = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: bgColors.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: '#ffffff',
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { boxWidth: 10, font: { size: 11, family: 'Plus Jakarta Sans' }, padding: 8 }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return ` ${context.label}: ${formatIDR(context.raw)}`;
                            }
                        }
                    }
                },
                cutout: "65%"
            }
        });
    }
}

async function submitAsset(e) {
    e.preventDefault();
    const kategori = document.getElementById("assetCategory").value;
    const nama = document.getElementById("assetName").value.trim();
    const platform = document.getElementById("assetPlatform").value.trim();
    const unit = document.getElementById("assetUnit").value.trim();
    const total_modal = parseFloat(document.getElementById("assetCost").value);
    const nilai_saat_ini = parseFloat(document.getElementById("assetCurrentVal").value);
    const catatan = document.getElementById("assetNote").value.trim();

    try {
        const res = await fetch("/api/assets", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                nama,
                kategori,
                platform,
                unit,
                total_modal,
                nilai_saat_ini,
                catatan
            })
        });
        const json = await res.json();
        if (json.status === "success") {
            showToast("Aset investasi berhasil disimpan ke Excel!", "success");
            closeModal("modalAsset");
            document.getElementById("assetName").value = "";
            document.getElementById("assetCost").value = "";
            document.getElementById("assetCurrentVal").value = "";
            document.getElementById("assetUnit").value = "";
            document.getElementById("assetNote").value = "";
            await refreshAll();
        } else {
            showToast(json.detail || "Gagal menyimpan aset", "error");
        }
    } catch (e) {
        showToast("Terjadi kesalahan koneksi", "error");
    }
}

function openEditAssetModal(id, nama, platform, unit, currentVal, note) {
    document.getElementById("editAssetId").value = id;
    document.getElementById("editAssetTitle").innerText = nama;
    document.getElementById("editAssetPlatform").innerText = `${platform} • ${unit}`;
    document.getElementById("editAssetVal").value = currentVal;
    document.getElementById("editAssetUnit").value = unit;
    document.getElementById("editAssetNote").value = note;
    openModal("modalUpdateAsset");
}

async function submitUpdateAsset(e) {
    e.preventDefault();
    const id = document.getElementById("editAssetId").value;
    const nilai_saat_ini = parseFloat(document.getElementById("editAssetVal").value);
    const unit = document.getElementById("editAssetUnit").value.trim();
    const catatan = document.getElementById("editAssetNote").value.trim();

    try {
        const res = await fetch(`/api/assets/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nilai_saat_ini, unit, catatan })
        });
        const json = await res.json();
        if (json.status === "success") {
            showToast("Nilai pasar aset berhasil diperbarui!", "success");
            closeModal("modalUpdateAsset");
            await refreshAll();
        } else {
            showToast(json.detail || "Gagal memperbarui nilai aset", "error");
        }
    } catch (e) {
        showToast("Terjadi kesalahan koneksi", "error");
    }
}

async function deleteAsset(id) {
    if (!confirm("Apakah Anda yakin ingin menghapus data aset ini dari Excel?")) return;

    try {
        const res = await fetch(`/api/assets/${id}`, { method: "DELETE" });
        const json = await res.json();
        if (json.status === "success") {
            showToast("Data aset berhasil dihapus", "success");
            await refreshAll();
        } else {
            showToast(json.detail || "Gagal menghapus aset", "error");
        }
    } catch (e) {
        showToast("Terjadi kesalahan koneksi", "error");
    }
}

// -------------------------------------------------------------
// INSTALLMENTS / CICILAN
// -------------------------------------------------------------
async function loadInstallments() {
    try {
        const res = await fetch("/api/installments");
        const json = await res.json();
        const grid = document.getElementById("installmentsGrid");
        const emptyState = document.getElementById("emptyInstallmentsState");
        const dashContainer = document.getElementById("dashboardInstallmentsContainer");
        const badge = document.getElementById("badgeActiveInstallments");

        if (json.status === "success") {
            const list = json.data;
            const activeList = list.filter(i => i.status === "Aktif");
            badge.innerText = activeList.length;

            if (activeList.length === 0) {
                dashContainer.innerHTML = `<p class="text-xs text-slate-400 py-3">Tidak ada cicilan berjalan saat ini.</p>`;
            } else {
                dashContainer.innerHTML = activeList.map(inst => `
                    <div class="p-3 bg-slate-50/90 rounded-2xl border border-slate-100 flex items-center justify-between">
                        <div class="space-y-1">
                            <div class="flex items-center gap-1.5">
                                <span class="font-extrabold text-xs text-slate-900">${inst.nama}</span>
                                <span class="text-[9px] px-1.5 py-0.5 bg-indigo-50 text-indigo-700 font-bold rounded-lg border border-indigo-100">${inst.penyedia}</span>
                            </div>
                            <p class="text-[10px] text-slate-500 font-medium">Bulan ${inst.cicilan_ke}/${inst.tenor} • <span class="font-bold text-indigo-600">Tempo tgl ${inst.tgl_jatuh_tempo}</span></p>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="text-xs font-black text-slate-900">${formatIDR(inst.cicilan_bulanan)}</span>
                            <button onclick="openPayModal('${inst.id_cicilan}', '${inst.nama}', ${inst.cicilan_bulanan}, ${inst.cicilan_ke + 1}, ${inst.tenor})" class="px-2.5 py-1 text-xs font-bold text-emerald-700 bg-emerald-100 hover:bg-emerald-200 rounded-xl transition">
                                Bayar
                            </button>
                        </div>
                    </div>
                `).join("");
            }

            if (list.length === 0) {
                grid.innerHTML = "";
                emptyState.classList.remove("hidden");
                return;
            }

            emptyState.classList.add("hidden");
            grid.innerHTML = list.map(inst => {
                const isLunas = inst.status === "Lunas";
                return `
                    <div class="bg-white p-4 sm:p-5 rounded-3xl border ${isLunas ? 'border-emerald-200 bg-emerald-50/20' : 'border-slate-200/80'} shadow-sm space-y-3.5 relative overflow-hidden">
                        <div class="flex items-start justify-between">
                            <div>
                                <div class="flex items-center gap-2">
                                    <h4 class="font-extrabold text-slate-900 text-sm">${inst.nama}</h4>
                                    <span class="px-2 py-0.5 text-[10px] font-bold rounded-full ${isLunas ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
                                        ${inst.status}
                                    </span>
                                </div>
                                <p class="text-xs text-slate-400 font-medium">${inst.penyedia || 'Finance'}</p>
                            </div>
                            <button onclick="deleteInstallment('${inst.id_cicilan}')" class="text-slate-400 hover:text-rose-600 p-1">
                                <i data-lucide="trash-2" class="w-4 h-4"></i>
                            </button>
                        </div>

                        <div class="space-y-1">
                            <div class="flex items-center justify-between text-xs font-bold text-slate-600">
                                <span>Progress Pelunasan</span>
                                <span>${inst.cicilan_ke} / ${inst.tenor} Bulan (${inst.progress_pct}%)</span>
                            </div>
                            <div class="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                                <div class="h-full ${isLunas ? 'bg-emerald-500' : 'bg-indigo-600'} rounded-full transition-all duration-500" style="width: ${Math.min(100, inst.progress_pct)}%"></div>
                            </div>
                        </div>

                        <div class="grid grid-cols-2 gap-2 p-3 bg-slate-50/80 rounded-2xl text-xs">
                            <div>
                                <p class="text-[10px] font-bold text-slate-400 uppercase">Cicilan / Bln</p>
                                <p class="font-black text-slate-900">${formatIDR(inst.cicilan_bulanan)}</p>
                            </div>
                            <div>
                                <p class="text-[10px] font-bold text-slate-400 uppercase">Sisa Pokok</p>
                                <p class="font-black text-slate-900">${formatIDR(inst.sisa_hutang)}</p>
                            </div>
                            <div>
                                <p class="text-[10px] font-bold text-slate-400 uppercase">Sisa Tenor</p>
                                <p class="font-bold text-slate-700">${inst.sisa_tenor} Bulan</p>
                            </div>
                            <div>
                                <p class="text-[10px] font-bold text-indigo-600 uppercase">Jatuh Tempo</p>
                                <p class="font-extrabold text-indigo-700">Tiap Tgl ${inst.tgl_jatuh_tempo}</p>
                            </div>
                        </div>

                        ${!isLunas ? `
                            <button onclick="openPayModal('${inst.id_cicilan}', '${inst.nama}', ${inst.cicilan_bulanan}, ${inst.cicilan_ke + 1}, ${inst.tenor})" class="w-full py-2.5 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-2xl shadow-md shadow-emerald-600/20 transition flex items-center justify-center gap-1.5 active:scale-98">
                                <i data-lucide="check" class="w-4 h-4"></i>
                                <span>Bayar Cicilan Bulan Ini</span>
                            </button>
                        ` : `
                            <div class="text-center py-2 text-xs font-extrabold text-emerald-700 bg-emerald-100/70 rounded-2xl">
                                ✓ Lunas Sepenuhnya
                            </div>
                        `}
                    </div>
                `;
            }).join("");

            lucide.createIcons();
        }
    } catch (e) {
        console.error("Error loading installments:", e);
    }
}

async function submitInstallment(e) {
    e.preventDefault();
    const nama = document.getElementById("instName").value.trim();
    const penyedia = document.getElementById("instProvider").value.trim();
    const total_pinjaman = parseFloat(document.getElementById("instTotal").value);
    const cicilan_bulanan = parseFloat(document.getElementById("instMonthly").value);
    const tenor = parseInt(document.getElementById("instTenor").value);
    const cicilan_ke = parseInt(document.getElementById("instCurrentStep").value || 0);
    const tgl_jatuh_tempo = parseInt(document.getElementById("instDueDay").value || 10);

    try {
        const res = await fetch("/api/installments", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                nama,
                penyedia,
                total_pinjaman,
                cicilan_bulanan,
                tenor,
                cicilan_ke,
                tgl_jatuh_tempo
            })
        });
        const json = await res.json();
        if (json.status === "success") {
            showToast("Cicilan baru berhasil disimpan ke Excel!", "success");
            closeModal("modalInstallment");
            document.getElementById("instName").value = "";
            document.getElementById("instProvider").value = "";
            document.getElementById("instTotal").value = "";
            document.getElementById("instMonthly").value = "";
            await refreshAll();
        } else {
            showToast(json.detail || "Gagal menyimpan cicilan", "error");
        }
    } catch (e) {
        showToast("Terjadi kesalahan koneksi", "error");
    }
}

function openPayModal(id, nama, nominal, nextStep, totalTenor) {
    document.getElementById("payInstId").value = id;
    document.getElementById("payInstTitle").innerText = nama;
    document.getElementById("payInstAmount").innerText = formatIDR(nominal);
    document.getElementById("payInstProgress").innerText = `Pembayaran Bulan ke-${nextStep} dari ${totalTenor}`;
    openModal("modalPayInstallment");
}

async function submitPayInstallment(e) {
    e.preventDefault();
    const id = document.getElementById("payInstId").value;
    const wallet = document.getElementById("payInstWallet").value;
    const payment_date = document.getElementById("payInstDate").value;

    try {
        const res = await fetch(`/api/installments/${id}/pay`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ wallet, payment_date })
        });
        const json = await res.json();
        if (json.status === "success") {
            showToast("Pembayaran cicilan berhasil dicatat & tenor diupdate!", "success");
            closeModal("modalPayInstallment");
            await refreshAll();
        } else {
            showToast(json.detail || "Gagal memproses pembayaran cicilan", "error");
        }
    } catch (e) {
        showToast("Terjadi kesalahan koneksi", "error");
    }
}

async function deleteInstallment(id) {
    if (!confirm("Apakah Anda yakin ingin menghapus catatan cicilan ini dari Excel?")) return;

    try {
        const res = await fetch(`/api/installments/${id}`, { method: "DELETE" });
        const json = await res.json();
        if (json.status === "success") {
            showToast("Data cicilan berhasil dihapus", "success");
            await refreshAll();
        } else {
            showToast(json.detail || "Gagal menghapus cicilan", "error");
        }
    } catch (e) {
        showToast("Terjadi kesalahan koneksi", "error");
    }
}

// -------------------------------------------------------------
// BOT STATUS & CONFIG
// -------------------------------------------------------------
async function checkBotStatus() {
    try {
        const res = await fetch("/api/system-info");
        const json = await res.json();
        const badge = document.getElementById("botStatusBadge");
        const tokenInput = document.getElementById("settingBotToken");
        const allowedInput = document.getElementById("settingAllowedUsers");

        if (json.telegram_bot_configured) {
            badge.className = "px-2.5 py-1 text-xs font-bold rounded-full bg-emerald-100 text-emerald-800 flex items-center gap-1";
            badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Bot Terhubung (${json.telegram_bot_token_masked})`;
            if (tokenInput && !tokenInput.value) {
                tokenInput.placeholder = `Token aktif: ${json.telegram_bot_token_masked}`;
            }
            if (allowedInput && json.allowed_users && json.allowed_users.length > 0) {
                allowedInput.value = json.allowed_users.join(", ");
            }
        } else {
            badge.className = "px-2.5 py-1 text-xs font-bold rounded-full bg-amber-100 text-amber-800 flex items-center gap-1";
            badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span> Token Belum Diisi`;
        }
    } catch (e) {}
}

async function submitTelegramConfig(e) {
    e.preventDefault();
    const bot_token = document.getElementById("settingBotToken").value.trim();
    const allowed_users = document.getElementById("settingAllowedUsers").value.trim();

    if (!bot_token) return showToast("Bot Token tidak boleh kosong", "error");

    try {
        const res = await fetch("/api/settings/telegram", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ bot_token, allowed_users })
        });
        const json = await res.json();
        if (json.status === "success") {
            showToast("Token Bot Telegram berhasil disimpan ke .env!", "success");
            await checkBotStatus();
        } else {
            showToast(json.detail || "Gagal menyimpan konfigurasi", "error");
        }
    } catch (e) {
        showToast("Terjadi kesalahan koneksi", "error");
    }
}

// -------------------------------------------------------------
// UTILITIES & MODAL
// -------------------------------------------------------------
function openModal(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.remove("hidden");
        el.classList.add("flex");
    }
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.add("hidden");
        el.classList.remove("flex");
    }
}

function showToast(message, type = "info") {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.innerText = message;
    toast.classList.remove("hidden", "bg-slate-900", "bg-emerald-600", "bg-rose-600", "text-white");
    
    if (type === "success") {
        toast.classList.add("bg-emerald-600", "text-white");
    } else if (type === "error") {
        toast.classList.add("bg-rose-600", "text-white");
    } else {
        toast.classList.add("bg-slate-900", "text-white");
    }

    setTimeout(() => {
        toast.classList.add("hidden");
    }, 3500);
}

// -------------------------------------------------------------
// AUTHENTICATION & MULTI-USER MANAGEMENT
// -------------------------------------------------------------
let currentUser = null;
let isGoogleConfigured = false;

async function checkAuthStatus() {
    try {
        const res = await fetch("/api/auth/me");
        const json = await res.json();
        isGoogleConfigured = json.google_configured;
        
        const warningHint = document.getElementById("googleWarningHint");
        const warningGate = document.getElementById("googleWarningGate");
        if (isGoogleConfigured) {
            warningHint?.classList.add("hidden");
            warningGate?.classList.add("hidden");
        } else {
            warningHint?.classList.remove("hidden");
            warningGate?.classList.remove("hidden");
        }

        const loginGateScreen = document.getElementById("loginGateScreen");
        const appContainer = document.getElementById("appContainer");
        const btnLoginHeader = document.getElementById("btnLoginHeader");
        const userProfileBadge = document.getElementById("userProfileBadge");
        const userAvatarImg = document.getElementById("userAvatarImg");
        const userNameText = document.getElementById("userNameText");
        const userEmailText = document.getElementById("userEmailText");

        if (json.is_authenticated && json.user) {
            currentUser = json.user;
            if (loginGateScreen) loginGateScreen.classList.add("hidden");
            if (appContainer) {
                appContainer.classList.remove("hidden");
                appContainer.classList.add("flex");
            }
            if (btnLoginHeader) btnLoginHeader.classList.add("hidden");
            if (userProfileBadge) {
                userProfileBadge.classList.remove("hidden");
                userProfileBadge.classList.add("flex");
            }
            if (userAvatarImg) userAvatarImg.src = currentUser.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(currentUser.name)}&background=4f46e5&color=fff`;
            if (userNameText) userNameText.innerText = currentUser.name || currentUser.email.split("@")[0];
            if (userEmailText) userEmailText.innerText = currentUser.email || "-";
        } else {
            currentUser = null;
            if (loginGateScreen) {
                loginGateScreen.classList.remove("hidden");
                loginGateScreen.classList.add("flex");
            }
            if (appContainer) {
                appContainer.classList.add("hidden");
                appContainer.classList.remove("flex");
            }
            if (btnLoginHeader) btnLoginHeader.classList.remove("hidden");
            if (userProfileBadge) {
                userProfileBadge.classList.add("hidden");
                userProfileBadge.classList.remove("flex");
            }
        }
        lucide.createIcons();
    } catch (e) {
        console.error("Error checking auth status:", e);
    }
}

function openLoginModal() {
    closeUserDropdown();
    openModal("modalLogin");
}

async function startGoogleLogin() {
    try {
        const res = await fetch("/api/auth/google/url");
        const json = await res.json();
        if (json.status === "success" && json.url) {
            window.location.href = json.url;
        } else {
            showToast(json.message || "Google OAuth belum dikonfigurasi", "error");
            document.getElementById("googleWarningHint")?.classList.remove("hidden");
            document.getElementById("googleWarningGate")?.classList.remove("hidden");
        }
    } catch (e) {
        showToast("Gagal memulai login Google", "error");
    }
}

async function submitGateLogin(e) {
    e.preventDefault();
    const email = document.getElementById("gateEmailInput").value.trim();
    const name = document.getElementById("gateNameInput").value.trim();

    if (!email) return showToast("Email harus diisi", "error");

    try {
        const res = await fetch("/api/auth/demo-login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, name })
        });
        const json = await res.json();
        if (json.status === "success") {
            showToast(`Selamat datang, ${json.user.name}!`, "success");
            await checkAuthStatus();
            await refreshAll();
        } else {
            showToast(json.detail || "Gagal login", "error");
        }
    } catch (e) {
        showToast("Terjadi kesalahan koneksi", "error");
    }
}

async function submitDemoLogin(e) {
    e.preventDefault();
    const email = document.getElementById("loginEmailInput").value.trim();
    const name = document.getElementById("loginNameInput").value.trim();

    if (!email) return showToast("Email harus diisi", "error");

    try {
        const res = await fetch("/api/auth/demo-login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, name })
        });
        const json = await res.json();
        if (json.status === "success") {
            showToast(`Selamat datang, ${json.user.name}!`, "success");
            closeModal("modalLogin");
            await checkAuthStatus();
            await refreshAll();
        } else {
            showToast(json.detail || "Gagal login", "error");
        }
    } catch (e) {
        showToast("Terjadi kesalahan koneksi", "error");
    }
}

async function logout() {
    closeUserDropdown();
    if (!confirm("Apakah Anda yakin ingin keluar dari akun ini?")) return;

    try {
        await fetch("/api/auth/logout", { method: "POST" });
        showToast("Anda telah keluar", "info");
        await checkAuthStatus();
        await refreshAll();
    } catch (e) {
        showToast("Gagal logout", "error");
    }
}

function toggleUserDropdown() {
    const menu = document.getElementById("userDropdownMenu");
    if (menu) menu.classList.toggle("hidden");
}

function closeUserDropdown() {
    const menu = document.getElementById("userDropdownMenu");
    if (menu) menu.classList.add("hidden");
}

// Close dropdown when clicking outside
document.addEventListener("click", (e) => {
    const badge = document.getElementById("userProfileBadge");
    if (badge && !badge.contains(e.target)) {
        closeUserDropdown();
    }
});

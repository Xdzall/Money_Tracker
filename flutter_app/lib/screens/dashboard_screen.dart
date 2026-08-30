import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/summary_model.dart';
import '../services/api_service.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  SummaryModel? _summary;
  bool _isLoading = true;
  int _selectedMonth = DateTime.now().month;
  int _selectedYear = DateTime.now().year;

  final _currencyFormat = NumberFormat.currency(locale: 'id_ID', symbol: 'Rp ', decimalDigits: 0);

  final List<String> _monthNames = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
  ];

  @override
  void initState() {
    super.initState();
    _loadSummary();
  }

  Future<void> _loadSummary() async {
    setState(() => _isLoading = true);
    final summary = await ApiService.getSummary(month: _selectedMonth, year: _selectedYear);
    if (mounted) {
      setState(() {
        _summary = summary;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Text(
          "Dashboard Finansial",
          style: TextStyle(color: Color(0xFF0F172A), fontWeight: FontWeight.w900, fontSize: 18),
        ),
        actions: [
          // Period Selector Dropdown (Month & Year)
          Container(
            margin: const EdgeInsets.only(right: 16),
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: const Color(0xFFF1F5F9),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: const Color(0xFFE2E8F0)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButton<int>(
                  value: _selectedMonth,
                  underline: const SizedBox(),
                  icon: const Icon(Icons.keyboard_arrow_down, size: 16, color: Color(0xFF475569)),
                  style: const TextStyle(color: Color(0xFF0F172A), fontWeight: FontWeight.w700, fontSize: 12),
                  items: List.generate(12, (index) {
                    final m = index + 1;
                    return DropdownMenuItem(value: m, child: Text(_monthNames[m]));
                  }),
                  onChanged: (val) {
                    if (val != null) {
                      setState(() => _selectedMonth = val);
                      _loadSummary();
                    }
                  },
                ),
                Container(width: 1, height: 16, color: const Color(0xFFCBD5E1), margin: const EdgeInsets.symmetric(horizontal: 4)),
                DropdownButton<int>(
                  value: _selectedYear,
                  underline: const SizedBox(),
                  icon: const Icon(Icons.keyboard_arrow_down, size: 16, color: Color(0xFF475569)),
                  style: const TextStyle(color: Color(0xFF0F172A), fontWeight: FontWeight.w700, fontSize: 12),
                  items: [2025, 2026, 2027].map((y) => DropdownMenuItem(value: y, child: Text("$y"))).toList(),
                  onChanged: (val) {
                    if (val != null) {
                      setState(() => _selectedYear = val);
                      _loadSummary();
                    }
                  },
                ),
              ],
            ),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF4F46E5)))
          : RefreshIndicator(
              color: const Color(0xFF4F46E5),
              onRefresh: _loadSummary,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Main Net Cashflow Banner
                    _buildMainCard(),
                    const SizedBox(height: 16),

                    // Income & Expense Grid
                    Row(
                      children: [
                        Expanded(
                          child: _buildStatCard(
                            title: "Pemasukan",
                            amount: _summary?.totalIncome ?? 0,
                            color: const Color(0xFF10B981),
                            icon: Icons.arrow_downward,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _buildStatCard(
                            title: "Pengeluaran",
                            amount: _summary?.totalExpense ?? 0,
                            color: const Color(0xFFEF4444),
                            icon: Icons.arrow_upward,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // Net Worth & Assets Row
                    Row(
                      children: [
                        Expanded(
                          child: _buildSecondaryCard(
                            title: "Kas Cair",
                            amount: _summary?.totalLiquidCash ?? 0,
                            icon: Icons.account_balance_wallet,
                            color: const Color(0xFF0EA5E9),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _buildSecondaryCard(
                            title: "Beban Cicilan",
                            amount: _summary?.activeInstallmentBurden ?? 0,
                            icon: Icons.credit_card,
                            color: const Color(0xFF8B5CF6),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // Wallet Balances Section
                    const Text(
                      "Saldo Rekening & Dompet",
                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: Color(0xFF0F172A)),
                    ),
                    const SizedBox(height: 10),
                    _buildWalletBalances(),

                    const SizedBox(height: 20),
                    // Category Breakdown Section
                    const Text(
                      "Top Pengeluaran Kategori",
                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: Color(0xFF0F172A)),
                    ),
                    const SizedBox(height: 10),
                    _buildCategoryBreakdown(),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildMainCard() {
    final net = _summary?.netCashflow ?? 0;
    final isPos = net >= 0;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF4F46E5), Color(0xFF6366F1), Color(0xFF7C3AED)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF4F46E5).withOpacity(0.35),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                "SISA BERSIH (NET CASHFLOW)",
                style: TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.w800, letterSpacing: 0.5),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  isPos ? "SURPLUS" : "DEFISIT",
                  style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w800),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            _currencyFormat.format(net),
            style: const TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 12),
          Divider(color: Colors.white.withOpacity(0.2)),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text("Total Net Worth Finansial:", style: TextStyle(color: Colors.white70, fontSize: 12)),
              Text(
                _currencyFormat.format(_summary?.totalNetWorth ?? 0),
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 13),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard({required String title, required double amount, required Color color, required IconData icon}) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFE2E8F0)),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(title, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Color(0xFF64748B))),
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(color: color.withOpacity(0.12), shape: BoxShape.circle),
                child: Icon(icon, size: 14, color: color),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            _currencyFormat.format(amount),
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: color),
          ),
        ],
      ),
    );
  }

  Widget _buildSecondaryCard({required String title, required double amount, required IconData icon, required Color color}) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
            child: Icon(icon, size: 18, color: color),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: Color(0xFF64748B))),
                Text(
                  _currencyFormat.format(amount),
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: Color(0xFF0F172A)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWalletBalances() {
    final wallets = _summary?.walletBalances ?? {};
    if (wallets.isEmpty) {
      return const Text("Belum ada saldo akun tercatat", style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12));
    }
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: wallets.entries.map((e) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: const Color(0xFFE2E8F0)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.account_balance, size: 14, color: Color(0xFF4F46E5)),
              const SizedBox(width: 6),
              Text("${e.key}: ", style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF64748B))),
              Text(
                _currencyFormat.format(e.value),
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: Color(0xFF0F172A)),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _buildCategoryBreakdown() {
    final cats = _summary?.categoryBreakdown ?? {};
    if (cats.isEmpty) {
      return const Text("Belum ada pengeluaran pada periode ini", style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12));
    }
    final sorted = cats.entries.toList()..sort((a, b) => b.value.compareTo(a.value));
    return Column(
      children: sorted.take(5).map((e) {
        return Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: const Color(0xFFF1F5F9)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(e.key, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: Color(0xFF334155))),
              Text(
                _currencyFormat.format(e.value),
                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: Color(0xFFEF4444)),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/transaction_model.dart';
import '../services/api_service.dart';

class TransactionsScreen extends StatefulWidget {
  const TransactionsScreen({super.key});

  @override
  State<TransactionsScreen> createState() => _TransactionsScreenState();
}

class _TransactionsScreenState extends State<TransactionsScreen> {
  List<TransactionModel> _transactions = [];
  bool _isLoading = true;
  String _selectedFilter = 'Semua';
  final _searchController = TextEditingController();
  final _currencyFormat = NumberFormat.currency(locale: 'id_ID', symbol: 'Rp ', decimalDigits: 0);

  @override
  void initState() {
    super.initState();
    _loadTransactions();
  }

  Future<void> _loadTransactions() async {
    setState(() => _isLoading = true);
    final trxs = await ApiService.getTransactions(
      tipe: _selectedFilter == 'Semua' ? null : _selectedFilter,
      search: _searchController.text.trim(),
    );
    if (mounted) {
      setState(() {
        _transactions = trxs;
        _isLoading = false;
      });
    }
  }

  Future<void> _deleteTrx(String id) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Hapus Transaksi?"),
        content: const Text("Data yang dihapus tidak dapat dikembalikan."),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Batal")),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text("Hapus", style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      final success = await ApiService.deleteTransaction(id);
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Transaksi berhasil dihapus")),
        );
        _loadTransactions();
      }
    }
  }

  void _openAddModal() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _AddTransactionSheet(onSuccess: _loadTransactions),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Text(
          "Daftar Transaksi",
          style: TextStyle(color: Color(0xFF0F172A), fontWeight: FontWeight.w900, fontSize: 18),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _openAddModal,
        backgroundColor: const Color(0xFF4F46E5),
        icon: const Icon(Icons.add, color: Colors.white),
        label: const Text("Catat", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800)),
      ),
      body: Column(
        children: [
          // Filter Chips & Search Bar
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.white,
            child: Column(
              children: [
                TextField(
                  controller: _searchController,
                  onSubmitted: (_) => _loadTransactions(),
                  style: const TextStyle(fontSize: 13),
                  decoration: InputDecoration(
                    hintText: "Cari transaksi...",
                    prefixIcon: const Icon(Icons.search, size: 20, color: Color(0xFF64748B)),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, size: 18),
                            onPressed: () {
                              _searchController.clear();
                              _loadTransactions();
                            },
                          )
                        : null,
                    filled: true,
                    fillColor: const Color(0xFFF1F5F9),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: BorderSide.none,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _filterChip("Semua"),
                    const SizedBox(width: 8),
                    _filterChip("Pengeluaran"),
                    const SizedBox(width: 8),
                    _filterChip("Pemasukan"),
                  ],
                ),
              ],
            ),
          ),

          // Transaction List
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: Color(0xFF4F46E5)))
                : _transactions.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.receipt_long_outlined, size: 64, color: Colors.grey.shade300),
                            const SizedBox(height: 12),
                            const Text(
                              "Belum ada transaksi ditemukan",
                              style: TextStyle(color: Color(0xFF64748B), fontWeight: FontWeight.w600),
                            ),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        color: const Color(0xFF4F46E5),
                        onRefresh: _loadTransactions,
                        child: ListView.separated(
                          padding: const EdgeInsets.fromLTRB(16, 16, 16, 80),
                          itemCount: _transactions.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 10),
                          itemBuilder: (ctx, idx) {
                            final t = _transactions[idx];
                            final isIncome = t.tipe == "Pemasukan";
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
                                    width: 42,
                                    height: 42,
                                    decoration: BoxDecoration(
                                      color: isIncome ? const Color(0xFFECFDF5) : const Color(0xFFFEF2F2),
                                      borderRadius: BorderRadius.circular(14),
                                    ),
                                    child: Icon(
                                      isIncome ? Icons.arrow_downward : Icons.arrow_upward,
                                      color: isIncome ? const Color(0xFF10B981) : const Color(0xFFEF4444),
                                      size: 20,
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          t.kategori,
                                          style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13, color: Color(0xFF0F172A)),
                                        ),
                                        Text(
                                          "${t.tanggal} • ${t.akun}${t.keterangan.isNotEmpty ? ' • ${t.keterangan}' : ''}",
                                          style: const TextStyle(fontSize: 11, color: Color(0xFF64748B)),
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ],
                                    ),
                                  ),
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.end,
                                    children: [
                                      Text(
                                        "${isIncome ? '+' : '-'}${_currencyFormat.format(t.jumlah)}",
                                        style: TextStyle(
                                          fontWeight: FontWeight.w900,
                                          fontSize: 13,
                                          color: isIncome ? const Color(0xFF10B981) : const Color(0xFFEF4444),
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      GestureDetector(
                                        onTap: () => _deleteTrx(t.id),
                                        child: const Icon(Icons.delete_outline, size: 16, color: Color(0xFF94A3B8)),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            );
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _filterChip(String label) {
    final isSelected = _selectedFilter == label;
    return GestureDetector(
      onTap: () {
        setState(() => _selectedFilter = label);
        _loadTransactions();
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF4F46E5) : const Color(0xFFF1F5F9),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.white : const Color(0xFF475569),
            fontSize: 12,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}

class _AddTransactionSheet extends StatefulWidget {
  final VoidCallback onSuccess;
  const _AddTransactionSheet({required this.onSuccess});

  @override
  State<_AddTransactionSheet> createState() => _AddTransactionSheetState();
}

class _AddTransactionSheetState extends State<_AddTransactionSheet> {
  String _tipe = "Pengeluaran";
  final _amountController = TextEditingController();
  final _descController = TextEditingController();
  String _selectedCat = "Makanan & Minuman";
  String _selectedWallet = "BCA";
  bool _isSaving = false;

  final List<String> _incomeCats = ["Gaji", "Investasi / Dividen", "Bonus / THR", "Freelance", "Lainnya"];
  final List<String> _expenseCats = ["Makanan & Minuman", "Transportasi & Bensin", "Belanja Bulanan", "Tagihan & Utilitas", "Cicilan & Hutang", "Lain-lain"];
  final List<String> _wallets = ["BCA", "SeaBank", "Mandiri", "BRI", "Cash / Tunai", "GoPay", "OVO", "DANA"];

  Future<void> _submit() async {
    final amtText = _amountController.text.replaceAll('.', '').replaceAll(',', '').trim();
    final amt = double.tryParse(amtText);
    if (amt == null || amt <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Nominal transaksi tidak valid")));
      return;
    }

    setState(() => _isSaving = true);
    final now = DateTime.now();
    final dateStr = DateFormat('yyyy-MM-dd').format(now);

    final trx = TransactionModel(
      id: '',
      tanggal: dateStr,
      tipe: _tipe,
      kategori: _selectedCat,
      akun: _selectedWallet,
      jumlah: amt,
      keterangan: _descController.text.trim(),
    );

    final success = await ApiService.addTransaction(trx);
    if (mounted) {
      setState(() => _isSaving = false);
      if (success) {
        Navigator.pop(context);
        widget.onSuccess();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Transaksi berhasil disimpan ke Excel!")),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final cats = _tipe == "Pengeluaran" ? _expenseCats : _incomeCats;
    if (!cats.contains(_selectedCat)) {
      _selectedCat = cats.first;
    }

    return Container(
      padding: EdgeInsets.only(
        left: 20, right: 20, top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("Catat Transaksi Baru", style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
                IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
              ],
            ),
            const SizedBox(height: 12),

            // Toggle Tipe
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _tipe == "Pengeluaran" ? const Color(0xFFEF4444) : const Color(0xFFF1F5F9),
                      foregroundColor: _tipe == "Pengeluaran" ? Colors.white : const Color(0xFF475569),
                      elevation: 0,
                    ),
                    onPressed: () => setState(() => _tipe = "Pengeluaran"),
                    child: const Text("Pengeluaran", style: TextStyle(fontWeight: FontWeight.w800)),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _tipe == "Pemasukan" ? const Color(0xFF10B981) : const Color(0xFFF1F5F9),
                      foregroundColor: _tipe == "Pemasukan" ? Colors.white : const Color(0xFF475569),
                      elevation: 0,
                    ),
                    onPressed: () => setState(() => _tipe = "Pemasukan"),
                    child: const Text("Pemasukan", style: TextStyle(fontWeight: FontWeight.w800)),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Nominal Input
            TextField(
              controller: _amountController,
              keyboardType: TextInputType.number,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900),
              decoration: InputDecoration(
                labelText: "Nominal (Rp)",
                filled: true,
                fillColor: const Color(0xFFF8FAFC),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
              ),
            ),
            const SizedBox(height: 12),

            // Kategori Dropdown
            DropdownButtonFormField<String>(
              value: _selectedCat,
              decoration: InputDecoration(
                labelText: "Kategori",
                filled: true,
                fillColor: const Color(0xFFF8FAFC),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
              ),
              items: cats.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
              onChanged: (v) => setState(() => _selectedCat = v ?? cats.first),
            ),
            const SizedBox(height: 12),

            // Akun / Dompet Dropdown
            DropdownButtonFormField<String>(
              value: _selectedWallet,
              decoration: InputDecoration(
                labelText: "Akun / Dompet",
                filled: true,
                fillColor: const Color(0xFFF8FAFC),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
              ),
              items: _wallets.map((w) => DropdownMenuItem(value: w, child: Text(w))).toList(),
              onChanged: (v) => setState(() => _selectedWallet = v ?? _wallets.first),
            ),
            const SizedBox(height: 12),

            // Keterangan Input
            TextField(
              controller: _descController,
              decoration: InputDecoration(
                labelText: "Keterangan (Opsional)",
                filled: true,
                fillColor: const Color(0xFFF8FAFC),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
              ),
            ),
            const SizedBox(height: 20),

            ElevatedButton(
              onPressed: _isSaving ? null : _submit,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF4F46E5),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
              child: _isSaving
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                  : const Text("Simpan Transaksi", style: TextStyle(fontWeight: FontWeight.w800, fontSize: 14)),
            ),
          ],
        ),
      ),
    );
  }
}

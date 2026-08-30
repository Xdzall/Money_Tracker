import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/installment_model.dart';
import '../services/api_service.dart';

class InstallmentsScreen extends StatefulWidget {
  const InstallmentsScreen({super.key});

  @override
  State<InstallmentsScreen> createState() => _InstallmentsScreenState();
}

class _InstallmentsScreenState extends State<InstallmentsScreen> {
  List<InstallmentModel> _installments = [];
  bool _isLoading = true;
  final _currencyFormat = NumberFormat.currency(locale: 'id_ID', symbol: 'Rp ', decimalDigits: 0);

  @override
  void initState() {
    super.initState();
    _loadInstallments();
  }

  Future<void> _loadInstallments() async {
    setState(() => _isLoading = true);
    final list = await ApiService.getInstallments();
    if (mounted) {
      setState(() {
        _installments = list;
        _isLoading = false;
      });
    }
  }

  Future<void> _payInstallment(InstallmentModel inst) async {
    String selectedWallet = "BCA";
    final now = DateTime.now();
    final dateStr = DateFormat('yyyy-MM-dd').format(now);

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text("Bayar ${inst.nama}?"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("Nominal: ${_currencyFormat.format(inst.cicilanBulanan)}", style: const TextStyle(fontWeight: FontWeight.w700)),
              Text("Progress: Bulan ke-${inst.cicilanKe + 1} dari ${inst.tenor}"),
              const SizedBox(height: 16),
              const Text("Pilih Rekening / Dompet:", style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
              const SizedBox(height: 6),
              DropdownButtonFormField<String>(
                value: selectedWallet,
                items: ["BCA", "SeaBank", "Mandiri", "BRI", "Cash / Tunai", "GoPay"]
                    .map((w) => DropdownMenuItem(value: w, child: Text(w)))
                    .toList(),
                onChanged: (v) => setDialogState(() => selectedWallet = v ?? "BCA"),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Batal")),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF4F46E5)),
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text("Konfirmasi Bayar", style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );

    if (confirmed == true) {
      final success = await ApiService.payInstallment(inst.id, selectedWallet, dateStr);
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Pembayaran ${inst.nama} berhasil dicatat!")),
        );
        _loadInstallments();
      }
    }
  }

  Future<void> _deleteInstallment(String id, String name) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text("Hapus Cicilan?", style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
        content: Text("Apakah Anda yakin ingin menghapus data cicilan \"$name\"?"),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text("Batal", style: TextStyle(color: Color(0xFF64748B), fontWeight: FontWeight.w700)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFEF4444),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text("Hapus", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      final success = await ApiService.deleteInstallment(id);
      if (success) {
        _loadInstallments();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text("Cicilan \"$name\" berhasil dihapus"),
              backgroundColor: Colors.green.shade600,
              behavior: SnackBarBehavior.floating,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          );
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: const Text("Gagal menghapus cicilan"),
              backgroundColor: Colors.red.shade600,
              behavior: SnackBarBehavior.floating,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          );
        }
      }
    }
  }

  void _openAddInstallmentModal() {
    final nameCtrl = TextEditingController();
    final providerCtrl = TextEditingController(text: "Finance / Bank");
    final loanCtrl = TextEditingController();
    final monthlyCtrl = TextEditingController();
    final tenorCtrl = TextEditingController(text: "12");
    final currentStepCtrl = TextEditingController(text: "0");
    final dueDayCtrl = TextEditingController(text: "10");

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(ctx).viewInsets.bottom + 24,
          top: 24,
          left: 24,
          right: 24,
        ),
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
        ),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(color: Colors.grey.shade300, borderRadius: BorderRadius.circular(2)),
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                "Tambah Cicilan Baru",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: Color(0xFF0F172A)),
              ),
              const SizedBox(height: 4),
              const Text(
                "Pantau kewajiban cicilan bulanan dan sisa tenor",
                style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: nameCtrl,
                decoration: InputDecoration(
                  labelText: "Nama Cicilan / Barang",
                  hintText: "e.g. Motor Honda Beat, iPhone 15",
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: providerCtrl,
                decoration: InputDecoration(
                  labelText: "Penyedia / Bank / Leasing",
                  hintText: "e.g. FIF, BCA Finance, SeaBank Paylater",
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: loanCtrl,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        labelText: "Total Pokok Pinjaman (Rp)",
                        hintText: "e.g. 18000000",
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: monthlyCtrl,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        labelText: "Cicilan per Bulan (Rp)",
                        hintText: "e.g. 750000",
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: tenorCtrl,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        labelText: "Tenor (Bulan)",
                        hintText: "12",
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: currentStepCtrl,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        labelText: "Cicilan Ke-",
                        hintText: "0",
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: dueDayCtrl,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        labelText: "Jatuh Tempo (Tgl)",
                        hintText: "10",
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: () async {
                  final nama = nameCtrl.text.trim();
                  final penyedia = providerCtrl.text.trim();
                  final totalPinjaman = double.tryParse(loanCtrl.text.trim().replaceAll('.', '').replaceAll(',', '')) ?? 0.0;
                  final cicilanBulanan = double.tryParse(monthlyCtrl.text.trim().replaceAll('.', '').replaceAll(',', '')) ?? 0.0;
                  final tenor = int.tryParse(tenorCtrl.text.trim()) ?? 12;
                  final cicilanKe = int.tryParse(currentStepCtrl.text.trim()) ?? 0;
                  final tglJatuhTempo = int.tryParse(dueDayCtrl.text.trim()) ?? 10;

                  if (nama.isEmpty || cicilanBulanan <= 0) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text("Harap isi nama dan nominal cicilan")),
                    );
                    return;
                  }

                  Navigator.pop(ctx);
                  final success = await ApiService.addInstallment(
                    nama: nama,
                    penyedia: penyedia.isEmpty ? "Finance / Bank" : penyedia,
                    totalPinjaman: totalPinjaman > 0 ? totalPinjaman : (cicilanBulanan * tenor),
                    cicilanBulanan: cicilanBulanan,
                    tenor: tenor,
                    cicilanKe: cicilanKe,
                    tglJatuhTempo: tglJatuhTempo,
                  );

                  if (success) {
                    _loadInstallments();
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text("Cicilan baru berhasil ditambahkan!"), backgroundColor: Colors.green),
                      );
                    }
                  }
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF4F46E5),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 15),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
                child: const Text("Simpan Cicilan", style: TextStyle(fontWeight: FontWeight.w800)),
              ),
            ],
          ),
        ),
      ),
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
          "Daftar Cicilan & Hutang",
          style: TextStyle(color: Color(0xFF0F172A), fontWeight: FontWeight.w900, fontSize: 18),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: Color(0xFF4F46E5)),
            tooltip: "Segarkan Cicilan",
            onPressed: _loadInstallments,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _openAddInstallmentModal,
        backgroundColor: const Color(0xFF4F46E5),
        foregroundColor: Colors.white,
        icon: const Icon(Icons.add),
        label: const Text("Tambah Cicilan", style: TextStyle(fontWeight: FontWeight.w800)),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF4F46E5)))
          : RefreshIndicator(
              color: const Color(0xFF4F46E5),
              onRefresh: _loadInstallments,
              child: _installments.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.check_circle_outline, size: 64, color: Colors.green.shade300),
                          const SizedBox(height: 12),
                          const Text("Tidak ada cicilan aktif saat ini", style: TextStyle(color: Color(0xFF64748B), fontWeight: FontWeight.w700)),
                          const SizedBox(height: 16),
                          OutlinedButton.icon(
                            onPressed: _openAddInstallmentModal,
                            icon: const Icon(Icons.add),
                            label: const Text("Tambah Cicilan Baru"),
                          ),
                        ],
                      ),
                    )
                  : ListView.separated(
                      padding: const EdgeInsets.fromLTRB(16, 16, 16, 80),
                      itemCount: _installments.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (ctx, idx) {
                        final inst = _installments[idx];
                        return Container(
                          padding: const EdgeInsets.all(18),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: const Color(0xFFE2E8F0)),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.02),
                                blurRadius: 8,
                                offset: const Offset(0, 2),
                              ),
                            ],
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Expanded(
                                    child: Text(
                                      inst.nama,
                                      style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: Color(0xFF0F172A)),
                                    ),
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFFF1F5F9),
                                      borderRadius: BorderRadius.circular(10),
                                    ),
                                    child: Text(
                                      inst.penyedia,
                                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Color(0xFF475569)),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  IconButton(
                                    icon: const Icon(Icons.delete_outline, size: 20, color: Color(0xFF94A3B8)),
                                    padding: EdgeInsets.zero,
                                    constraints: const BoxConstraints(),
                                    tooltip: "Hapus Cicilan",
                                    onPressed: () => _deleteInstallment(inst.id, inst.nama),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 12),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const Text("Cicilan / Bulan", style: TextStyle(fontSize: 11, color: Color(0xFF64748B))),
                                      Text(
                                        _currencyFormat.format(inst.cicilanBulanan),
                                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: Color(0xFF4F46E5)),
                                      ),
                                    ],
                                  ),
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.end,
                                    children: [
                                      const Text("Jatuh Tempo", style: TextStyle(fontSize: 11, color: Color(0xFF64748B))),
                                      Text(
                                        "Tgl ${inst.tglJatuhTempo} Tiap Bln",
                                        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: Color(0xFFEF4444)),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                              const SizedBox(height: 14),

                              // Progress Bar
                              ClipRRect(
                                borderRadius: BorderRadius.circular(8),
                                child: LinearProgressIndicator(
                                  value: (inst.tenor > 0) ? (inst.cicilanKe / inst.tenor) : 0,
                                  backgroundColor: const Color(0xFFF1F5F9),
                                  valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF10B981)),
                                  minHeight: 8,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text("Progress: Bulan ${inst.cicilanKe} dari ${inst.tenor} (${inst.progressPct}%)", style: const TextStyle(fontSize: 11, color: Color(0xFF64748B))),
                                  Text("Sisa: ${_currencyFormat.format(inst.sisaHutang)}", style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Color(0xFF0F172A))),
                                ],
                              ),
                              const SizedBox(height: 16),

                              // Pay Button
                              SizedBox(
                                width: double.infinity,
                                child: ElevatedButton.icon(
                                  onPressed: () => _payInstallment(inst),
                                  icon: const Icon(Icons.payment, size: 16),
                                  label: const Text("Bayar Cicilan Bulan Ini", style: TextStyle(fontWeight: FontWeight.w800, fontSize: 12)),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: const Color(0xFF4F46E5),
                                    foregroundColor: Colors.white,
                                    padding: const EdgeInsets.symmetric(vertical: 12),
                                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
            ),
    );
  }
}

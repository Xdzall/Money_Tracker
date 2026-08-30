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
                        ],
                      ),
                    )
                  : ListView.separated(
                      padding: const EdgeInsets.all(16),
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
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
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

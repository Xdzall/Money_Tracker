class InstallmentModel {
  final String id;
  final String nama;
  final String penyedia;
  final double totalPinjaman;
  final double cicilanBulanan;
  final int tenor;
  final int cicilanKe;
  final int tglJatuhTempo;
  final String status;
  final int sisaTenor;
  final double sisaHutang;
  final double totalTerbayar;
  final double progressPct;

  InstallmentModel({
    required this.id,
    required this.nama,
    required this.penyedia,
    required this.totalPinjaman,
    required this.cicilanBulanan,
    required this.tenor,
    required this.cicilanKe,
    required this.tglJatuhTempo,
    required this.status,
    required this.sisaTenor,
    required this.sisaHutang,
    required this.totalTerbayar,
    required this.progressPct,
  });

  factory InstallmentModel.fromJson(Map<String, dynamic> json) {
    return InstallmentModel(
      id: json['id_cicilan']?.toString() ?? '',
      nama: json['nama']?.toString() ?? '',
      penyedia: json['penyedia']?.toString() ?? '',
      totalPinjaman: (json['total_pinjaman'] is num) ? (json['total_pinjaman'] as num).toDouble() : 0.0,
      cicilanBulanan: (json['cicilan_bulanan'] is num) ? (json['cicilan_bulanan'] as num).toDouble() : 0.0,
      tenor: (json['tenor'] is num) ? (json['tenor'] as num).toInt() : 0,
      cicilanKe: (json['cicilan_ke'] is num) ? (json['cicilan_ke'] as num).toInt() : 0,
      tglJatuhTempo: (json['tgl_jatuh_tempo'] is num) ? (json['tgl_jatuh_tempo'] as num).toInt() : 10,
      status: json['status']?.toString() ?? 'Aktif',
      sisaTenor: (json['sisa_tenor'] is num) ? (json['sisa_tenor'] as num).toInt() : 0,
      sisaHutang: (json['sisa_hutang'] is num) ? (json['sisa_hutang'] as num).toDouble() : 0.0,
      totalTerbayar: (json['total_terbayar'] is num) ? (json['total_terbayar'] as num).toDouble() : 0.0,
      progressPct: (json['progress_pct'] is num) ? (json['progress_pct'] as num).toDouble() : 0.0,
    );
  }
}

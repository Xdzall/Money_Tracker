class AssetModel {
  final String id;
  final String nama;
  final String kategori;
  final String platform;
  final String unit;
  final double totalModal;
  final double nilaiSaatIni;
  final double pnl;
  final double returnPct;
  final String catatan;

  AssetModel({
    required this.id,
    required this.nama,
    required this.kategori,
    required this.platform,
    required this.unit,
    required this.totalModal,
    required this.nilaiSaatIni,
    required this.pnl,
    required this.returnPct,
    required this.catatan,
  });

  factory AssetModel.fromJson(Map<String, dynamic> json) {
    return AssetModel(
      id: json['id_aset']?.toString() ?? '',
      nama: json['nama']?.toString() ?? '',
      kategori: json['kategori']?.toString() ?? 'Saham',
      platform: json['platform']?.toString() ?? 'Ajaib',
      unit: json['unit']?.toString() ?? '1',
      totalModal: (json['total_modal'] is num) ? (json['total_modal'] as num).toDouble() : 0.0,
      nilaiSaatIni: (json['nilai_saat_ini'] is num) ? (json['nilai_saat_ini'] as num).toDouble() : 0.0,
      pnl: (json['pnl'] is num) ? (json['pnl'] as num).toDouble() : 0.0,
      returnPct: (json['return_pct'] is num) ? (json['return_pct'] as num).toDouble() : 0.0,
      catatan: json['catatan']?.toString() ?? '',
    );
  }
}

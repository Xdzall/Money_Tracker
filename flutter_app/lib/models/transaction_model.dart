class TransactionModel {
  final String id;
  final String tanggal;
  final String tipe;
  final String kategori;
  final String akun;
  final double jumlah;
  final String keterangan;

  TransactionModel({
    required this.id,
    required this.tanggal,
    required this.tipe,
    required this.kategori,
    required this.akun,
    required this.jumlah,
    required this.keterangan,
  });

  factory TransactionModel.fromJson(Map<String, dynamic> json) {
    return TransactionModel(
      id: json['id_transaksi']?.toString() ?? '',
      tanggal: json['tanggal']?.toString() ?? '',
      tipe: json['tipe']?.toString() ?? 'Pengeluaran',
      kategori: json['kategori']?.toString() ?? 'Lain-lain',
      akun: json['akun']?.toString() ?? 'Cash',
      jumlah: (json['jumlah'] is num) ? (json['jumlah'] as num).toDouble() : 0.0,
      keterangan: json['keterangan']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'tanggal': tanggal,
      'tipe': tipe,
      'kategori': kategori,
      'akun': akun,
      'jumlah': jumlah,
      'keterangan': keterangan,
    };
  }
}

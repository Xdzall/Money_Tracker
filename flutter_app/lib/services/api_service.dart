import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/summary_model.dart';
import '../models/transaction_model.dart';
import '../models/installment_model.dart';
import '../models/asset_model.dart';
import 'auth_service.dart';

class ApiService {
  // Summary
  static Future<SummaryModel?> getSummary({int? month, int? year}) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      String url = ApiConfig.summary;
      List<String> queryParams = [];
      if (month != null) queryParams.add("month=$month");
      if (year != null) queryParams.add("year=$year");
      if (queryParams.isNotEmpty) {
        url += "?${queryParams.join('&')}";
      }

      final res = await http.get(Uri.parse(url), headers: headers);
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        if (data['status'] == 'success' && data['data'] != null) {
          return SummaryModel.fromJson(data['data']);
        }
      }
    } catch (e) {
      print("Error fetching summary: $e");
    }
    return null;
  }

  // Transactions
  static Future<List<TransactionModel>> getTransactions({
    int? month,
    int? year,
    String? tipe,
    String? search,
  }) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      String url = ApiConfig.transactions;
      List<String> queryParams = [];
      if (month != null) queryParams.add("month=$month");
      if (year != null) queryParams.add("year=$year");
      if (tipe != null && tipe.isNotEmpty && tipe != 'Semua') {
        queryParams.add("tipe=${Uri.encodeComponent(tipe)}");
      }
      if (search != null && search.isNotEmpty) {
        queryParams.add("search=${Uri.encodeComponent(search)}");
      }
      if (queryParams.isNotEmpty) {
        url += "?${queryParams.join('&')}";
      }

      final res = await http.get(Uri.parse(url), headers: headers);
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        if (data['status'] == 'success' && data['data'] is List) {
          return (data['data'] as List)
              .map((item) => TransactionModel.fromJson(item))
              .toList();
        }
      }
    } catch (e) {
      print("Error fetching transactions: $e");
    }
    return [];
  }

  static Future<bool> addTransaction(TransactionModel item) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final res = await http.post(
        Uri.parse(ApiConfig.transactions),
        headers: headers,
        body: jsonEncode(item.toJson()),
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        return data['status'] == 'success';
      }
    } catch (e) {
      print("Error adding transaction: $e");
    }
    return false;
  }

  static Future<bool> deleteTransaction(String id) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final res = await http.delete(
        Uri.parse("${ApiConfig.transactions}/$id"),
        headers: headers,
      );
      return res.statusCode == 200;
    } catch (e) {
      print("Error deleting transaction: $e");
    }
    return false;
  }

  // Installments
  static Future<List<InstallmentModel>> getInstallments() async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final res = await http.get(Uri.parse(ApiConfig.installments), headers: headers);
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        if (data['status'] == 'success' && data['data'] is List) {
          return (data['data'] as List)
              .map((item) => InstallmentModel.fromJson(item))
              .toList();
        }
      }
    } catch (e) {
      print("Error fetching installments: $e");
    }
    return [];
  }

  static Future<bool> addInstallment({
    required String nama,
    required String penyedia,
    required double totalPinjaman,
    required double cicilanBulanan,
    required int tenor,
    required int cicilanKe,
    required int tglJatuhTempo,
  }) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final res = await http.post(
        Uri.parse(ApiConfig.installments),
        headers: headers,
        body: jsonEncode({
          "nama": nama,
          "penyedia": penyedia,
          "total_pinjaman": totalPinjaman,
          "cicilan_bulanan": cicilanBulanan,
          "tenor": tenor,
          "cicilan_ke": cicilanKe,
          "tgl_jatuh_tempo": tglJatuhTempo,
        }),
      );
      return res.statusCode == 200;
    } catch (e) {
      print("Error adding installment: $e");
    }
    return false;
  }

  static Future<bool> deleteInstallment(String id) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final res = await http.delete(
        Uri.parse("${ApiConfig.installments}/$id"),
        headers: headers,
      );
      return res.statusCode == 200;
    } catch (e) {
      print("Error deleting installment: $e");
    }
    return false;
  }

  static Future<bool> payInstallment(String id, String wallet, String date) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final res = await http.post(
        Uri.parse("${ApiConfig.installments}/$id/pay"),
        headers: headers,
        body: jsonEncode({"wallet": wallet, "payment_date": date}),
      );
      return res.statusCode == 200;
    } catch (e) {
      print("Error paying installment: $e");
    }
    return false;
  }

  // Assets
  static Future<List<AssetModel>> getAssets() async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final res = await http.get(Uri.parse(ApiConfig.assets), headers: headers);
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        if (data['status'] == 'success' && data['data'] is List) {
          return (data['data'] as List)
              .map((item) => AssetModel.fromJson(item))
              .toList();
        }
      }
    } catch (e) {
      print("Error fetching assets: $e");
    }
    return [];
  }

  static Future<bool> addAsset({
    required String nama,
    required String kategori,
    required String platform,
    required String unit,
    required double totalModal,
    required double nilaiSaatIni,
    String catatan = "",
  }) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final res = await http.post(
        Uri.parse(ApiConfig.assets),
        headers: headers,
        body: jsonEncode({
          "nama": nama,
          "kategori": kategori,
          "platform": platform,
          "unit": unit,
          "total_modal": totalModal,
          "nilai_saat_ini": nilaiSaatIni,
          "catatan": catatan,
        }),
      );
      return res.statusCode == 200;
    } catch (e) {
      print("Error adding asset: $e");
    }
    return false;
  }

  static Future<bool> updateAsset({
    required String id,
    required double nilaiSaatIni,
    String? unit,
    double? totalModal,
    String? catatan,
  }) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final res = await http.put(
        Uri.parse("${ApiConfig.assets}/$id"),
        headers: headers,
        body: jsonEncode({
          "nilai_saat_ini": nilaiSaatIni,
          if (unit != null) "unit": unit,
          if (totalModal != null) "total_modal": totalModal,
          if (catatan != null) "catatan": catatan,
        }),
      );
      return res.statusCode == 200;
    } catch (e) {
      print("Error updating asset: $e");
    }
    return false;
  }

  static Future<bool> deleteAsset(String id) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final res = await http.delete(
        Uri.parse("${ApiConfig.assets}/$id"),
        headers: headers,
      );
      return res.statusCode == 200;
    } catch (e) {
      print("Error deleting asset: $e");
    }
    return false;
  }

  // Master Data
  static Future<Map<String, dynamic>> getMasterData() async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final res = await http.get(Uri.parse(ApiConfig.masterData), headers: headers);
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        if (data['status'] == 'success' && data['data'] != null) {
          return data['data'];
        }
      }
    } catch (e) {
      print("Error fetching master data: $e");
    }
    return {
      "income_categories": ["Gaji", "Investasi / Dividen", "Bonus / THR", "Freelance", "Lainnya"],
      "expense_categories": ["Makanan & Minuman", "Transportasi & Bensin", "Belanja Bulanan", "Tagihan & Utilitas", "Cicilan & Hutang", "Lain-lain"],
      "wallets": ["BCA", "SeaBank", "Mandiri", "BRI", "Cash / Tunai", "GoPay", "OVO", "DANA"]
    };
  }

  // Bot Config
  static Future<Map<String, dynamic>?> getUserBotConfig() async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final res = await http.get(Uri.parse(ApiConfig.userBotConfig), headers: headers);
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        if (data['status'] == 'success') {
          return data['data'];
        }
      }
    } catch (e) {
      print("Error getting bot config: $e");
    }
    return null;
  }

  static Future<bool> saveUserBotConfig(String token, int? tgId) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final res = await http.post(
        Uri.parse(ApiConfig.userBotConfig),
        headers: headers,
        body: jsonEncode({"bot_token": token, "telegram_user_id": tgId}),
      );
      return res.statusCode == 200;
    } catch (e) {
      print("Error saving bot config: $e");
    }
    return false;
  }

  static Future<bool> disconnectUserBot() async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final res = await http.post(
        Uri.parse("${ApiConfig.userBotConfig}/disconnect"),
        headers: headers,
      );
      return res.statusCode == 200;
    } catch (e) {
      print("Error disconnecting bot: $e");
    }
    return false;
  }

  // Admin
  static Future<List<Map<String, dynamic>>> getAdminUsers() async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final res = await http.get(
        Uri.parse("${ApiConfig.baseUrl}/api/admin/users"),
        headers: headers,
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        if (data['status'] == 'success' && data['data'] is List) {
          return List<Map<String, dynamic>>.from(data['data']);
        }
      }
    } catch (e) {
      print("Error fetching admin users: $e");
    }
    return [];
  }
}

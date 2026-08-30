class ApiConfig {
  static const String baseUrl = "https://moneytracker.mghazali.my.id";

  // Auth endpoints
  static const String authMe = "$baseUrl/api/auth/me";
  static const String authGoogleUrl = "$baseUrl/api/auth/google/url";
  static const String authDemoLogin = "$baseUrl/api/auth/demo-login";
  static const String authLogout = "$baseUrl/api/auth/logout";

  // Data endpoints
  static const String summary = "$baseUrl/api/summary";
  static const String transactions = "$baseUrl/api/transactions";
  static const String installments = "$baseUrl/api/installments";
  static const String assets = "$baseUrl/api/assets";
  static const String masterData = "$baseUrl/api/master-data";
  static const String userBotConfig = "$baseUrl/api/user/bot-config";
  static const String exportExcel = "$baseUrl/api/export";
}

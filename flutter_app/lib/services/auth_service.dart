import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/api_config.dart';

class AuthService {
  static const String _tokenKey = "session_token";
  static const String _userKey = "user_profile";

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  static Future<Map<String, dynamic>?> getUserProfile() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_userKey);
    if (raw != null) {
      try {
        return jsonDecode(raw) as Map<String, dynamic>;
      } catch (_) {}
    }
    return null;
  }

  static Future<void> saveSession(String token, Map<String, dynamic> user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
    await prefs.setString(_userKey, jsonEncode(user));
  }

  static Future<Map<String, String>> getAuthHeaders() async {
    final token = await getToken();
    Map<String, String> headers = {
      "Content-Type": "application/json",
      "Accept": "application/json",
    };
    if (token != null && token.isNotEmpty) {
      headers["Authorization"] = "Bearer $token";
      headers["Cookie"] = "session_token=$token";
    }
    return headers;
  }

  static Future<bool> loginDemo(String email, String name) async {
    try {
      final res = await http.post(
        Uri.parse(ApiConfig.authDemoLogin),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"email": email.trim(), "name": name.trim()}),
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        if (data['status'] == 'success') {
          final prefs = await SharedPreferences.getInstance();
          final token = data['token'];
          if (token != null) {
            await prefs.setString(_tokenKey, token.toString());
          }
          if (data['user'] != null) {
            await prefs.setString(_userKey, jsonEncode(data['user']));
          }
          return true;
        }
      }
    } catch (e) {
      print("Login demo error: $e");
    }
    return false;
  }

  static Future<Map<String, dynamic>> checkAuth() async {
    try {
      final headers = await getAuthHeaders();
      final res = await http.get(
        Uri.parse(ApiConfig.authMe),
        headers: headers,
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        if (data['is_authenticated'] == true && data['user'] != null) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString(_userKey, jsonEncode(data['user']));
          return {"is_authenticated": true, "user": data['user']};
        }
      }
    } catch (e) {
      print("Check auth error: $e");
    }
    return {"is_authenticated": false, "user": null};
  }

  static Future<void> logout() async {
    try {
      final headers = await getAuthHeaders();
      await http.post(Uri.parse(ApiConfig.authLogout), headers: headers);
    } catch (_) {}
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_userKey);
  }
}

import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import 'auth_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _tokenController = TextEditingController();
  final _idController = TextEditingController();
  Map<String, dynamic>? _botConfig;
  Map<String, dynamic>? _userProfile;
  bool _isLoading = true;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    final botCfg = await ApiService.getUserBotConfig();
    final profile = await AuthService.getUserProfile();
    if (mounted) {
      setState(() {
        _botConfig = botCfg;
        _userProfile = profile;
        if (botCfg != null && botCfg['telegram_user_id'] != null) {
          _idController.text = botCfg['telegram_user_id'].toString();
        }
        _isLoading = false;
      });
    }
  }

  Future<void> _saveBot() async {
    final token = _tokenController.text.trim();
    final idText = _idController.text.trim();
    final tgId = int.tryParse(idText);

    if (token.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Token Bot Telegram wajib diisi")),
      );
      return;
    }

    setState(() => _isSaving = true);
    final success = await ApiService.saveUserBotConfig(token, tgId);
    if (mounted) {
      setState(() => _isSaving = false);
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Bot Telegram pribadi Anda aktif 24/7!")),
        );
        _tokenController.clear();
        _loadData();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Gagal mengaktifkan bot. Periksa token Anda.")),
        );
      }
    }
  }

  Future<void> _disconnectBot() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Putuskan Bot Telegram?"),
        content: const Text("Bot tidak akan lagi merespons chat Telegram Anda."),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Batal")),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text("Putuskan", style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await ApiService.disconnectUserBot();
      _loadData();
    }
  }

  Future<void> _handleLogout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Keluar dari Akun?"),
        content: const Text("Anda harus login kembali untuk membuka data."),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Batal")),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text("Keluar", style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await AuthService.logout();
      if (mounted) {
        Navigator.pushAndRemoveUntil(
          context,
          MaterialPageRoute(builder: (_) => const AuthScreen()),
          (route) => false,
        );
      }
    }
  }

  void _showAdminUsersModal() async {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => FutureBuilder<List<Map<String, dynamic>>>(
        future: ApiService.getAdminUsers(),
        builder: (ctx, snapshot) {
          final isLoading = snapshot.connectionState == ConnectionState.waiting;
          final users = snapshot.data ?? [];

          return Container(
            height: MediaQuery.of(context).size.height * 0.75,
            padding: const EdgeInsets.all(20),
            decoration: const BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
            ),
            child: Column(
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
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      "Pengguna Terdaftar",
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Color(0xFF0F172A)),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: const Color(0xFFEEF2FF),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        "${users.length} User",
                        style: const TextStyle(fontWeight: FontWeight.w800, color: Color(0xFF4F46E5), fontSize: 12),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                const Text(
                  "Daftar akun, email, dan statistik data pengguna",
                  style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                ),
                const SizedBox(height: 16),
                Expanded(
                  child: isLoading
                      ? const Center(child: CircularProgressIndicator(color: Color(0xFF4F46E5)))
                      : users.isEmpty
                          ? const Center(child: Text("Belum ada pengguna terdaftar."))
                          : ListView.separated(
                              itemCount: users.length,
                              separatorBuilder: (_, __) => const SizedBox(height: 12),
                              itemBuilder: (ctx, idx) {
                                final u = users[idx];
                                final name = u['name'] ?? 'User';
                                final email = u['email'] ?? u['user_id'] ?? '-';
                                final trxCount = u['transactions_count'] ?? 0;
                                final instCount = u['installments_count'] ?? 0;
                                final hasBot = u['has_telegram_bot'] == true;
                                final lastSeen = u['last_seen'] ?? '-';
                                final method = u['login_method'] ?? 'Web / App';

                                return Container(
                                  padding: const EdgeInsets.all(14),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFF8FAFC),
                                    borderRadius: BorderRadius.circular(18),
                                    border: Border.all(color: const Color(0xFFE2E8F0)),
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          CircleAvatar(
                                            radius: 20,
                                            backgroundColor: const Color(0xFF4F46E5),
                                            child: Text(
                                              name.isNotEmpty ? name[0].toUpperCase() : 'U',
                                              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                                            ),
                                          ),
                                          const SizedBox(width: 12),
                                          Expanded(
                                            child: Column(
                                              crossAxisAlignment: CrossAxisAlignment.start,
                                              children: [
                                                Text(
                                                  name,
                                                  style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 14, color: Color(0xFF0F172A)),
                                                ),
                                                Text(
                                                  email,
                                                  style: const TextStyle(fontSize: 12, color: Color(0xFF4F46E5), fontWeight: FontWeight.w600),
                                                ),
                                              ],
                                            ),
                                          ),
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                            decoration: BoxDecoration(
                                              color: hasBot ? const Color(0xFFECFDF5) : const Color(0xFFF1F5F9),
                                              borderRadius: BorderRadius.circular(8),
                                            ),
                                            child: Text(
                                              hasBot ? "🤖 Bot ON" : "No Bot",
                                              style: TextStyle(
                                                fontSize: 10,
                                                fontWeight: FontWeight.w700,
                                                color: hasBot ? const Color(0xFF10B981) : const Color(0xFF64748B),
                                              ),
                                            ),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 10),
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Text(
                                            "📊 $trxCount Transaksi • $instCount Cicilan",
                                            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Color(0xFF334155)),
                                          ),
                                          Text(
                                            "Via: $method",
                                            style: const TextStyle(fontSize: 10, color: Color(0xFF94A3B8)),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        "Terakhir aktif: $lastSeen",
                                        style: const TextStyle(fontSize: 10, color: Color(0xFF94A3B8)),
                                      ),
                                    ],
                                  ),
                                );
                              },
                            ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isBotActive = _botConfig != null &&
        (_botConfig!['is_active'] == true || _botConfig!['is_running'] == true || (_botConfig!['bot_token'] != null && _botConfig!['bot_token'].toString().isNotEmpty));
    final isAdmin = _userProfile?['is_admin'] == true || (_userProfile?['email'] != null && _userProfile!['email'].toString().contains("mghazali"));

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Text(
          "Pengaturan & Akun",
          style: TextStyle(color: Color(0xFF0F172A), fontWeight: FontWeight.w900, fontSize: 18),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF4F46E5)))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // User Profile Card
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    child: Row(
                      children: [
                        CircleAvatar(
                          radius: 24,
                          backgroundColor: const Color(0xFF4F46E5),
                          child: Text(
                            (_userProfile?['name'] ?? 'U')[0].toUpperCase(),
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18),
                          ),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                _userProfile?['name'] ?? 'Pengguna',
                                style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15, color: Color(0xFF0F172A)),
                              ),
                              Text(
                                _userProfile?['email'] ?? 'Akun Terhubung',
                                style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                              ),
                            ],
                          ),
                        ),
                        if (isAdmin)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: const Color(0xFFFEF3C7),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: const Text("👑 Admin", style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: Color(0xFFD97706))),
                          ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Admin Users Card (Only if Admin)
                  if (isAdmin) ...[
                    Container(
                      padding: const EdgeInsets.all(18),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(colors: [Color(0xFF312E81), Color(0xFF4F46E5)]),
                        borderRadius: BorderRadius.circular(20),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF4F46E5).withOpacity(0.25),
                            blurRadius: 12,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Row(
                            children: [
                              Icon(Icons.admin_panel_settings, color: Colors.white, size: 20),
                              SizedBox(width: 8),
                              Text("Panel Admin: Kelola Pengguna", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 14)),
                            ],
                          ),
                          const SizedBox(height: 6),
                          const Text(
                            "Lihat daftar semua pengguna yang telah mendaftar, email mereka, dan status aktivitasnya.",
                            style: TextStyle(color: Colors.white70, fontSize: 12),
                          ),
                          const SizedBox(height: 12),
                          ElevatedButton.icon(
                            onPressed: _showAdminUsersModal,
                            icon: const Icon(Icons.people_alt, size: 16, color: Color(0xFF4F46E5)),
                            label: const Text("Lihat Daftar Pengguna Terdaftar", style: TextStyle(color: Color(0xFF4F46E5), fontWeight: FontWeight.w800, fontSize: 12)),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.white,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],

                  // Telegram Bot Setup Card
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Row(
                              children: [
                                Icon(Icons.smart_toy_outlined, color: Color(0xFF0284C7), size: 22),
                                SizedBox(width: 8),
                                Text("Bot Telegram Pribadi", style: TextStyle(fontWeight: FontWeight.w800, fontSize: 14, color: Color(0xFF0F172A))),
                              ],
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: isBotActive ? const Color(0xFFECFDF5) : const Color(0xFFF1F5F9),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                isBotActive ? "Online 24/7" : "Belum Terhubung",
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.w800,
                                  color: isBotActive ? const Color(0xFF059669) : const Color(0xFF64748B),
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          "Hubungkan bot Telegram Anda agar chat transaksi langsung tercatat ke akun privat Anda.",
                          style: TextStyle(fontSize: 12, color: Color(0xFF64748B), height: 1.4),
                        ),
                        const SizedBox(height: 16),

                        TextField(
                          controller: _tokenController,
                          style: const TextStyle(fontSize: 13, fontFamily: 'monospace'),
                          decoration: InputDecoration(
                            labelText: "HTTP API Token (Dari @BotFather)",
                            hintText: isBotActive ? "Token aktif tersimpan" : "7123456789:AAF...",
                            filled: true,
                            fillColor: const Color(0xFFF8FAFC),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
                          ),
                        ),
                        const SizedBox(height: 12),

                        TextField(
                          controller: _idController,
                          keyboardType: TextInputType.number,
                          style: const TextStyle(fontSize: 13, fontFamily: 'monospace'),
                          decoration: InputDecoration(
                            labelText: "Telegram User ID Anda (Dari @userinfobot)",
                            hintText: "Contoh: 8004700349",
                            filled: true,
                            fillColor: const Color(0xFFF8FAFC),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
                          ),
                        ),
                        const SizedBox(height: 16),

                        Row(
                          children: [
                            Expanded(
                              child: ElevatedButton(
                                onPressed: _isSaving ? null : _saveBot,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: const Color(0xFF0284C7),
                                  foregroundColor: Colors.white,
                                  padding: const EdgeInsets.symmetric(vertical: 12),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                                ),
                                child: _isSaving
                                    ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                                    : Text(isBotActive ? "Perbarui Bot" : "Aktifkan Bot Pribadi", style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 12)),
                              ),
                            ),
                            if (isBotActive) ...[
                              const SizedBox(width: 8),
                              OutlinedButton(
                                onPressed: _disconnectBot,
                                style: OutlinedButton.styleFrom(
                                  foregroundColor: Colors.red,
                                  side: const BorderSide(color: Colors.red),
                                  padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                                ),
                                child: const Text("Putuskan", style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12)),
                              ),
                            ],
                          ],
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Logout Button
                  OutlinedButton.icon(
                    onPressed: _handleLogout,
                    icon: const Icon(Icons.logout, color: Color(0xFFEF4444), size: 18),
                    label: const Text("Keluar dari Akun", style: TextStyle(color: Color(0xFFEF4444), fontWeight: FontWeight.w800)),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      side: const BorderSide(color: Color(0xFFFECACA)),
                      backgroundColor: const Color(0xFFFEF2F2),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}

class SummaryModel {
  final int month;
  final int year;
  final double totalIncome;
  final double totalExpense;
  final double netCashflow;
  final double totalAssetValue;
  final double totalAssetCost;
  final double assetPnl;
  final double totalLiquidCash;
  final double activeInstallmentBurden;
  final double totalNetWorth;
  final Map<String, double> categoryBreakdown;
  final Map<String, double> walletBalances;

  SummaryModel({
    required this.month,
    required this.year,
    required this.totalIncome,
    required this.totalExpense,
    required this.netCashflow,
    required this.totalAssetValue,
    required this.totalAssetCost,
    required this.assetPnl,
    required this.totalLiquidCash,
    required this.activeInstallmentBurden,
    required this.totalNetWorth,
    required this.categoryBreakdown,
    required this.walletBalances,
  });

  factory SummaryModel.fromJson(Map<String, dynamic> json) {
    Map<String, double> cats = {};
    if (json['category_breakdown'] is Map) {
      (json['category_breakdown'] as Map).forEach((k, v) {
        cats[k.toString()] = (v is num) ? v.toDouble() : 0.0;
      });
    }

    Map<String, double> wallets = {};
    if (json['wallet_balances'] is Map) {
      (json['wallet_balances'] as Map).forEach((k, v) {
        wallets[k.toString()] = (v is num) ? v.toDouble() : 0.0;
      });
    }

    return SummaryModel(
      month: (json['month'] is num) ? (json['month'] as num).toInt() : DateTime.now().month,
      year: (json['year'] is num) ? (json['year'] as num).toInt() : DateTime.now().year,
      totalIncome: (json['total_income'] is num) ? (json['total_income'] as num).toDouble() : 0.0,
      totalExpense: (json['total_expense'] is num) ? (json['total_expense'] as num).toDouble() : 0.0,
      netCashflow: (json['net_cashflow'] is num) ? (json['net_cashflow'] as num).toDouble() : 0.0,
      totalAssetValue: (json['total_asset_value'] is num) ? (json['total_asset_value'] as num).toDouble() : 0.0,
      totalAssetCost: (json['total_asset_cost'] is num) ? (json['total_asset_cost'] as num).toDouble() : 0.0,
      assetPnl: (json['asset_pnl'] is num) ? (json['asset_pnl'] as num).toDouble() : 0.0,
      totalLiquidCash: (json['total_liquid_cash'] is num) ? (json['total_liquid_cash'] as num).toDouble() : 0.0,
      activeInstallmentBurden: (json['active_installment_burden'] is num) ? (json['active_installment_burden'] as num).toDouble() : 0.0,
      totalNetWorth: (json['total_net_worth'] is num) ? (json['total_net_worth'] as num).toDouble() : 0.0,
      categoryBreakdown: cats,
      walletBalances: wallets,
    );
  }
}

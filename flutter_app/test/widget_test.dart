import 'package:flutter_test/flutter_test.dart';
import 'package:money_tracker_app/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const MoneyTrackerApp());
    expect(find.byType(MoneyTrackerApp), findsOneWidget);
  });
}

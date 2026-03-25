import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app.dart';
import 'core/analytics/analytics_provider.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: '.env');

  final analytics = await buildAnalyticsService();

  runApp(ProviderScope(
    overrides: [
      analyticsServiceProvider.overrideWithValue(analytics),
    ],
    child: const App(),
  ));
}

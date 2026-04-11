import 'package:flutter_dotenv/flutter_dotenv.dart';

class RuntimeConfig {
  RuntimeConfig._();

  static String get apiBaseUrl =>
      dotenv.env['BASE_URL']?.trim().isNotEmpty == true
          ? dotenv.env['BASE_URL']!.trim()
          : 'http://127.0.0.1:8000/api/v1';

  static String get paymentReturnUrlBase =>
      dotenv.env['PAYMENT_RETURN_URL_BASE']?.trim() ?? '';

  static String get websiteUrl => dotenv.env['WEBSITE_URL']?.trim() ?? '';
}

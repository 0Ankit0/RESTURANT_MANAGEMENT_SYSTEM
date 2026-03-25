// Stub for non-web platforms (mobile/desktop).
// On mobile, eSewa is handled entirely by the WebView — nothing needed here.
import 'dart:async';

Future<void> submitEsewaFormWeb(
    String formAction, Map<String, dynamic> fields) async {
  // No-op on mobile; WebView handles the form POST.
}

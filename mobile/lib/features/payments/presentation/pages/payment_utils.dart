// Conditional export: uses dart:html on web, no-op stub on mobile.
export 'payment_utils_stub.dart'
    if (dart.library.html) 'payment_utils_web.dart';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:webview_flutter/webview_flutter.dart';
import '../../data/models/payment.dart';
import '../providers/payment_provider.dart';

/// Callback result passed back when payment completes or fails.
class PaymentResult {
  final bool success;
  final String message;
  final VerifyPaymentResponse? response;

  const PaymentResult({required this.success, required this.message, this.response});
}

/// Full-screen WebView for both Khalti and eSewa payments.
///
/// Khalti: loads the [paymentUrl] directly.
/// eSewa: builds an HTML auto-submit form from [esewaFormFields] and [esewaFormAction].
///
/// Intercepts navigation to [callbackUrlPrefix] and extracts query params
/// to verify the payment via the backend.
class PaymentWebViewPage extends ConsumerStatefulWidget {
  final PaymentProvider provider;
  final String? paymentUrl;
  final String? esewaFormAction;
  final Map<String, dynamic>? esewaFormFields;
  final String callbackUrlPrefix;

  const PaymentWebViewPage({
    super.key,
    required this.provider,
    this.paymentUrl,
    this.esewaFormAction,
    this.esewaFormFields,
    this.callbackUrlPrefix = 'http://localhost:3000/payment-callback',
  });

  @override
  ConsumerState<PaymentWebViewPage> createState() => _PaymentWebViewPageState();
}

class _PaymentWebViewPageState extends ConsumerState<PaymentWebViewPage> {
  late final WebViewController _controller;
  bool _loading = true;
  bool _verifying = false;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(NavigationDelegate(
        onPageStarted: (_) => setState(() => _loading = true),
        onPageFinished: (_) => setState(() => _loading = false),
        onNavigationRequest: _onNavRequest,
      ));

    if (widget.provider == PaymentProvider.esewa) {
      _loadEsewaForm();
    } else {
      _controller.loadRequest(Uri.parse(widget.paymentUrl!));
    }
  }

  /// Builds an HTML page with a hidden form and auto-submits it for eSewa.
  void _loadEsewaForm() {
    final action = widget.esewaFormAction ??
        'https://rc-epay.esewa.com.np/api/epay/main/v2/form';
    final fields = widget.esewaFormFields ?? {};
    final inputs = fields.entries
        .map((e) =>
            '<input type="hidden" name="${e.key}" value="${e.value}" />')
        .join('\n');

    final html = '''
<!DOCTYPE html>
<html>
<body>
  <p style="font-family:sans-serif;text-align:center;margin-top:40px">
    Redirecting to eSewa…
  </p>
  <form id="f" method="POST" action="$action">
    $inputs
  </form>
  <script>document.getElementById('f').submit();</script>
</body>
</html>''';

    _controller.loadHtmlString(html);
  }

  NavigationDecision _onNavRequest(NavigationRequest request) {
    final url = request.url;
    if (url.startsWith(widget.callbackUrlPrefix)) {
      _handleCallback(Uri.parse(url));
      return NavigationDecision.prevent;
    }
    return NavigationDecision.navigate;
  }

  Future<void> _handleCallback(Uri uri) async {
    if (_verifying) return;
    setState(() => _verifying = true);

    final repo = ref.read(paymentRepositoryProvider);

    try {
      VerifyPaymentRequest verifyReq;
      if (widget.provider == PaymentProvider.khalti) {
        final pidx = uri.queryParameters['pidx'];
        verifyReq = VerifyPaymentRequest(
          provider: PaymentProvider.khalti,
          pidx: pidx,
        );
      } else {
        // eSewa sends base64-encoded `data` param
        final data = uri.queryParameters['data'];
        verifyReq = VerifyPaymentRequest(
          provider: PaymentProvider.esewa,
          data: data,
        );
      }

      final result = await repo.verifyPayment(verifyReq);
      if (!mounted) return;
      Navigator.of(context).pop(
        PaymentResult(
          success: result.status == PaymentStatus.completed,
          message: result.status == PaymentStatus.completed
              ? 'Payment completed successfully!'
              : 'Payment status: ${result.status.name}',
          response: result,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      Navigator.of(context).pop(
        PaymentResult(success: false, message: e.toString()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.provider.displayName} Payment'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.of(context).pop(
            const PaymentResult(success: false, message: 'Payment cancelled'),
          ),
        ),
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_loading || _verifying)
            Container(
              color: Colors.white.withValues(alpha: 0.85),
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const CircularProgressIndicator(),
                    const SizedBox(height: 16),
                    Text(
                      _verifying ? 'Verifying payment…' : 'Loading…',
                      style: const TextStyle(fontSize: 14),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}

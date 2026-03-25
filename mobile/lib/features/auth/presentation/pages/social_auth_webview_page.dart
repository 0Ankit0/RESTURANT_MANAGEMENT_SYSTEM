import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:webview_flutter/webview_flutter.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/network/api_endpoints.dart';

/// Result returned when social auth WebView completes.
class SocialAuthResult {
  final bool success;
  final String? accessToken;
  final String? refreshToken;
  final String? error;

  const SocialAuthResult({
    required this.success,
    this.accessToken,
    this.refreshToken,
    this.error,
  });
}

/// Full-screen WebView that handles the social OAuth2 flow.
///
/// Opens [provider]'s OAuth login URL (routed via the backend) and intercepts
/// the redirect to the frontend auth-callback URL, extracting the JWT tokens.
class SocialAuthWebViewPage extends StatefulWidget {
  final String provider;

  const SocialAuthWebViewPage({super.key, required this.provider});

  @override
  State<SocialAuthWebViewPage> createState() => _SocialAuthWebViewPageState();
}

class _SocialAuthWebViewPageState extends State<SocialAuthWebViewPage> {
  late final WebViewController _controller;
  bool _loading = true;

  @override
  void initState() {
    super.initState();

    final baseUrl = dotenv.env['BASE_URL'] ?? 'http://127.0.0.1:8000/api/v1';
    final apiBase = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
    final loginUrl = '$apiBase${ApiEndpoints.socialLogin(widget.provider)}';

    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(NavigationDelegate(
        onPageStarted: (_) => setState(() => _loading = true),
        onPageFinished: (_) => setState(() => _loading = false),
        onNavigationRequest: _onNavigationRequest,
      ))
      ..loadRequest(Uri.parse(loginUrl));
  }

  NavigationDecision _onNavigationRequest(NavigationRequest request) {
    final url = request.url;
    if (url.contains(AppConstants.socialAuthCallbackPrefix)) {
      final uri = Uri.parse(url);
      final access = uri.queryParameters['access'];
      final refresh = uri.queryParameters['refresh'];
      final error = uri.queryParameters['error'];

      if (error != null) {
        Navigator.of(context).pop(
          SocialAuthResult(success: false, error: error),
        );
      } else if (access != null && refresh != null) {
        Navigator.of(context).pop(
          SocialAuthResult(success: true, accessToken: access, refreshToken: refresh),
        );
      } else {
        Navigator.of(context).pop(
          const SocialAuthResult(success: false, error: 'oauth_failed'),
        );
      }
      return NavigationDecision.prevent;
    }
    return NavigationDecision.navigate;
  }

  String get _providerLabel {
    switch (widget.provider) {
      case 'google':
        return 'Google';
      case 'github':
        return 'GitHub';
      case 'facebook':
        return 'Facebook';
      default:
        return widget.provider[0].toUpperCase() + widget.provider.substring(1);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Sign in with $_providerLabel'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.of(context).pop(
            const SocialAuthResult(success: false, error: 'cancelled'),
          ),
        ),
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_loading)
            const Center(child: CircularProgressIndicator()),
        ],
      ),
    );
  }
}

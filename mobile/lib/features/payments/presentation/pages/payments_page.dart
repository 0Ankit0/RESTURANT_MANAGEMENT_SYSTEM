import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../data/models/payment.dart';
import '../providers/payment_provider.dart';
import '../../../../core/analytics/analytics_provider.dart';
import '../../../../core/analytics/analytics_events.dart';
import 'payment_utils.dart';
import 'payment_webview_page.dart';

class PaymentsPage extends ConsumerStatefulWidget {
  const PaymentsPage({super.key});

  @override
  ConsumerState<PaymentsPage> createState() => _PaymentsPageState();
}

class _PaymentsPageState extends ConsumerState<PaymentsPage> {
  final _formKey = GlobalKey<FormState>();
  final _amountCtrl = TextEditingController();
  final _orderNameCtrl = TextEditingController();
  final _customerNameCtrl = TextEditingController();
  final _customerPhoneCtrl = TextEditingController();

  PaymentProvider? _selectedProvider;
  bool _showForm = false;
  bool _initiating = false;
  String? _orderId;

  @override
  void initState() {
    super.initState();
    _orderId = 'ORDER-${DateTime.now().millisecondsSinceEpoch}';
  }

  @override
  void dispose() {
    _amountCtrl.dispose();
    _orderNameCtrl.dispose();
    _customerNameCtrl.dispose();
    _customerPhoneCtrl.dispose();
    super.dispose();
  }

  Future<void> _initiate() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    if (_selectedProvider == null) {
      _showError('Please select a payment provider');
      return;
    }

    final nprAmount = double.tryParse(_amountCtrl.text) ?? 0;
    if (nprAmount <= 0) {
      _showError('Amount must be greater than 0');
      return;
    }

    // Khalti expects paisa (×100), eSewa expects NPR directly
    final amount = _selectedProvider == PaymentProvider.khalti
        ? (nprAmount * 100).round()
        : nprAmount.round();

    final returnUrl = 'http://localhost:3000/payment-callback?provider=${_selectedProvider!.name}';

    setState(() => _initiating = true);

    try {
      final repo = ref.read(paymentRepositoryProvider);
      final result = await repo.initiatePayment(InitiatePaymentRequest(
        provider: _selectedProvider!,
        amount: amount,
        purchaseOrderId: _orderId!,
        purchaseOrderName: _orderNameCtrl.text.trim(),
        returnUrl: returnUrl,
        websiteUrl: 'http://localhost:3000',
        customerName: _customerNameCtrl.text.trim().isEmpty
            ? null
            : _customerNameCtrl.text.trim(),
        customerPhone: _customerPhoneCtrl.text.trim().isEmpty
            ? null
            : _customerPhoneCtrl.text.trim(),
      ));

      ref.read(analyticsServiceProvider).capture(
        PaymentAnalyticsEvents.paymentInitiated,
        {
          'provider': _selectedProvider!.name,
          'amount': nprAmount,
          'order_id': _orderId!,
        },
      );

      if (!mounted) return;
      setState(() => _initiating = false);

      await _openPaymentWebView(result);
    } catch (e) {
      if (!mounted) return;
      setState(() => _initiating = false);
      _showError(e.toString());
    }
  }

  Future<void> _openPaymentWebView(InitiatePaymentResponse response) async {
    if (kIsWeb) {
      await _handleWebPayment(response);
      return;
    }

    // ── Native mobile: full-screen WebView ──────────────────────────────
    final result = await Navigator.of(context).push<PaymentResult>(
      MaterialPageRoute(
        fullscreenDialog: true,
        builder: (_) => UncontrolledProviderScope(
          container: ProviderScope.containerOf(context),
          child: PaymentWebViewPage(
            provider: response.provider,
            paymentUrl: response.paymentUrl,
            esewaFormAction: response.extra?['form_action'] as String?,
            esewaFormFields:
                response.extra?['form_fields'] as Map<String, dynamic>?,
          ),
        ),
      ),
    );

    if (!mounted) return;

    if (result != null) {
      ref.read(analyticsServiceProvider).capture(
        result.success
            ? PaymentAnalyticsEvents.paymentCompleted
            : PaymentAnalyticsEvents.paymentFailed,
        {'provider': response.provider.name},
      );
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result.message),
          backgroundColor: result.success ? Colors.green : Colors.red,
        ),
      );
    }

    _resetForm();
  }

  /// Web fallback: Khalti → open payment URL in browser tab.
  /// eSewa → POST form via dart:html (see payment_utils_web.dart).
  Future<void> _handleWebPayment(InitiatePaymentResponse response) async {
    try {
      if (response.provider == PaymentProvider.esewa) {
        final formAction = response.extra?['form_action'] as String? ??
            'https://rc-epay.esewa.com.np/api/epay/main/v2/form';
        final formFields =
            response.extra?['form_fields'] as Map<String, dynamic>? ?? {};
        await submitEsewaFormWeb(formAction, formFields);
      } else {
        // Khalti and others: redirect to payment URL
        final url = response.paymentUrl;
        if (url != null) {
          await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
        }
      }
    } catch (e) {
      if (!mounted) return;
      _showError('Could not open payment page: $e');
    }
    _resetForm();
  }

  void _resetForm() {
    if (!mounted) return;
    ref.invalidate(transactionsProvider);
    setState(() {
      _showForm = false;
      _orderId = 'ORDER-${DateTime.now().millisecondsSinceEpoch}';
      _amountCtrl.clear();
      _orderNameCtrl.clear();
      _customerNameCtrl.clear();
      _customerPhoneCtrl.clear();
      _selectedProvider = null;
    });
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Payments'),
        actions: [
          IconButton(
            icon: Icon(_showForm ? Icons.close : Icons.add),
            tooltip: _showForm ? 'Cancel' : 'New Payment',
            onPressed: () => setState(() => _showForm = !_showForm),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(transactionsProvider),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (_showForm) ...[
              _PaymentForm(
                formKey: _formKey,
                selectedProvider: _selectedProvider,
                orderId: _orderId!,
                amountCtrl: _amountCtrl,
                orderNameCtrl: _orderNameCtrl,
                customerNameCtrl: _customerNameCtrl,
                customerPhoneCtrl: _customerPhoneCtrl,
                initiating: _initiating,
                onProviderSelected: (p) =>
                    setState(() => _selectedProvider = p),
                onInitiate: _initiate,
              ),
              const SizedBox(height: 24),
            ],
            const _TransactionList(),
          ],
        ),
      ),
    );
  }
}

// ─── Payment Initiation Form ───────────────────────────────────────────────

class _PaymentForm extends ConsumerWidget {
  final GlobalKey<FormState> formKey;
  final PaymentProvider? selectedProvider;
  final String orderId;
  final TextEditingController amountCtrl;
  final TextEditingController orderNameCtrl;
  final TextEditingController customerNameCtrl;
  final TextEditingController customerPhoneCtrl;
  final bool initiating;
  final ValueChanged<PaymentProvider> onProviderSelected;
  final VoidCallback onInitiate;

  const _PaymentForm({
    required this.formKey,
    required this.selectedProvider,
    required this.orderId,
    required this.amountCtrl,
    required this.orderNameCtrl,
    required this.customerNameCtrl,
    required this.customerPhoneCtrl,
    required this.initiating,
    required this.onProviderSelected,
    required this.onInitiate,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final providersAsync = ref.watch(paymentProvidersProvider);
    final theme = Theme.of(context);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('New Payment',
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),

              // Provider chips
              Text('Provider', style: theme.textTheme.labelMedium),
              const SizedBox(height: 8),
              providersAsync.when(
                data: (providers) => Wrap(
                  spacing: 8,
                  children: providers.map((p) {
                    final pv = PaymentProvider.fromString(p);
                    final selected = selectedProvider == pv;
                    return ChoiceChip(
                      label: Text(pv.displayName),
                      selected: selected,
                      onSelected: (_) => onProviderSelected(pv),
                    );
                  }).toList(),
                ),
                loading: () => const CircularProgressIndicator.adaptive(),
                error: (_, __) => const Text('Failed to load providers'),
              ),

              // Sandbox test credential hint
              if (selectedProvider == PaymentProvider.khalti) ...[
                const SizedBox(height: 8),
                _CredentialHint(
                  color: Colors.blue.shade50,
                  borderColor: Colors.blue.shade200,
                  title: 'Khalti Sandbox',
                  lines: const [
                    'Mobile: 9800000000 – 9800000005',
                    'MPIN: 1111  ·  OTP: 987654',
                    'Amount in NPR (e.g. 10 = NPR 10)',
                  ],
                ),
              ],
              if (selectedProvider == PaymentProvider.esewa) ...[
                const SizedBox(height: 8),
                _CredentialHint(
                  color: Colors.green.shade50,
                  borderColor: Colors.green.shade200,
                  title: 'eSewa Sandbox',
                  lines: const [
                    'ID: 9806800001 – 9806800005',
                    'Password: Nepal@123  ·  OTP: 123456',
                    'Amount in NPR (e.g. 100 = NPR 100)',
                  ],
                ),
              ],

              const SizedBox(height: 16),

              // Amount
              TextFormField(
                controller: amountCtrl,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Amount (NPR)',
                  hintText: 'e.g. 100',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.payments_outlined),
                ),
                validator: (v) {
                  if (v == null || v.isEmpty) return 'Required';
                  if ((double.tryParse(v) ?? 0) <= 0) return 'Must be > 0';
                  return null;
                },
              ),
              const SizedBox(height: 12),

              // Order name
              TextFormField(
                controller: orderNameCtrl,
                decoration: const InputDecoration(
                  labelText: 'Order / Product Name',
                  hintText: 'e.g. Subscription Plan',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.shopping_bag_outlined),
                ),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 12),

              // Order ID (read-only)
              TextFormField(
                initialValue: orderId,
                readOnly: true,
                decoration: const InputDecoration(
                  labelText: 'Order ID (auto-generated)',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.tag),
                ),
                style: const TextStyle(fontSize: 12, color: Colors.grey),
              ),
              const SizedBox(height: 12),

              // Customer name (optional)
              TextFormField(
                controller: customerNameCtrl,
                decoration: const InputDecoration(
                  labelText: 'Customer Name (optional)',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.person_outline),
                ),
              ),
              const SizedBox(height: 12),

              // Customer phone (optional)
              TextFormField(
                controller: customerPhoneCtrl,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(
                  labelText: 'Customer Phone (optional)',
                  hintText: '9800000000',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.phone_outlined),
                ),
              ),
              const SizedBox(height: 20),

              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: initiating ? null : onInitiate,
                  icon: initiating
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white),
                        )
                      : const Icon(Icons.open_in_new),
                  label: Text(initiating
                      ? 'Initiating…'
                      : selectedProvider != null
                          ? 'Pay with ${selectedProvider!.displayName}'
                          : 'Select a provider'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─── Transaction List ──────────────────────────────────────────────────────

class _TransactionList extends ConsumerWidget {
  const _TransactionList();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final txAsync = ref.watch(transactionsProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Transaction History',
          style: Theme.of(context)
              .textTheme
              .titleMedium
              ?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        txAsync.when(
          data: (txList) => txList.isEmpty
              ? const _EmptyTransactions()
              : Column(
                  children:
                      txList.map((tx) => _TransactionTile(tx: tx)).toList(),
                ),
          loading: () => const Center(
              child: Padding(
            padding: EdgeInsets.all(32),
            child: CircularProgressIndicator.adaptive(),
          )),
          error: (e, _) => Center(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text('Failed to load transactions: $e',
                  style: const TextStyle(color: Colors.red)),
            ),
          ),
        ),
      ],
    );
  }
}

class _TransactionTile extends StatelessWidget {
  final PaymentTransaction tx;
  const _TransactionTile({required this.tx});

  Color _statusColor() {
    switch (tx.status) {
      case PaymentStatus.completed:
        return Colors.green;
      case PaymentStatus.failed:
        return Colors.red;
      case PaymentStatus.initiated:
      case PaymentStatus.pending:
        return Colors.orange;
      case PaymentStatus.refunded:
        return Colors.blue;
      case PaymentStatus.cancelled:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    final amountDisplay = tx.provider == PaymentProvider.khalti
        ? 'NPR ${(tx.amount / 100).toStringAsFixed(2)}'
        : 'NPR ${tx.amount}';

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: _statusColor().withValues(alpha: 0.15),
          child: Icon(Icons.payment, color: _statusColor(), size: 20),
        ),
        title: Text(tx.purchaseOrderName,
            style: const TextStyle(fontWeight: FontWeight.w500)),
        subtitle: Text('${tx.provider.displayName} · $amountDisplay'),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: _statusColor().withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            tx.status.name.toUpperCase(),
            style: TextStyle(
                color: _statusColor(),
                fontSize: 10,
                fontWeight: FontWeight.bold),
          ),
        ),
      ),
    );
  }
}

class _EmptyTransactions extends StatelessWidget {
  const _EmptyTransactions();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(vertical: 32),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.receipt_long_outlined, size: 48, color: Colors.grey),
            SizedBox(height: 12),
            Text('No transactions yet',
                style: TextStyle(color: Colors.grey)),
          ],
        ),
      ),
    );
  }
}

// ─── Shared widget ─────────────────────────────────────────────────────────

class _CredentialHint extends StatelessWidget {
  final Color color;
  final Color borderColor;
  final String title;
  final List<String> lines;

  const _CredentialHint({
    required this.color,
    required this.borderColor,
    required this.title,
    required this.lines,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style: const TextStyle(
                  fontWeight: FontWeight.bold, fontSize: 12)),
          const SizedBox(height: 2),
          ...lines.map((l) => Text(l, style: const TextStyle(fontSize: 11))),
        ],
      ),
    );
  }
}

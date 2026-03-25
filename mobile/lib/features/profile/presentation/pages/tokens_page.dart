import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/error/error_handler.dart';
import '../../../../core/analytics/analytics_provider.dart';
import '../../../../core/analytics/analytics_events.dart';
import '../../data/models/token_tracking.dart';
import '../../../tokens/presentation/providers/token_provider.dart';

class TokensPage extends ConsumerWidget {
  const TokensPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tokensAsync = ref.watch(tokenListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Active Tokens'),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_sweep_outlined),
            tooltip: 'Revoke All',
            onPressed: () async {
              final confirm = await showDialog<bool>(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('Revoke All Tokens'),
                  content: const Text(
                      'This will log you out of all sessions. Continue?'),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(ctx, false),
                        child: const Text('Cancel')),
                    TextButton(
                        onPressed: () => Navigator.pop(ctx, true),
                        child: const Text('Revoke All',
                            style: TextStyle(color: Colors.red))),
                  ],
                ),
              );
              if (confirm == true && context.mounted) {
                try {
                  await ref
                      .read(tokenRepositoryProvider)
                      .revokeAllTokens();
                  ref.read(analyticsServiceProvider).capture(
                    UserAnalyticsEvents.tokenRevoked,
                    {'scope': 'all'},
                  );
                  ref.invalidate(tokenListProvider);
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                          content:
                              Text(ErrorHandler.handle(e).message),
                          backgroundColor: Colors.red),
                    );
                  }
                }
              }
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(tokensProvider),
        child: tokensAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 48, color: Colors.red),
                const SizedBox(height: 12),
                Text(ErrorHandler.handle(err).message,
                    textAlign: TextAlign.center),
                const SizedBox(height: 12),
                ElevatedButton(
                  onPressed: () => ref.invalidate(tokenListProvider),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
          data: (tokens) => tokens.isEmpty
              ? const Center(
                  child: Text('No active tokens found.',
                      style: TextStyle(color: Colors.grey)))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: tokens.length,
                  itemBuilder: (context, index) {
                    final token = tokens[index];
                    return _TokenCard(
                      token: token,
                      onRevoke: () async {
                        try {
                          await ref
                              .read(tokenRepositoryProvider)
                              .revokeToken(token.id);
                          ref.read(analyticsServiceProvider).capture(
                            UserAnalyticsEvents.tokenRevoked,
                            {'scope': 'single'},
                          );
                          ref.invalidate(tokenListProvider);
                        } catch (e) {
                          if (context.mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                  content: Text(ErrorHandler.handle(e).message),
                                  backgroundColor: Colors.red),
                            );
                          }
                        }
                      },
                    ).animate().fadeIn(delay: Duration(milliseconds: index * 50)).slideY(begin: 0.05);
                  },
                ),
        ),
      ),
    );
  }
}

class _TokenCard extends StatelessWidget {
  final TokenTracking token;
  final VoidCallback onRevoke;

  const _TokenCard({required this.token, required this.onRevoke});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: token.isActive
                        ? Colors.green.withValues(alpha: 0.15)
                        : Colors.grey.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    token.tokenType.toJson().toUpperCase(),
                    style: TextStyle(
                      color: token.isActive ? Colors.green : Colors.grey,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.delete_outline, color: Colors.red),
                  onPressed: onRevoke,
                  tooltip: 'Revoke',
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (token.ipAddress.isNotEmpty)
              _Row(icon: Icons.location_on_outlined, text: token.ipAddress),
            if (token.userAgent.isNotEmpty)
              _Row(
                  icon: Icons.devices_outlined,
                  text: token.userAgent,
                  maxLines: 2),
            _Row(
                icon: Icons.access_time,
                text: 'Created: ${_formatDate(token.createdAt)}'),
            _Row(
                icon: Icons.timer_off_outlined,
                text: 'Expires: ${_formatDate(token.expiresAt)}'),
          ],
        ),
      ),
    );
  }

  String _formatDate(String dateStr) {
    try {
      final dt = DateTime.parse(dateStr).toLocal();
      return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')} '
          '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return dateStr;
    }
  }
}

class _Row extends StatelessWidget {
  final IconData icon;
  final String text;
  final int maxLines;

  const _Row({required this.icon, required this.text, this.maxLines = 1});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 16, color: Colors.grey),
          const SizedBox(width: 8),
          Expanded(
            child: Text(text,
                style: const TextStyle(fontSize: 13),
                maxLines: maxLines,
                overflow: TextOverflow.ellipsis),
          ),
        ],
      ),
    );
  }
}

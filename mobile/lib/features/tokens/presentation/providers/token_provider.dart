import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/models/paginated_response.dart';
import '../../../../core/providers/dio_provider.dart';
import '../../../profile/data/models/token_tracking.dart';
import '../../data/repositories/token_repository.dart';

final tokenRepositoryProvider = Provider<TokenRepository>((ref) {
  return TokenRepository(ref.watch(dioClientProvider));
});

final tokensProvider =
    FutureProvider.family<PaginatedResponse<TokenTracking>, ({int skip, int limit})>(
  (ref, params) => ref
      .watch(tokenRepositoryProvider)
      .getTokens(skip: params.skip, limit: params.limit),
);

final tokenListProvider = FutureProvider<List<TokenTracking>>((ref) async {
  final result = await ref.watch(tokenRepositoryProvider).getTokens();
  return result.items;
});

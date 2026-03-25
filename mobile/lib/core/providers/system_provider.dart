import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/capability_summary.dart';
import '../models/general_setting.dart';
import '../repositories/system_repository.dart';
import 'dio_provider.dart';

final systemRepositoryProvider = Provider<SystemRepository>((ref) {
  return SystemRepository(ref.watch(dioClientProvider));
});

final systemCapabilitiesProvider =
    FutureProvider<CapabilitySummary>((ref) async {
  return ref.watch(systemRepositoryProvider).getCapabilities();
});

final systemGeneralSettingsProvider = FutureProvider<List<GeneralSetting>>((
  ref,
) async {
  return ref.watch(systemRepositoryProvider).getGeneralSettings();
});

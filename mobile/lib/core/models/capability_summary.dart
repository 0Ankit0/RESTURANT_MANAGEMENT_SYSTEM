class CapabilitySummary {
  const CapabilitySummary({
    required this.modules,
    required this.activeProviders,
    required this.fallbackProviders,
  });

  final Map<String, bool> modules;
  final Map<String, String?> activeProviders;
  final Map<String, List<String>> fallbackProviders;

  factory CapabilitySummary.fromJson(Map<String, dynamic> json) {
    final modulesJson = json['modules'] as Map<String, dynamic>? ?? {};
    final activeJson = json['active_providers'] as Map<String, dynamic>? ?? {};
    final fallbackJson = json['fallback_providers'] as Map<String, dynamic>? ?? {};

    return CapabilitySummary(
      modules: {
        for (final entry in modulesJson.entries) entry.key: entry.value as bool? ?? false,
      },
      activeProviders: {
        for (final entry in activeJson.entries) entry.key: entry.value as String?,
      },
      fallbackProviders: {
        for (final entry in fallbackJson.entries)
          entry.key: ((entry.value as List<dynamic>?) ?? []).map((item) => item.toString()).toList(),
      },
    );
  }
}

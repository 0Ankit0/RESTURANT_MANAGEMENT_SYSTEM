class GeneralSetting {
  const GeneralSetting({
    required this.key,
    required this.envValue,
    required this.dbValue,
    required this.effectiveValue,
    required this.source,
    required this.useDbValue,
    required this.isRuntimeEditable,
  });

  final String key;
  final String? envValue;
  final String? dbValue;
  final String? effectiveValue;
  final String source;
  final bool useDbValue;
  final bool isRuntimeEditable;

  factory GeneralSetting.fromJson(Map<String, dynamic> json) {
    return GeneralSetting(
      key: json['key'] as String? ?? '',
      envValue: json['env_value'] as String?,
      dbValue: json['db_value'] as String?,
      effectiveValue: json['effective_value'] as String?,
      source: json['source'] as String? ?? 'environment',
      useDbValue: json['use_db_value'] as bool? ?? false,
      isRuntimeEditable: json['is_runtime_editable'] as bool? ?? false,
    );
  }
}

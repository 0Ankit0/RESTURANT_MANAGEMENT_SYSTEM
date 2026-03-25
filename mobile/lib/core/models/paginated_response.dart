class PaginatedResponse<T> {
  final List<T> items;
  final int total;
  final int skip;
  final int limit;
  final bool hasMore;

  const PaginatedResponse({
    required this.items,
    required this.total,
    required this.skip,
    required this.limit,
    this.hasMore = false,
  });

  factory PaginatedResponse.fromJson(
    Map<String, dynamic> json,
    T Function(Map<String, dynamic>) fromJson,
  ) {
    final rawItems = json['items'] as List<dynamic>? ?? [];
    return PaginatedResponse(
      items: rawItems.map((e) => fromJson(e as Map<String, dynamic>)).toList(),
      total: json['total'] as int? ?? 0,
      skip: json['skip'] as int? ?? 0,
      limit: json['limit'] as int? ?? 10,
      hasMore: json['has_more'] as bool? ?? false,
    );
  }
}

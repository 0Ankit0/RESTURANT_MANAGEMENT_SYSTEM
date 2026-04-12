import 'dart:async';

enum PushRealtimeChannel {
  notifications,
  restaurant,
}

class PushRealtimeEvent {
  const PushRealtimeEvent({
    required this.channel,
    required this.event,
    this.branchId,
    this.payload = const {},
  });

  final PushRealtimeChannel channel;
  final String event;
  final int? branchId;
  final Map<String, dynamic> payload;
}

class PushRealtimeBridge {
  PushRealtimeBridge._();

  static final StreamController<PushRealtimeEvent> _controller =
      StreamController<PushRealtimeEvent>.broadcast();

  static Stream<PushRealtimeEvent> get stream => _controller.stream;

  static void emit(PushRealtimeEvent event) {
    if (!_controller.isClosed) {
      _controller.add(event);
    }
  }

  static PushRealtimeEvent? fromPushData(Map<String, dynamic> data) {
    final rawEvent = (data['event'] ?? data['type'] ?? '').toString();
    if (rawEvent.isEmpty) return null;

    final branchIdRaw = data['branch_id'];
    final branchId = branchIdRaw is int
        ? branchIdRaw
        : int.tryParse(branchIdRaw?.toString() ?? '');

    final channel = rawEvent.startsWith('restaurant.')
        ? PushRealtimeChannel.restaurant
        : PushRealtimeChannel.notifications;

    return PushRealtimeEvent(
      channel: channel,
      event: rawEvent,
      branchId: branchId,
      payload: data,
    );
  }
}

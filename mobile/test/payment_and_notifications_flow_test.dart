import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/realtime/push_realtime_bridge.dart';
import 'package:mobile/features/payments/data/models/payment.dart';

void main() {
  test('payment initiate/verify payloads preserve provider specific fields', () {
    const initiate = InitiatePaymentRequest(
      provider: PaymentProvider.khalti,
      amount: 1250,
      purchaseOrderId: 'ORDER-1',
      purchaseOrderName: 'Branch lunch',
      returnUrl: 'https://web/callback',
      websiteUrl: 'https://web',
      customerPhone: '9800000001',
    );
    final initiatePayload = initiate.toJson();
    expect(initiatePayload['provider'], 'khalti');
    expect(initiatePayload['amount'], 1250);
    expect(initiatePayload['customer_phone'], '9800000001');

    const verify = VerifyPaymentRequest(
      provider: PaymentProvider.esewa,
      oid: 'ORDER-1',
      refId: 'REF-1',
      transactionId: 'txn-123',
    );
    final verifyPayload = verify.toJson();
    expect(verifyPayload['provider'], 'esewa');
    expect(verifyPayload['oid'], 'ORDER-1');
    expect(verifyPayload['refId'], 'REF-1');
    expect(verifyPayload['transaction_id'], 'txn-123');
  });

  test('push bridge routes branch ops and notification events to correct channels', () {
    final restaurantEvent = PushRealtimeBridge.fromPushData({
      'event': 'restaurant.kitchen.ticket_ready',
      'branch_id': '5',
    });
    expect(restaurantEvent, isNotNull);
    expect(restaurantEvent!.channel, PushRealtimeChannel.restaurant);
    expect(restaurantEvent.branchId, 5);

    final notificationEvent = PushRealtimeBridge.fromPushData({
      'type': 'notifications.broadcast',
    });
    expect(notificationEvent, isNotNull);
    expect(notificationEvent!.channel, PushRealtimeChannel.notifications);
  });
}

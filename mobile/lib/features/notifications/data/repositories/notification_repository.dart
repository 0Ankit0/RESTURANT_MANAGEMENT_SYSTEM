import '../../../../core/error/error_handler.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../core/network/dio_client.dart';
import '../models/notification_list.dart';
import '../models/notification_device.dart';
import '../models/notification_preference.dart';
import '../models/push_config.dart';

class NotificationRepository {
  final DioClient _dioClient;

  NotificationRepository(this._dioClient);

  Future<NotificationList> getNotifications({
    bool unreadOnly = false,
    int skip = 0,
    int limit = 20,
  }) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.notifications,
        queryParameters: {
          'unread_only': unreadOnly,
          'skip': skip,
          'limit': limit,
        },
      );
      return NotificationList.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> markRead(String id) async {
    try {
      await _dioClient.dio.patch(ApiEndpoints.markNotificationRead(id));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> markAllRead() async {
    try {
      await _dioClient.dio.patch(ApiEndpoints.markAllNotificationsRead);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> deleteNotification(String id) async {
    try {
      await _dioClient.dio.delete(ApiEndpoints.deleteNotification(id));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<NotificationPreference> getPreferences() async {
    try {
      final response =
          await _dioClient.dio.get(ApiEndpoints.notificationPreferences);
      return NotificationPreference.fromJson(
          response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<NotificationPreference> updatePreferences(
      Map<String, bool> updates) async {
    try {
      final response = await _dioClient.dio.patch(
        ApiEndpoints.notificationPreferences,
        data: updates,
      );
      return NotificationPreference.fromJson(
          response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<List<NotificationDevice>> getDevices() async {
    try {
      final response = await _dioClient.dio.get(ApiEndpoints.notificationDevices);
      final data = response.data as List<dynamic>;
      return data
          .map((item) => NotificationDevice.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<NotificationDevice> registerDevice(Map<String, dynamic> payload) async {
    try {
      final provider = payload['provider'] as String?;
      final endpoint = provider == null
          ? ApiEndpoints.notificationDevices
          : ApiEndpoints.notificationDevicesByProvider(provider);
      final response = await _dioClient.dio.post(
        endpoint,
        data: payload,
      );
      return NotificationDevice.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> deleteDevice(int id) async {
    try {
      await _dioClient.dio.delete('${ApiEndpoints.notificationDevices}$id/');
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<PushConfig> getPushConfig() async {
    try {
      final response = await _dioClient.dio.get(ApiEndpoints.notificationPushConfig);
      return PushConfig.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }
}

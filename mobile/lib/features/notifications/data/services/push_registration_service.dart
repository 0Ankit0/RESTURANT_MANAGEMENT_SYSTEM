import 'dart:io';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:onesignal_flutter/onesignal_flutter.dart';

import '../models/notification_device.dart';
import '../models/push_config.dart';
import '../repositories/notification_repository.dart';

class PushRegistrationService {
  PushRegistrationService(this._repository);

  final NotificationRepository _repository;

  Future<void> sync({
    required PushConfig config,
    required List<NotificationDevice> existingDevices,
    required String userId,
  }) async {
    final activeProvider = config.provider;
    if (activeProvider == null) {
      return;
    }

    final hasActiveDevice = existingDevices.any(
      (device) => device.provider == activeProvider && device.isActive,
    );
    if (hasActiveDevice) {
      return;
    }

    if (activeProvider == 'fcm') {
      await _registerFcm(config, userId);
      return;
    }

    if (activeProvider == 'onesignal') {
      await _registerOneSignal(config, userId);
    }
  }

  Future<void> _registerFcm(PushConfig config, String userId) async {
    final providerConfig = config.fcm;
    if (!providerConfig.enabled ||
        providerConfig.apiKey == null ||
        providerConfig.appId == null ||
        providerConfig.messagingSenderId == null ||
        providerConfig.projectId == null) {
      return;
    }

    final app = Firebase.apps.where((candidate) => candidate.name == 'template-push');

    if (app.isEmpty) {
      await Firebase.initializeApp(
        name: 'template-push',
        options: FirebaseOptions(
          apiKey: providerConfig.apiKey!,
          appId: providerConfig.appId!,
          messagingSenderId: providerConfig.messagingSenderId!,
          projectId: providerConfig.projectId!,
          authDomain: providerConfig.authDomain,
          iosBundleId: dotenv.env['IOS_BUNDLE_ID'],
          measurementId: providerConfig.measurementId,
          storageBucket: providerConfig.storageBucket,
        ),
      );
    }

    final messaging = FirebaseMessaging.instance;
    await messaging.requestPermission(alert: true, badge: true, sound: true);
    final token = await messaging.getToken(
      vapidKey: kIsWeb ? providerConfig.webVapidKey : null,
    );
    if (token == null || token.isEmpty) {
      return;
    }

    await _repository.registerDevice({
      'provider': 'fcm',
      'platform': _platform,
      'token': token,
      'device_metadata': {
        'user_id': userId,
        'platform': _platform,
      },
    });
  }

  Future<void> _registerOneSignal(PushConfig config, String userId) async {
    final providerConfig = config.onesignal;
    if (!providerConfig.enabled || providerConfig.appId == null) {
      return;
    }

    OneSignal.initialize(providerConfig.appId!);
    await OneSignal.Notifications.requestPermission(false);
    await OneSignal.login(userId);

    final subscriptionId = OneSignal.User.pushSubscription.id;
    if (subscriptionId == null || subscriptionId.isEmpty) {
      return;
    }

    await _repository.registerDevice({
      'provider': 'onesignal',
      'platform': _platform,
      'subscription_id': subscriptionId,
      'device_metadata': {
        'user_id': userId,
        'platform': _platform,
      },
    });
  }

  String get _platform {
    if (kIsWeb) {
      return 'web';
    }
    if (Platform.isIOS) {
      return 'ios';
    }
    return 'android';
  }
}

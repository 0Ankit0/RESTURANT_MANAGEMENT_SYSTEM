import '../error/error_handler.dart';
import '../models/capability_summary.dart';
import '../models/general_setting.dart';
import '../network/api_endpoints.dart';
import '../network/dio_client.dart';

class SystemRepository {
  SystemRepository(this._dioClient);

  final DioClient _dioClient;

  Future<CapabilitySummary> getCapabilities() async {
    try {
      final response =
          await _dioClient.dio.get(ApiEndpoints.systemCapabilities);
      return CapabilitySummary.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<List<GeneralSetting>> getGeneralSettings() async {
    try {
      final response =
          await _dioClient.dio.get(ApiEndpoints.systemGeneralSettings);
      final data = response.data as List<dynamic>? ?? const [];
      return data
          .map((item) => GeneralSetting.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }
}

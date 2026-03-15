import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../constants/app_constants.dart';

/// Dio 기반 API 클라이언트. JWT 자동 주입, 에러 핸들링, 토큰 갱신.
class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late final Dio _dio;
  final _storage = const FlutterSecureStorage();

  // 로그아웃 콜백 (GoRouter redirect 트리거용)
  void Function()? onUnauthorized;

  ApiClient._internal() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: _onRequest,
        onError: _onError,
      ),
    );
  }

  Future<void> _onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _storage.read(key: AppConstants.tokenKey);
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  Future<void> _onError(
    DioException error,
    ErrorInterceptorHandler handler,
  ) async {
    if (error.response?.statusCode == 401) {
      await clearToken();
      onUnauthorized?.call();
    }
    handler.next(error);
  }

  // ── Token Management ──

  Future<void> saveToken(String token) async {
    await _storage.write(key: AppConstants.tokenKey, value: token);
  }

  Future<void> clearToken() async {
    await _storage.delete(key: AppConstants.tokenKey);
    await _storage.delete(key: AppConstants.refreshTokenKey);
  }

  Future<bool> hasToken() async {
    final token = await _storage.read(key: AppConstants.tokenKey);
    return token != null && token.isNotEmpty;
  }

  // ── HTTP Methods ──

  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
  }) async {
    return _dio.get<T>(path, queryParameters: queryParameters);
  }

  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
  }) async {
    return _dio.post<T>(path, data: data);
  }

  Future<Response<T>> put<T>(
    String path, {
    dynamic data,
  }) async {
    return _dio.put<T>(path, data: data);
  }

  Future<Response<T>> patch<T>(
    String path, {
    dynamic data,
  }) async {
    return _dio.patch<T>(path, data: data);
  }

  Future<Response<T>> delete<T>(String path) async {
    return _dio.delete<T>(path);
  }

  /// API 응답에서 data 필드를 추출합니다.
  static T? extractData<T>(Response response) {
    final body = response.data;
    if (body is Map<String, dynamic> && body['success'] == true) {
      return body['data'] as T?;
    }
    return null;
  }

  /// API 응답에서 error 메시지를 추출합니다.
  static String? extractError(Response? response) {
    if (response?.data is Map<String, dynamic>) {
      return response!.data['error'] as String?;
    }
    return null;
  }
}

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Dio 기반 API 클라이언트.
/// 기본 URL, Authorization 헤더, 에러 인터셉터를 설정합니다.
class ApiClient {
  static const String _baseUrl = 'https://your-api-domain.com';
  static const String _tokenKey = 'access_token';

  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late final Dio _dio;
  final _storage = const FlutterSecureStorage();

  ApiClient._internal() {
    _dio = Dio(
      BaseOptions(
        baseUrl: _baseUrl,
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
        onResponse: _onResponse,
        onError: _onError,
      ),
    );
  }

  /// 저장된 JWT 토큰을 Authorization 헤더에 주입합니다.
  Future<void> _onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _storage.read(key: _tokenKey);
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  /// 성공 응답을 그대로 통과시킵니다.
  void _onResponse(Response response, ResponseInterceptorHandler handler) {
    handler.next(response);
  }

  /// HTTP 에러를 처리합니다. 401 시 토큰을 삭제하고 로그인 화면으로 유도합니다.
  Future<void> _onError(
    DioException error,
    ErrorInterceptorHandler handler,
  ) async {
    if (error.response?.statusCode == 401) {
      await _storage.delete(key: _tokenKey);
    }
    handler.next(error);
  }

  /// JWT 토큰을 안전하게 저장합니다.
  Future<void> saveToken(String token) async {
    await _storage.write(key: _tokenKey, value: token);
  }

  /// 저장된 JWT 토큰을 삭제합니다.
  Future<void> clearToken() async {
    await _storage.delete(key: _tokenKey);
  }

  /// GET 요청을 수행합니다.
  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
  }) async {
    return _dio.get<T>(path, queryParameters: queryParameters);
  }

  /// POST 요청을 수행합니다.
  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
  }) async {
    return _dio.post<T>(path, data: data);
  }

  /// DELETE 요청을 수행합니다.
  Future<Response<T>> delete<T>(String path) async {
    return _dio.delete<T>(path);
  }
}

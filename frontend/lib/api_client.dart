import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

String _normalizedApiBaseUrl(String? value) {
  final compileTimeValue = const String.fromEnvironment('API_BASE_URL');
  final configured = value?.trim().isNotEmpty == true
      ? value!.trim()
      : compileTimeValue.trim();
  final configuredHost = Uri.tryParse(configured)?.host.toLowerCase();
  if (kIsWeb &&
      {'localhost', '127.0.0.1', '::1'}.contains(configuredHost)) {
    throw ArgumentError.value(
      configured,
      'API_BASE_URL',
      'Flutter Web must use the current origin or a same-origin proxy.',
    );
  }
  final fallback = kIsWeb
      ? '${Uri.base.origin}/api/v1'
      : defaultTargetPlatform == TargetPlatform.android
          ? 'http://10.0.2.2:8000/api/v1'
          : 'http://127.0.0.1:8000/api/v1';
  final base = configured.isEmpty ? fallback : configured;
  return base.endsWith('/') ? base : '$base/';
}

class ApiClient {
  ApiClient({String? baseUrl})
      : _dio = Dio(
          BaseOptions(
            baseUrl: _normalizedApiBaseUrl(baseUrl),
            connectTimeout: const Duration(seconds: 15),
            receiveTimeout: const Duration(seconds: 60),
            headers: const {'Accept': 'application/json'},
          ),
        ) {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          try {
            final token = await _storage.read(key: 'access_token');
            if (token != null && token.isNotEmpty) {
              options.headers['Authorization'] = 'Bearer $token';
            }
          } catch (_) {
            // Continue so callers receive the API's unauthenticated response
            // instead of leaving a request pending if platform storage fails.
          }
          handler.next(options);
        },
      ),
    );
  }

  final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  Future<Map<String, dynamic>> register(
    String name,
    String email,
    String password,
  ) async {
    final response = await _dio.post(
      'auth/register',
      data: {'full_name': name, 'email': email, 'password': password},
    );
    return _saveAuth(response.data);
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await _dio.post(
      'auth/login',
      data: {'email': email, 'password': password},
    );
    return _saveAuth(response.data);
  }

  Future<Map<String, dynamic>> _saveAuth(dynamic data) async {
    final result = _asMap(data);
    final token = result['access_token']?.toString();
    if (token == null || token.isEmpty) {
      throw const FormatException('The API did not return an access token.');
    }
    await _storage.write(key: 'access_token', value: token);
    return result;
  }

  Future<void> logout() => _storage.delete(key: 'access_token');

  Future<Map<String, dynamic>> me() async => _asMap((await _dio.get('auth/me')).data);

  Future<Map<String, dynamic>> stats() async =>
      _asMap((await _dio.get('dashboard/stats')).data);

  Future<List<Map<String, dynamic>>> contracts() async =>
      _items((await _dio.get('contracts')).data);

  Future<Map<String, dynamic>> contract(String id) async =>
      _asMap((await _dio.get('contracts/${Uri.encodeComponent(id)}')).data);

  Future<Map<String, dynamic>> rules() async => _asMap((await _dio.get('rules')).data);

  Future<List<Map<String, dynamic>>> chatHistory(String id) async =>
      _items((await _dio.get('contracts/${Uri.encodeComponent(id)}/chat')).data);

  Future<Map<String, dynamic>> upload({
    required String name,
    required Uint8List bytes,
    required String type,
    String state = '',
    String governingLaw = '',
    bool msmeSupplier = false,
  }) async {
    final data = FormData.fromMap({
      'file': MultipartFile.fromBytes(bytes, filename: name),
      'contract_type': type,
      'jurisdiction_state': state,
      'governing_law': governingLaw,
      'msme_supplier': msmeSupplier.toString(),
    });
    return _asMap((await _dio.post('contracts/upload', data: data)).data);
  }

  Future<Map<String, dynamic>> analyze(String id) async => _asMap(
        (await _dio.post('contracts/${Uri.encodeComponent(id)}/analyze')).data,
      );

  Future<Map<String, dynamic>> ask(String id, String message) async => _asMap(
        (await _dio.post(
          'contracts/${Uri.encodeComponent(id)}/chat',
          data: {'message': message},
        ))
            .data,
      );

  Future<Map<String, dynamic>> suggest(String id, String clauseId) async => _asMap(
        (await _dio.post(
          'contracts/${Uri.encodeComponent(id)}/suggestions',
          data: {'message': clauseId},
        ))
            .data,
      );

  Future<void> deleteContract(String id) async {
    await _dio.delete('contracts/${Uri.encodeComponent(id)}');
  }

  Future<Uint8List> report(String id) async {
    final response = await _dio.get<List<int>>(
      'contracts/${Uri.encodeComponent(id)}/report',
      options: Options(responseType: ResponseType.bytes),
    );
    return Uint8List.fromList(response.data ?? <int>[]);
  }

  static Map<String, dynamic> _asMap(dynamic data) {
    if (data is Map<String, dynamic>) return data;
    if (data is Map) return Map<String, dynamic>.from(data);
    throw const FormatException('The API returned an unexpected response.');
  }

  static List<Map<String, dynamic>> _items(dynamic data) {
    final items = _asMap(data)['items'];
    if (items is! List) return <Map<String, dynamic>>[];
    return items
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
  }
}

String friendlyError(Object error) {
  if (error is DioException) {
    final data = error.response?.data;
    if (data is Map && data['detail'] != null) return data['detail'].toString();
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.connectionError) {
      return 'Cannot reach the ContractSense API. Check its URL and that the server is running.';
    }
    if (error.response?.statusCode == 413) {
      return 'The selected file is larger than the server upload limit.';
    }
  }
  if (error is FormatException) return error.message;
  return error.toString().replaceFirst('Exception: ', '');
}

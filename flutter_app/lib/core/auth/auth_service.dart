import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../api/api_client.dart';

/// Firebase Auth 래퍼 서비스.
/// 구글, 카카오(OIDC), 애플 로그인을 지원합니다.
class AuthService {
  static final AuthService _instance = AuthService._internal();
  factory AuthService() => _instance;
  static AuthService get instance => _instance;

  AuthService._internal();

  final FirebaseAuth _auth = FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn();
  final ApiClient _apiClient = ApiClient();

  /// 현재 로그인된 Firebase 사용자를 반환합니다.
  User? get currentUser => _auth.currentUser;

  /// 인증 상태 변경 스트림을 반환합니다.
  Stream<User?> get authStateChanges => _auth.authStateChanges();

  /// Google 계정으로 로그인하고 백엔드 JWT를 발급받습니다.
  ///
  /// Returns:
  ///   String? - 발급된 JWT 액세스 토큰, 실패 시 null
  Future<String?> signInWithGoogle() async {
    try {
      final googleUser = await _googleSignIn.signIn();
      if (googleUser == null) return null;

      final googleAuth = await googleUser.authentication;
      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      final userCredential = await _auth.signInWithCredential(credential);
      return _exchangeFirebaseToken(userCredential);
    } catch (e) {
      rethrow;
    }
  }

  /// Apple 계정으로 로그인하고 백엔드 JWT를 발급받습니다.
  ///
  /// Returns:
  ///   String? - 발급된 JWT 액세스 토큰, 실패 시 null
  Future<String?> signInWithApple() async {
    try {
      final provider = AppleAuthProvider()
        ..addScope('email')
        ..addScope('fullName');

      final userCredential = await _auth.signInWithProvider(provider);
      return _exchangeFirebaseToken(userCredential);
    } catch (e) {
      rethrow;
    }
  }

  /// Firebase ID 토큰을 백엔드 JWT로 교환합니다.
  ///
  /// Args:
  ///   userCredential - Firebase UserCredential 객체
  ///
  /// Returns:
  ///   String? - 발급된 JWT 액세스 토큰
  Future<String?> _exchangeFirebaseToken(UserCredential userCredential) async {
    final idToken = await userCredential.user?.getIdToken();
    if (idToken == null) return null;

    final response = await _apiClient.post<Map<String, dynamic>>(
      '/api/v1/users/auth',
      data: {'firebase_token': idToken},
    );

    final accessToken = response.data?['data']?['access_token'] as String?;
    if (accessToken != null) {
      await _apiClient.saveToken(accessToken);
    }
    return accessToken;
  }

  /// 로그아웃 처리: Firebase 로그아웃 + 로컬 JWT 토큰 삭제.
  Future<void> signOut() async {
    await _googleSignIn.signOut();
    await _auth.signOut();
    await _apiClient.clearToken();
  }
}

import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../api/api_client.dart';

/// Firebase Auth + 백엔드 JWT 인증 서비스.
class AuthService {
  static final AuthService _instance = AuthService._internal();
  factory AuthService() => _instance;
  static AuthService get instance => _instance;

  AuthService._internal();

  final FirebaseAuth _auth = FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn();
  final ApiClient _apiClient = ApiClient();

  User? get currentUser => _auth.currentUser;
  Stream<User?> get authStateChanges => _auth.authStateChanges();

  /// Google 로그인 → Firebase → 백엔드 JWT 발급.
  Future<Map<String, dynamic>?> signInWithGoogle() async {
    final googleUser = await _googleSignIn.signIn();
    if (googleUser == null) return null;

    final googleAuth = await googleUser.authentication;
    final credential = GoogleAuthProvider.credential(
      accessToken: googleAuth.accessToken,
      idToken: googleAuth.idToken,
    );

    final userCredential = await _auth.signInWithCredential(credential);
    return _exchangeFirebaseToken(userCredential);
  }

  /// Apple 로그인 → Firebase → 백엔드 JWT 발급.
  Future<Map<String, dynamic>?> signInWithApple() async {
    final provider = AppleAuthProvider()
      ..addScope('email')
      ..addScope('fullName');

    final userCredential = await _auth.signInWithProvider(provider);
    return _exchangeFirebaseToken(userCredential);
  }

  /// Kakao (OIDC) 로그인 → Firebase → 백엔드 JWT 발급.
  Future<Map<String, dynamic>?> signInWithKakao() async {
    final provider = OAuthProvider('oidc.kakao');
    final userCredential = await _auth.signInWithProvider(provider);
    return _exchangeFirebaseToken(userCredential);
  }

  /// Firebase ID 토큰을 백엔드 JWT로 교환.
  Future<Map<String, dynamic>?> _exchangeFirebaseToken(
    UserCredential userCredential,
  ) async {
    final idToken = await userCredential.user?.getIdToken();
    if (idToken == null) return null;

    final response = await _apiClient.post<Map<String, dynamic>>(
      '/api/v1/users/auth',
      data: {'firebase_token': idToken},
    );

    final data = ApiClient.extractData<Map<String, dynamic>>(response);
    if (data == null) return null;

    final accessToken = data['access_token'] as String?;
    final refreshToken = data['refresh_token'] as String?;
    if (accessToken != null) {
      await _apiClient.saveToken(accessToken);
    }
    if (refreshToken != null) {
      await _apiClient.saveRefreshToken(refreshToken);
    }

    return data;
  }

  /// 로그아웃: Firebase + 로컬 토큰 삭제.
  Future<void> signOut() async {
    await _googleSignIn.signOut();
    await _auth.signOut();
    await _apiClient.clearToken();
  }

  /// 현재 로그인 상태 확인.
  Future<bool> isAuthenticated() async {
    if (currentUser == null) return false;
    return _apiClient.hasToken();
  }
}

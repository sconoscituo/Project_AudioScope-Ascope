import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/auth/auth_service.dart';
import 'features/auth/login_screen.dart';
import 'features/briefing/briefing_screen.dart';

/// AudioScope 앱 진입점.
/// Firebase 초기화 후 Riverpod ProviderScope로 앱을 래핑합니다.
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  runApp(const ProviderScope(child: AudioScopeApp()));
}

/// 앱 라우터 설정.
/// Firebase Auth 상태에 따라 로그인 화면 또는 브리핑 화면으로 리다이렉트합니다.
final _router = GoRouter(
  initialLocation: '/briefing',
  redirect: (context, state) {
    final authService = AuthService.instance;
    final isLoggedIn = authService.currentUser != null;
    final isLoginRoute = state.matchedLocation == '/login';

    if (!isLoggedIn && !isLoginRoute) return '/login';
    if (isLoggedIn && isLoginRoute) return '/briefing';
    return null;
  },
  routes: [
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginScreen(),
    ),
    GoRoute(
      path: '/briefing',
      builder: (context, state) => const BriefingScreen(),
    ),
  ],
);

/// AudioScope 루트 위젯.
class AudioScopeApp extends StatelessWidget {
  const AudioScopeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'AudioScope',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1A73E8),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
        fontFamily: 'Pretendard',
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1A73E8),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
        fontFamily: 'Pretendard',
      ),
      routerConfig: _router,
    );
  }
}

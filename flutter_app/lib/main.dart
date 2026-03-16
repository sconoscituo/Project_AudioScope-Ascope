import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'core/auth/auth_service.dart';
import 'core/theme/app_theme.dart';
import 'features/article/article_detail_screen.dart';
import 'features/auth/login_screen.dart';
import 'features/briefing/briefing_screen.dart';
import 'features/categories/category_screen.dart';
import 'features/home/home_screen.dart';
import 'features/onboarding/onboarding_screen.dart';
import 'features/settings/settings_screen.dart';
import 'features/splash/splash_screen.dart';
import 'features/subscription/subscription_screen.dart';
import 'features/support/faq_screen.dart';
import 'features/support/privacy_screen.dart';
import 'features/support/terms_screen.dart';
import 'features/trends/trends_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 상태바 투명
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
    ),
  );

  try {
    await Firebase.initializeApp();
  } catch (e) {
    // google-services.json 또는 GoogleService-Info.plist 미설치 시 무시
    debugPrint('Firebase init skipped: $e');
  }
  await initializeDateFormatting('ko_KR');

  runApp(const ProviderScope(child: AudioScopeApp()));
}

/// GoRouter 설정.
final _router = GoRouter(
  initialLocation: '/',
  redirect: (context, state) async {
    final path = state.matchedLocation;

    // 스플래시, 온보딩, 로그인은 인증 불필요
    if (path == '/' || path == '/onboarding' || path == '/login') {
      return null;
    }

    // 카테고리 초기 설정은 인증 후 접근
    if (path == '/categories') return null;

    final isAuth = await AuthService.instance.isAuthenticated();
    if (!isAuth) return '/login';
    return null;
  },
  routes: [
    // 스플래시
    GoRoute(
      path: '/',
      builder: (context, state) => const SplashScreen(),
    ),

    // 온보딩
    GoRoute(
      path: '/onboarding',
      builder: (context, state) => const OnboardingScreen(),
    ),

    // 로그인
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginScreen(),
    ),

    // 카테고리 초기 설정
    GoRoute(
      path: '/categories',
      builder: (context, state) => const CategoryScreen(isInitialSetup: true),
    ),

    // 메인 (ShellRoute로 하단 탭 유지)
    ShellRoute(
      builder: (context, state, child) => HomeScreen(child: child),
      routes: [
        GoRoute(
          path: '/home',
          pageBuilder: (context, state) => const NoTransitionPage(
            child: BriefingTab(),
          ),
        ),
        GoRoute(
          path: '/trends',
          pageBuilder: (context, state) => const NoTransitionPage(
            child: TrendsScreen(),
          ),
        ),
        GoRoute(
          path: '/settings',
          pageBuilder: (context, state) => const NoTransitionPage(
            child: SettingsScreen(),
          ),
        ),
      ],
    ),

    // 브리핑 상세
    GoRoute(
      path: '/briefing/:period',
      builder: (context, state) {
        final period = state.pathParameters['period']!;
        final tab = state.uri.queryParameters['tab'];
        return BriefingDetailScreen(period: period, initialTab: tab);
      },
    ),

    // 기사 상세
    GoRoute(
      path: '/article/:id',
      builder: (context, state) => ArticleDetailScreen(
        articleId: state.pathParameters['id']!,
      ),
    ),

    // 카테고리 설정 (설정에서)
    GoRoute(
      path: '/categories/edit',
      builder: (context, state) => const CategoryScreen(),
    ),

    // 구독
    GoRoute(
      path: '/subscription',
      builder: (context, state) => const SubscriptionScreen(),
    ),

    // 고객지원
    GoRoute(
      path: '/faq',
      builder: (context, state) => const FaqScreen(),
    ),
    GoRoute(
      path: '/terms',
      builder: (context, state) => const TermsScreen(),
    ),
    GoRoute(
      path: '/privacy',
      builder: (context, state) => const PrivacyScreen(),
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
      theme: AppTheme.darkTheme,
      routerConfig: _router,
    );
  }
}

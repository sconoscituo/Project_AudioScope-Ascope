import 'dart:math';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/auth/auth_service.dart';
import '../../core/theme/app_theme.dart';

/// 스플래시 화면. Scope 빨려들어가는 애니메이션 + 태그라인.
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with TickerProviderStateMixin {
  late final AnimationController _scopeController;
  late final AnimationController _textController;
  late final AnimationController _pulseController;
  late final Animation<double> _scopeScale;
  late final Animation<double> _scopeRotation;
  late final Animation<double> _textOpacity;
  late final Animation<double> _taglineSlide;

  @override
  void initState() {
    super.initState();

    // Scope 줌인 + 회전 (빨려들어가는 느낌)
    _scopeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    );
    _scopeScale = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _scopeController, curve: Curves.easeOutBack),
    );
    _scopeRotation = Tween<double>(begin: -0.5, end: 0.0).animate(
      CurvedAnimation(parent: _scopeController, curve: Curves.easeOutCubic),
    );

    // 펄스 애니메이션
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);

    // 태그라인 텍스트
    _textController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _textOpacity = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _textController, curve: Curves.easeIn),
    );
    _taglineSlide = Tween<double>(begin: 30.0, end: 0.0).animate(
      CurvedAnimation(parent: _textController, curve: Curves.easeOutCubic),
    );

    _startAnimation();
  }

  Future<void> _startAnimation() async {
    await Future.delayed(const Duration(milliseconds: 300));
    _scopeController.forward();
    await Future.delayed(const Duration(milliseconds: 1200));
    _textController.forward();
    await Future.delayed(const Duration(milliseconds: 2000));

    if (!mounted) return;
    final isAuth = await AuthService.instance.isAuthenticated();
    if (!mounted) return;
    context.go(isAuth ? '/home' : '/onboarding');
  }

  @override
  void dispose() {
    _scopeController.dispose();
    _textController.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primary,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // 로고 + Scope 애니메이션
            AnimatedBuilder(
              animation: Listenable.merge([_scopeController, _pulseController]),
              builder: (context, child) {
                final pulse = 1.0 + (_pulseController.value * 0.05);
                return Transform.scale(
                  scale: _scopeScale.value * pulse,
                  child: Transform.rotate(
                    angle: _scopeRotation.value * pi,
                    child: child,
                  ),
                );
              },
              child: _buildLogo(),
            ),

            const SizedBox(height: 32),

            // 앱 이름
            AnimatedBuilder(
              animation: _scopeController,
              builder: (context, child) {
                return Opacity(
                  opacity: _scopeScale.value.clamp(0.0, 1.0),
                  child: child,
                );
              },
              child: const Text(
                'AudioScope',
                style: TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                  letterSpacing: 2,
                ),
              ),
            ),

            const SizedBox(height: 16),

            // 태그라인
            AnimatedBuilder(
              animation: _textController,
              builder: (context, _) {
                return Transform.translate(
                  offset: Offset(0, _taglineSlide.value),
                  child: Opacity(
                    opacity: _textOpacity.value,
                    child: const Text(
                      '5분 안에 귀에 꽂아드리는\n전 세계 주요 시사',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w400,
                        color: AppColors.textSecondary,
                        height: 1.6,
                      ),
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLogo() {
    return Container(
      width: 120,
      height: 120,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: const RadialGradient(
          colors: [AppColors.accentGlow, AppColors.accent, AppColors.primaryLight],
          stops: [0.0, 0.5, 1.0],
        ),
        boxShadow: [
          BoxShadow(
            color: AppColors.accent.withOpacity(0.3),
            blurRadius: 40,
            spreadRadius: 10,
          ),
        ],
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          // 지구본 느낌의 원형 라인
          ...List.generate(3, (i) {
            return Transform.rotate(
              angle: (i * pi / 3),
              child: Container(
                width: 80 + (i * 10),
                height: 80 + (i * 10),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: Colors.white.withOpacity(0.15 - (i * 0.03)),
                    width: 1,
                  ),
                ),
              ),
            );
          }),
          // 헤드셋 아이콘
          const Icon(
            Icons.headphones_rounded,
            size: 48,
            color: Colors.white,
          ),
        ],
      ),
    );
  }
}

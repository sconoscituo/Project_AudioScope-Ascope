import 'dart:math';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/auth/auth_service.dart';
import '../../core/theme/app_theme.dart';

/// Splash: 오디오 파형 애니메이션으로 로고 등장.
/// 파형이 좌→우로 펼쳐지며 로고 등장 → 1.5초 후 홈으로 전환.
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with TickerProviderStateMixin {
  late final AnimationController _waveController;
  late final AnimationController _logoController;
  late final AnimationController _pulseController;
  late final AnimationController _textController;

  late final Animation<double> _logoOpacity;
  late final Animation<double> _logoScale;
  late final Animation<double> _textOpacity;
  late final Animation<Offset> _textSlide;

  @override
  void initState() {
    super.initState();

    // 파형 루프 애니메이션
    _waveController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    );

    // 로고 등장
    _logoController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 550),
    );
    _logoOpacity = CurvedAnimation(parent: _logoController, curve: Curves.easeOut);
    _logoScale = Tween<double>(begin: 0.6, end: 1.0).animate(
      CurvedAnimation(parent: _logoController, curve: Curves.easeOutBack),
    );

    // 미세 펄스
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    );

    // 텍스트 슬라이드업
    _textController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 450),
    );
    _textOpacity = CurvedAnimation(parent: _textController, curve: Curves.easeOut);
    _textSlide = Tween<Offset>(
      begin: const Offset(0, 0.4),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _textController, curve: Curves.easeOutCubic));

    _startSequence();
  }

  Future<void> _startSequence() async {
    // 파형 먼저 시작
    await Future.delayed(const Duration(milliseconds: 150));
    _waveController.repeat();

    // 로고 등장
    await Future.delayed(const Duration(milliseconds: 300));
    _logoController.forward();

    // 텍스트 등장
    await Future.delayed(const Duration(milliseconds: 200));
    _textController.forward();
    _pulseController.repeat(reverse: true);

    // 1.5초 후 라우팅
    await Future.delayed(const Duration(milliseconds: 1500));
    if (!mounted) return;
    final isAuth = await AuthService.instance.isAuthenticated();
    if (!mounted) return;
    context.go(isAuth ? '/home' : '/onboarding');
  }

  @override
  void dispose() {
    _waveController.dispose();
    _logoController.dispose();
    _pulseController.dispose();
    _textController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;

    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Color(0xFF050505),
              Color(0xFF0D1A16),
              Color(0xFF050505),
            ],
            stops: [0.0, 0.5, 1.0],
          ),
        ),
        child: Stack(
          children: [
            // 하단 파형 배경 (넓게)
            Positioned(
              bottom: size.height * 0.12,
              left: 0,
              right: 0,
              child: AnimatedBuilder(
                animation: _waveController,
                builder: (context, _) {
                  return CustomPaint(
                    size: Size(size.width, 90),
                    painter: _SplashWavePainter(
                      progress: _waveController.value,
                      opacity: _logoOpacity.value * 0.35,
                    ),
                  );
                },
              ),
            ),

            // 상단 파형 배경 (반전)
            Positioned(
              top: size.height * 0.12,
              left: 0,
              right: 0,
              child: AnimatedBuilder(
                animation: _waveController,
                builder: (context, _) {
                  return CustomPaint(
                    size: Size(size.width, 90),
                    painter: _SplashWavePainter(
                      progress: _waveController.value,
                      opacity: _logoOpacity.value * 0.2,
                      phaseOffset: pi,
                      flipped: true,
                    ),
                  );
                },
              ),
            ),

            // 중앙: 로고 + 텍스트
            Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // 로고 아이콘
                  AnimatedBuilder(
                    animation: Listenable.merge([_logoController, _pulseController]),
                    builder: (context, _) {
                      final pulse = 1.0 + (_pulseController.value * 0.025);
                      return Opacity(
                        opacity: _logoOpacity.value,
                        child: Transform.scale(
                          scale: _logoScale.value * pulse,
                          child: _buildLogo(),
                        ),
                      );
                    },
                  ),

                  const SizedBox(height: 32),

                  // 텍스트
                  FadeTransition(
                    opacity: _textOpacity,
                    child: SlideTransition(
                      position: _textSlide,
                      child: Column(
                        children: [
                          const Text(
                            'AudioScope',
                            style: TextStyle(
                              fontSize: 32,
                              fontWeight: FontWeight.w700,
                              color: AppColors.textPrimary,
                              letterSpacing: 2.5,
                            ),
                          ),
                          const SizedBox(height: 10),
                          Text(
                            'AI 뉴스 오디오 브리핑',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w400,
                              color: AppColors.accent.withOpacity(0.75),
                              letterSpacing: 1.5,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // 하단 로딩 인디케이터 (점 3개)
            Positioned(
              bottom: 60,
              left: 0,
              right: 0,
              child: AnimatedBuilder(
                animation: _pulseController,
                builder: (context, _) {
                  return Opacity(
                    opacity: _logoOpacity.value,
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: List.generate(3, (i) {
                        final phase = (i / 3) * pi;
                        final scale = 0.6 + 0.4 * sin(_pulseController.value * pi + phase).abs();
                        return Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 4),
                          child: Transform.scale(
                            scale: scale,
                            child: Container(
                              width: 5,
                              height: 5,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: AppColors.accent.withOpacity(0.5 + 0.5 * scale),
                              ),
                            ),
                          ),
                        );
                      }),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLogo() {
    return SizedBox(
      width: 96,
      height: 96,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // 외부 글로우 링
          Container(
            width: 96,
            height: 96,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(
                color: AppColors.accent.withOpacity(0.3),
                width: 1.5,
              ),
              boxShadow: [
                BoxShadow(
                  color: AppColors.accent.withOpacity(0.18),
                  blurRadius: 28,
                  spreadRadius: 4,
                ),
              ],
            ),
          ),
          // 내부 원형 배경
          Container(
            width: 68,
            height: 68,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.accent.withOpacity(0.07),
              border: Border.all(
                color: AppColors.accent.withOpacity(0.18),
                width: 1,
              ),
            ),
          ),
          // 헤드폰 아이콘
          const Icon(
            Icons.headphones_rounded,
            size: 34,
            color: AppColors.accent,
          ),
        ],
      ),
    );
  }
}

/// 스플래시용 파형 페인터.
class _SplashWavePainter extends CustomPainter {
  final double progress;
  final double opacity;
  final double phaseOffset;
  final bool flipped;

  _SplashWavePainter({
    required this.progress,
    required this.opacity,
    this.phaseOffset = 0,
    this.flipped = false,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (opacity <= 0) return;

    const barCount = 36;
    final barWidth = (size.width / barCount) * 0.5;
    final gap = (size.width - barWidth * barCount) / (barCount + 1);

    final paint = Paint()..strokeCap = StrokeCap.round;

    for (int i = 0; i < barCount; i++) {
      final x = gap + i * (barWidth + gap) + barWidth / 2;
      final phase = (i / barCount) * 2 * pi + phaseOffset;
      final wave = sin(progress * 2 * pi + phase);
      final heightFraction = 0.2 + 0.6 * ((wave + 1) / 2);
      final barHeight = size.height * heightFraction;

      final top = flipped ? 0.0 : size.height - barHeight;

      paint.color = AppColors.accent.withOpacity(opacity * (0.4 + 0.6 * heightFraction));

      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(x - barWidth / 2, top, barWidth, barHeight),
          const Radius.circular(2),
        ),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _SplashWavePainter old) =>
      old.progress != progress || old.opacity != opacity;
}

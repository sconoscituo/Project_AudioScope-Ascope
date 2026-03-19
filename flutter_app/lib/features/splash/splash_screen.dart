import 'dart:math';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/auth/auth_service.dart';
import '../../core/theme/app_theme.dart';

/// Splash: 풀스크린 Radar Sweep 애니메이션.
/// 레이더가 360도 스캔 → "Signal Found" → 로고 등장 → 라우팅.
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with TickerProviderStateMixin {
  late final AnimationController _sweepController;
  late final AnimationController _revealController;
  late final AnimationController _pulseController;
  late final Animation<double> _sweepAngle;
  late final Animation<double> _revealOpacity;
  late final Animation<double> _revealScale;
  late final Animation<double> _gridOpacity;

  @override
  void initState() {
    super.initState();

    // 레이더 스윕 회전 (1.6초에 1바퀴)
    _sweepController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1600),
    );
    _sweepAngle = Tween<double>(begin: 0, end: 2 * pi).animate(
      CurvedAnimation(parent: _sweepController, curve: Curves.easeInOut),
    );

    // 로고 등장
    _revealController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _revealOpacity = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _revealController, curve: Curves.easeOut),
    );
    _revealScale = Tween<double>(begin: 0.5, end: 1.0).animate(
      CurvedAnimation(parent: _revealController, curve: Curves.easeOutBack),
    );
    _gridOpacity = Tween<double>(begin: 0, end: 0.3).animate(
      CurvedAnimation(parent: _sweepController, curve: Curves.easeIn),
    );

    // 펄스
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );

    _startSequence();
  }

  Future<void> _startSequence() async {
    await Future.delayed(const Duration(milliseconds: 200));
    // 레이더 스윕
    _sweepController.forward();
    await Future.delayed(const Duration(milliseconds: 1700));
    // 로고 등장 + 펄스
    _revealController.forward();
    _pulseController.repeat(reverse: true);
    await Future.delayed(const Duration(milliseconds: 900));
    // 라우팅
    if (!mounted) return;
    final isAuth = await AuthService.instance.isAuthenticated();
    if (!mounted) return;
    context.go(isAuth ? '/home' : '/onboarding');
  }

  @override
  void dispose() {
    _sweepController.dispose();
    _revealController.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final maxRadius = size.longestSide * 0.7;

    return Scaffold(
      backgroundColor: AppColors.primary,
      body: Stack(
        children: [
          // 배경 격자 라인 (스캔 후 나타남)
          AnimatedBuilder(
            animation: _sweepController,
            builder: (context, _) {
              return Opacity(
                opacity: _gridOpacity.value,
                child: CustomPaint(
                  size: size,
                  painter: _GridPainter(),
                ),
              );
            },
          ),

          // 동심원 레이더 링
          Center(
            child: AnimatedBuilder(
              animation: _sweepController,
              builder: (context, _) {
                return CustomPaint(
                  size: Size(maxRadius * 2, maxRadius * 2),
                  painter: _RadarPainter(
                    sweepAngle: _sweepAngle.value,
                    progress: _sweepController.value,
                    maxRadius: maxRadius,
                  ),
                );
              },
            ),
          ),

          // 중앙 로고 + 텍스트
          Center(
            child: AnimatedBuilder(
              animation: Listenable.merge([_revealController, _pulseController]),
              builder: (context, _) {
                final pulse = 1.0 + (_pulseController.value * 0.03);
                return Opacity(
                  opacity: _revealOpacity.value,
                  child: Transform.scale(
                    scale: _revealScale.value * pulse,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // 로고 — 스코프 십자선 + 헤드셋
                        _buildScopeLogo(),
                        const SizedBox(height: 28),
                        const Text(
                          'AudioScope',
                          style: TextStyle(
                            fontSize: 34,
                            fontWeight: FontWeight.w700,
                            color: AppColors.textPrimary,
                            letterSpacing: 3,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          'SIGNAL ACQUIRED',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: AppColors.accent.withOpacity(0.8),
                            letterSpacing: 4,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildScopeLogo() {
    return SizedBox(
      width: 100,
      height: 100,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // 외부 글로우 링
          Container(
            width: 100,
            height: 100,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: AppColors.accent.withOpacity(0.4), width: 2),
              boxShadow: [
                BoxShadow(
                  color: AppColors.accent.withOpacity(0.2),
                  blurRadius: 30,
                  spreadRadius: 5,
                ),
              ],
            ),
          ),
          // 내부 링
          Container(
            width: 70,
            height: 70,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: AppColors.accent.withOpacity(0.25), width: 1),
            ),
          ),
          // 십자선
          Container(
            width: 100,
            height: 1,
            color: AppColors.accent.withOpacity(0.3),
          ),
          Container(
            width: 1,
            height: 100,
            color: AppColors.accent.withOpacity(0.3),
          ),
          // 헤드셋 아이콘
          const Icon(
            Icons.headphones_rounded,
            size: 36,
            color: AppColors.accent,
          ),
        ],
      ),
    );
  }
}

/// 레이더 스윕 + 동심원 페인터.
class _RadarPainter extends CustomPainter {
  final double sweepAngle;
  final double progress;
  final double maxRadius;

  _RadarPainter({
    required this.sweepAngle,
    required this.progress,
    required this.maxRadius,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);

    // 동심원 (레이더 스캔이 진행될수록 나타남)
    for (int i = 1; i <= 4; i++) {
      final r = maxRadius * i / 4;
      final ringOpacity = (progress * 4 - i + 1).clamp(0.0, 1.0) * 0.15;
      canvas.drawCircle(
        center,
        r,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1
          ..color = AppColors.accent.withOpacity(ringOpacity),
      );
    }

    // 스윕 빔 (부채꼴 그라데이션)
    if (progress < 1.0) {
      final sweepPaint = Paint()
        ..shader = SweepGradient(
          startAngle: sweepAngle - 0.5,
          endAngle: sweepAngle,
          colors: [
            Colors.transparent,
            AppColors.accent.withOpacity(0.0),
            AppColors.accent.withOpacity(0.25),
          ],
          stops: const [0.0, 0.3, 1.0],
          transform: GradientRotation(sweepAngle - 0.5),
        ).createShader(Rect.fromCircle(center: center, radius: maxRadius));

      canvas.drawCircle(center, maxRadius, sweepPaint);

      // 스윕 라인
      final lineEnd = Offset(
        center.dx + maxRadius * cos(sweepAngle - pi / 2),
        center.dy + maxRadius * sin(sweepAngle - pi / 2),
      );
      canvas.drawLine(
        center,
        lineEnd,
        Paint()
          ..color = AppColors.accent.withOpacity(0.6)
          ..strokeWidth = 1.5,
      );
    }

    // 스캔 도트 (스윕 팁에 밝은 점)
    if (progress < 1.0) {
      for (int i = 0; i < 3; i++) {
        final dotAngle = sweepAngle - pi / 2 - (i * 0.15);
        final dotR = maxRadius * (0.3 + (i * 0.25));
        final dotPos = Offset(
          center.dx + dotR * cos(dotAngle),
          center.dy + dotR * sin(dotAngle),
        );
        canvas.drawCircle(
          dotPos,
          3 - i.toDouble(),
          Paint()..color = AppColors.accent.withOpacity(0.8 - (i * 0.2)),
        );
      }
    }
  }

  @override
  bool shouldRepaint(covariant _RadarPainter oldDelegate) =>
      oldDelegate.sweepAngle != sweepAngle || oldDelegate.progress != progress;
}

/// 배경 격자 페인터.
class _GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppColors.accent.withOpacity(0.06)
      ..strokeWidth = 0.5;

    const spacing = 40.0;

    for (double x = 0; x < size.width; x += spacing) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (double y = 0; y < size.height; y += spacing) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

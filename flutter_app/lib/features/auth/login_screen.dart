import 'dart:io';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/auth/auth_service.dart';
import '../../core/theme/app_theme.dart';

/// 로그인 화면. Scope Tunnel 풀스크린 애니메이션.
/// 동심원 링이 바깥에서 중앙으로 수축 → 콘텐츠 fade in.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with TickerProviderStateMixin {
  bool _isLoading = false;

  late final AnimationController _tunnelController;
  late final AnimationController _contentController;
  late final Animation<double> _tunnelProgress;
  late final Animation<double> _contentOpacity;
  late final Animation<double> _contentSlide;

  @override
  void initState() {
    super.initState();

    // 터널 수축 (1.2초)
    _tunnelController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
    _tunnelProgress = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _tunnelController, curve: Curves.easeInOutCubic),
    );

    // 콘텐츠 등장 (800ms, 터널 끝나고)
    _contentController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _contentOpacity = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _contentController, curve: Curves.easeOut),
    );
    _contentSlide = Tween<double>(begin: 40, end: 0).animate(
      CurvedAnimation(parent: _contentController, curve: Curves.easeOutCubic),
    );

    _startAnimation();
  }

  Future<void> _startAnimation() async {
    await Future.delayed(const Duration(milliseconds: 100));
    _tunnelController.forward();
    await Future.delayed(const Duration(milliseconds: 900));
    _contentController.forward();
  }

  @override
  void dispose() {
    _tunnelController.dispose();
    _contentController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin(Future<Map<String, dynamic>?> Function() loginFn) async {
    setState(() => _isLoading = true);
    try {
      final result = await loginFn();
      if (result != null && mounted) {
        final isNew = result['is_new_user'] == true;
        context.go(isNew ? '/categories' : '/home');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('로그인 실패: ${e.toString().split(']').last.trim()}'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;

    return Scaffold(
      backgroundColor: AppColors.primary,
      body: Stack(
        children: [
          // 풀스크린 Scope Tunnel 애니메이션
          AnimatedBuilder(
            animation: _tunnelController,
            builder: (context, _) {
              return CustomPaint(
                size: size,
                painter: _ScopeTunnelPainter(
                  progress: _tunnelProgress.value,
                ),
              );
            },
          ),

          // 콘텐츠
          SafeArea(
            child: AnimatedBuilder(
              animation: _contentController,
              builder: (context, child) {
                return Opacity(
                  opacity: _contentOpacity.value,
                  child: Transform.translate(
                    offset: Offset(0, _contentSlide.value),
                    child: child,
                  ),
                );
              },
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 32),
                child: Column(
                  children: [
                    const Spacer(flex: 3),

                    // 로고
                    _buildScopeLogo(),
                    const SizedBox(height: 24),

                    // 앱 이름
                    const Text(
                      'AudioScope',
                      style: TextStyle(
                        fontSize: 30,
                        fontWeight: FontWeight.w700,
                        color: AppColors.textPrimary,
                        letterSpacing: 2,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '귀로 살피는 세계',
                      style: TextStyle(
                        fontSize: 15,
                        color: AppColors.accent.withOpacity(0.7),
                        fontWeight: FontWeight.w400,
                        letterSpacing: 1,
                      ),
                    ),

                    const Spacer(flex: 3),

                    // 소셜 로그인 버튼
                    if (_isLoading)
                      const CircularProgressIndicator(color: AppColors.accent)
                    else ...[
                      _SocialButton(
                        label: 'Google로 계속하기',
                        icon: Icons.g_mobiledata_rounded,
                        backgroundColor: Colors.white,
                        textColor: Colors.black87,
                        onPressed: () => _handleLogin(AuthService.instance.signInWithGoogle),
                      ),
                      const SizedBox(height: 12),
                      _SocialButton(
                        label: 'Kakao로 계속하기',
                        icon: Icons.chat_bubble_rounded,
                        backgroundColor: const Color(0xFFFEE500),
                        textColor: const Color(0xFF191919),
                        onPressed: () => _handleLogin(AuthService.instance.signInWithKakao),
                      ),
                      const SizedBox(height: 12),
                      if (Platform.isIOS) ...[
                        _SocialButton(
                          label: 'Apple로 계속하기',
                          icon: Icons.apple_rounded,
                          backgroundColor: Colors.white,
                          textColor: Colors.black,
                          onPressed: () => _handleLogin(AuthService.instance.signInWithApple),
                        ),
                        const SizedBox(height: 12),
                      ],
                    ],

                    const Spacer(),

                    Padding(
                      padding: const EdgeInsets.only(bottom: 20),
                      child: Text(
                        '로그인 시 서비스 이용약관 및\n개인정보 처리방침에 동의합니다.',
                        style: TextStyle(
                          fontSize: 12,
                          color: AppColors.textTertiary,
                          height: 1.5,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildScopeLogo() {
    return SizedBox(
      width: 80,
      height: 80,
      child: Stack(
        alignment: Alignment.center,
        children: [
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: AppColors.accent.withOpacity(0.5), width: 1.5),
              boxShadow: [
                BoxShadow(
                  color: AppColors.accent.withOpacity(0.15),
                  blurRadius: 25,
                  spreadRadius: 3,
                ),
              ],
            ),
          ),
          Container(
            width: 55,
            height: 55,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: AppColors.accent.withOpacity(0.2), width: 1),
            ),
          ),
          Container(width: 80, height: 0.5, color: AppColors.accent.withOpacity(0.2)),
          Container(width: 0.5, height: 80, color: AppColors.accent.withOpacity(0.2)),
          const Icon(Icons.headphones_rounded, size: 30, color: AppColors.accent),
        ],
      ),
    );
  }
}

/// Scope Tunnel: 동심원이 바깥에서 중앙으로 수축하는 페인터.
class _ScopeTunnelPainter extends CustomPainter {
  final double progress;

  _ScopeTunnelPainter({required this.progress});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final maxR = size.longestSide * 0.8;
    const ringCount = 8;

    for (int i = 0; i < ringCount; i++) {
      // 각 링이 시간차로 수축
      final delay = i * 0.08;
      final ringProgress = ((progress - delay) / (1 - delay)).clamp(0.0, 1.0);

      // 큰 원에서 작은 원으로 수축
      final startR = maxR * (1 - i * 0.08);
      final endR = 30.0 + i * 8;
      final r = startR + (endR - startR) * Curves.easeInCubic.transform(ringProgress);

      // 수축할수록 밝아짐
      final opacity = (0.05 + ringProgress * 0.15).clamp(0.0, 0.25);

      canvas.drawCircle(
        center,
        r,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.0 + ringProgress * 0.5
          ..color = AppColors.accent.withOpacity(opacity),
      );
    }

    // 중앙 글로우 (수축 완료 시)
    if (progress > 0.7) {
      final glowOpacity = ((progress - 0.7) / 0.3).clamp(0.0, 1.0) * 0.1;
      canvas.drawCircle(
        center,
        60,
        Paint()
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 40)
          ..color = AppColors.accent.withOpacity(glowOpacity),
      );
    }

    // 미세한 십자선 (풀스크린)
    final crossOpacity = (progress * 0.15).clamp(0.0, 0.1);
    final crossPaint = Paint()
      ..color = AppColors.accent.withOpacity(crossOpacity)
      ..strokeWidth = 0.5;
    canvas.drawLine(
      Offset(0, center.dy),
      Offset(size.width, center.dy),
      crossPaint,
    );
    canvas.drawLine(
      Offset(center.dx, 0),
      Offset(center.dx, size.height),
      crossPaint,
    );
  }

  @override
  bool shouldRepaint(covariant _ScopeTunnelPainter oldDelegate) =>
      oldDelegate.progress != progress;
}

class _SocialButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color backgroundColor;
  final Color textColor;
  final VoidCallback onPressed;

  const _SocialButton({
    required this.label,
    required this.icon,
    required this.backgroundColor,
    required this.textColor,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 54,
      child: ElevatedButton(
        style: ElevatedButton.styleFrom(
          backgroundColor: backgroundColor,
          foregroundColor: textColor,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
        ),
        onPressed: onPressed,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 24, color: textColor),
            const SizedBox(width: 10),
            Text(
              label,
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w600,
                color: textColor,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

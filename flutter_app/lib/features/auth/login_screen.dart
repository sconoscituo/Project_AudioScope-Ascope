import 'dart:io';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/auth/auth_service.dart';
import '../../core/theme/app_theme.dart';

/// 로그인 화면. 소셜 로그인(Google, Apple, Kakao).
/// 심플하면서 세련된 다크 테마 디자인.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  bool _isLoading = false;
  late final AnimationController _fadeController;
  late final Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    )..forward();
    _fadeAnimation = CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeInOut,
    );
  }

  @override
  void dispose() {
    _fadeController.dispose();
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
    return Scaffold(
      backgroundColor: AppColors.primary,
      body: SafeArea(
        child: FadeTransition(
          opacity: _fadeAnimation,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 32),
            child: Column(
              children: [
                const Spacer(flex: 3),

                // 로고
                _buildLogo(),
                const SizedBox(height: 24),

                // 앱 이름
                const Text(
                  'AudioScope',
                  style: TextStyle(
                    fontSize: 30,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                    letterSpacing: 1.5,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  '귀로 살피는 세계',
                  style: TextStyle(
                    fontSize: 15,
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w400,
                  ),
                ),

                const Spacer(flex: 3),

                // 소셜 로그인 버튼
                if (_isLoading)
                  const CircularProgressIndicator(color: AppColors.accent)
                else ...[
                  // Google
                  _SocialButton(
                    label: 'Google로 계속하기',
                    icon: Icons.g_mobiledata_rounded,
                    backgroundColor: Colors.white,
                    textColor: Colors.black87,
                    onPressed: () => _handleLogin(AuthService.instance.signInWithGoogle),
                  ),
                  const SizedBox(height: 12),

                  // Kakao
                  _SocialButton(
                    label: 'Kakao로 계속하기',
                    icon: Icons.chat_bubble_rounded,
                    backgroundColor: const Color(0xFFFEE500),
                    textColor: const Color(0xFF191919),
                    onPressed: () => _handleLogin(AuthService.instance.signInWithKakao),
                  ),
                  const SizedBox(height: 12),

                  // Apple (iOS only)
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

                // 약관
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
    );
  }

  Widget _buildLogo() {
    return Container(
      width: 90,
      height: 90,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: const RadialGradient(
          colors: [AppColors.accentGlow, AppColors.accent],
        ),
        boxShadow: [
          BoxShadow(
            color: AppColors.accent.withOpacity(0.25),
            blurRadius: 30,
            spreadRadius: 5,
          ),
        ],
      ),
      child: const Icon(
        Icons.headphones_rounded,
        size: 42,
        color: Colors.white,
      ),
    );
  }
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

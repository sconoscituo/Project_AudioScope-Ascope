import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/auth/auth_service.dart';

/// 로그인 화면.
/// 구글, 애플 소셜 로그인을 제공합니다.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool _isLoading = false;

  /// 소셜 로그인을 처리합니다.
  ///
  /// Args:
  ///   loginFn - 로그인 함수 (Google 또는 Apple)
  Future<void> _handleLogin(Future<String?> Function() loginFn) async {
    setState(() => _isLoading = true);
    try {
      final token = await loginFn();
      if (token != null && mounted) {
        context.go('/briefing');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('로그인 실패: $e'),
            backgroundColor: Theme.of(context).colorScheme.error,
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
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Spacer(flex: 2),

              // 로고 영역
              Column(
                children: [
                  Container(
                    width: 80,
                    height: 80,
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primary,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Icon(
                      Icons.headphones,
                      size: 44,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 20),
                  Text(
                    'AudioScope',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'AI가 읽어주는 오늘의 뉴스',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          color: Theme.of(context).colorScheme.outline,
                        ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),

              const Spacer(flex: 2),

              // 로그인 버튼들
              if (_isLoading)
                const Center(child: CircularProgressIndicator())
              else ...[
                // Google 로그인
                _SocialLoginButton(
                  label: 'Google로 계속하기',
                  icon: Icons.g_mobiledata,
                  backgroundColor: Colors.white,
                  textColor: Colors.black87,
                  borderColor: Colors.grey.shade300,
                  onPressed: () => _handleLogin(
                    AuthService.instance.signInWithGoogle,
                  ),
                ),
                const SizedBox(height: 12),

                // Apple 로그인
                _SocialLoginButton(
                  label: 'Apple로 계속하기',
                  icon: Icons.apple,
                  backgroundColor: Colors.black,
                  textColor: Colors.white,
                  onPressed: () => _handleLogin(
                    AuthService.instance.signInWithApple,
                  ),
                ),
              ],

              const Spacer(),

              // 하단 약관 안내
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Text(
                  '로그인 시 서비스 이용약관 및 개인정보 처리방침에 동의합니다.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.outline,
                      ),
                  textAlign: TextAlign.center,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// 소셜 로그인 버튼 위젯.
class _SocialLoginButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color backgroundColor;
  final Color textColor;
  final Color? borderColor;
  final VoidCallback onPressed;

  const _SocialLoginButton({
    required this.label,
    required this.icon,
    required this.backgroundColor,
    required this.textColor,
    required this.onPressed,
    this.borderColor,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 52,
      child: ElevatedButton(
        style: ElevatedButton.styleFrom(
          backgroundColor: backgroundColor,
          foregroundColor: textColor,
          elevation: 1,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: borderColor != null
                ? BorderSide(color: borderColor!)
                : BorderSide.none,
          ),
        ),
        onPressed: onPressed,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 22),
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

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// AudioScope 브랜드 컬러 및 테마 시스템.
/// 다크 모드 기본, 뉴스 + 오디오 = 프리미엄 느낌.
class AppColors {
  AppColors._();

  // Primary - Deep Navy + Electric Blue
  static const primary = Color(0xFF0A1628);
  static const primaryLight = Color(0xFF1A2D4A);
  static const accent = Color(0xFF3B82F6);
  static const accentLight = Color(0xFF60A5FA);
  static const accentGlow = Color(0xFF2563EB);

  // Surface
  static const surface = Color(0xFF0F1923);
  static const surfaceLight = Color(0xFF162231);
  static const surfaceCard = Color(0xFF1A2D42);
  static const surfaceElevated = Color(0xFF1E3348);

  // Text
  static const textPrimary = Color(0xFFF1F5F9);
  static const textSecondary = Color(0xFF94A3B8);
  static const textTertiary = Color(0xFF64748B);

  // Status
  static const success = Color(0xFF10B981);
  static const warning = Color(0xFFF59E0B);
  static const error = Color(0xFFEF4444);

  // Premium
  static const premiumGold = Color(0xFFD4A853);
  static const premiumGradientStart = Color(0xFF1E3A5F);
  static const premiumGradientEnd = Color(0xFF0A1628);

  // Category chips
  static const categoryPolitics = Color(0xFF6366F1);
  static const categoryEconomy = Color(0xFF10B981);
  static const categoryWorld = Color(0xFF3B82F6);
  static const categoryTech = Color(0xFF8B5CF6);
  static const categorySociety = Color(0xFFF59E0B);
  static const categoryScience = Color(0xFF14B8A6);

  static Color categoryColor(String category) {
    return switch (category) {
      'politics' => categoryPolitics,
      'economy' => categoryEconomy,
      'world' => categoryWorld,
      'tech' => categoryTech,
      'society' => categorySociety,
      'science' => categoryScience,
      _ => accentLight,
    };
  }
}

class AppTheme {
  AppTheme._();

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      fontFamily: 'Pretendard',
      scaffoldBackgroundColor: AppColors.primary,
      colorScheme: const ColorScheme.dark(
        primary: AppColors.accent,
        onPrimary: Colors.white,
        secondary: AppColors.accentLight,
        surface: AppColors.surface,
        onSurface: AppColors.textPrimary,
        error: AppColors.error,
        outline: AppColors.textTertiary,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        systemOverlayStyle: SystemUiOverlayStyle.light,
        titleTextStyle: TextStyle(
          fontFamily: 'Pretendard',
          fontSize: 20,
          fontWeight: FontWeight.w700,
          color: AppColors.textPrimary,
        ),
        iconTheme: IconThemeData(color: AppColors.textPrimary),
      ),
      cardTheme: CardTheme(
        color: AppColors.surfaceCard,
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        margin: EdgeInsets.zero,
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AppColors.surface,
        selectedItemColor: AppColors.accent,
        unselectedItemColor: AppColors.textTertiary,
        type: BottomNavigationBarType.fixed,
        elevation: 0,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.accent,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: const TextStyle(
            fontFamily: 'Pretendard',
            fontSize: 15,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.accent,
          side: const BorderSide(color: AppColors.accent, width: 1.5),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      textTheme: const TextTheme(
        headlineLarge: TextStyle(fontSize: 28, fontWeight: FontWeight.w700, color: AppColors.textPrimary, height: 1.3),
        headlineMedium: TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: AppColors.textPrimary, height: 1.3),
        headlineSmall: TextStyle(fontSize: 20, fontWeight: FontWeight.w600, color: AppColors.textPrimary, height: 1.3),
        titleLarge: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
        titleMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
        titleSmall: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
        bodyLarge: TextStyle(fontSize: 16, fontWeight: FontWeight.w400, color: AppColors.textPrimary, height: 1.6),
        bodyMedium: TextStyle(fontSize: 14, fontWeight: FontWeight.w400, color: AppColors.textSecondary, height: 1.5),
        bodySmall: TextStyle(fontSize: 12, fontWeight: FontWeight.w400, color: AppColors.textTertiary, height: 1.4),
        labelLarge: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.accent),
        labelMedium: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: AppColors.textSecondary),
        labelSmall: TextStyle(fontSize: 10, fontWeight: FontWeight.w500, color: AppColors.textTertiary),
      ),
      dividerTheme: const DividerThemeData(
        color: AppColors.surfaceLight,
        thickness: 1,
        space: 1,
      ),
      chipTheme: ChipThemeData(
        backgroundColor: AppColors.surfaceLight,
        selectedColor: AppColors.accent.withOpacity(0.2),
        labelStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        side: BorderSide.none,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: AppColors.surfaceElevated,
        contentTextStyle: const TextStyle(color: AppColors.textPrimary, fontSize: 14),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}

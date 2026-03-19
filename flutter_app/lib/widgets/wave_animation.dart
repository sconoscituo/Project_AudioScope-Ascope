import 'dart:math';
import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';

/// 오디오 파형 시각화 위젯.
/// 재생 중: AnimationController로 각 바가 사인파 기반으로 물결침.
/// 정지 중: 모든 바가 낮은 높이의 평평한 선으로 정렬.
class WaveAnimation extends StatefulWidget {
  final bool isPlaying;
  final Color? color;
  final int barCount;
  final double height;
  final double width;

  const WaveAnimation({
    super.key,
    required this.isPlaying,
    this.color,
    this.barCount = 28,
    this.height = 40,
    this.width = double.infinity,
  });

  @override
  State<WaveAnimation> createState() => _WaveAnimationState();
}

class _WaveAnimationState extends State<WaveAnimation>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
    if (widget.isPlaying) _controller.repeat();
  }

  @override
  void didUpdateWidget(WaveAnimation oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isPlaying != oldWidget.isPlaying) {
      if (widget.isPlaying) {
        _controller.repeat();
      } else {
        _controller.animateTo(0, duration: const Duration(milliseconds: 300));
      }
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final color = widget.color ?? AppColors.accent;
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return CustomPaint(
          size: Size(widget.width == double.infinity ? double.infinity : widget.width, widget.height),
          painter: _WavePainter(
            progress: _controller.value,
            isPlaying: widget.isPlaying,
            color: color,
            barCount: widget.barCount,
          ),
        );
      },
    );
  }
}

class _WavePainter extends CustomPainter {
  final double progress;
  final bool isPlaying;
  final Color color;
  final int barCount;

  _WavePainter({
    required this.progress,
    required this.isPlaying,
    required this.color,
    required this.barCount,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeCap = StrokeCap.round;

    final barWidth = (size.width / barCount) * 0.55;
    final gap = (size.width - barWidth * barCount) / (barCount + 1);

    for (int i = 0; i < barCount; i++) {
      final x = gap + i * (barWidth + gap) + barWidth / 2;

      double heightFraction;
      if (isPlaying) {
        // 사인파 기반: 각 바마다 위상 오프셋을 다르게 해서 물결 효과
        final phase = (i / barCount) * 2 * pi;
        final wave = sin(progress * 2 * pi + phase);
        // 기본 높이 0.25 + 진폭 0.45 → 0.25 ~ 0.7 범위
        heightFraction = 0.25 + 0.45 * ((wave + 1) / 2);
        // 중앙 바들이 더 크게 움직이도록 가중치
        final centerBias = sin(pi * i / (barCount - 1));
        heightFraction = 0.15 + (heightFraction * 0.7 + centerBias * 0.15);
      } else {
        // 정지: 아주 낮은 평평한 바
        heightFraction = 0.12;
      }

      final barHeight = size.height * heightFraction.clamp(0.08, 1.0);
      final top = (size.height - barHeight) / 2;

      paint.color = color.withOpacity(isPlaying ? (0.5 + 0.5 * heightFraction) : 0.3);

      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(x - barWidth / 2, top, barWidth, barHeight),
          const Radius.circular(3),
        ),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _WavePainter oldDelegate) =>
      oldDelegate.progress != progress ||
      oldDelegate.isPlaying != isPlaying ||
      oldDelegate.color != color;
}

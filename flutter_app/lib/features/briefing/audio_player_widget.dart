import 'package:flutter/material.dart';
import 'package:just_audio/just_audio.dart';

import '../../core/api/api_client.dart';
import '../../core/theme/app_theme.dart';

/// 프리미엄 오디오 플레이어 위젯.
/// 재생/정지, 진행바, 시간 표시, 속도 조절, 청취 기록.
class AudioPlayerWidget extends StatefulWidget {
  final String audioUrl;
  final String briefingId;

  const AudioPlayerWidget({
    super.key,
    required this.audioUrl,
    this.briefingId = '',
  });

  @override
  State<AudioPlayerWidget> createState() => _AudioPlayerWidgetState();
}

class _AudioPlayerWidgetState extends State<AudioPlayerWidget> {
  late final AudioPlayer _player;
  bool _isLoading = true;
  String? _error;
  double _speed = 1.0;

  @override
  void initState() {
    super.initState();
    _player = AudioPlayer();
    _initPlayer();
  }

  Future<void> _initPlayer() async {
    try {
      await _player.setUrl(widget.audioUrl);
      if (mounted) setState(() => _isLoading = false);

      // 재생 완료 시 청취 기록
      _player.playerStateStream.listen((state) {
        if (state.processingState == ProcessingState.completed) {
          _recordListenProgress(completed: true);
        }
      });
    } catch (e) {
      if (mounted) setState(() { _error = '오디오 로드 실패'; _isLoading = false; });
    }
  }

  Future<void> _recordListenProgress({bool completed = false}) async {
    if (widget.briefingId.isEmpty) return;
    try {
      await ApiClient().post('/api/v1/briefings/listen', data: {
        'briefing_id': widget.briefingId,
        'listened_seconds': _player.position.inSeconds,
        'completed': completed,
      });
    } catch (_) {}
  }

  @override
  void dispose() {
    _recordListenProgress();
    _player.dispose();
    super.dispose();
  }

  String _formatDuration(Duration? d) {
    if (d == null) return '--:--';
    final m = d.inMinutes.remainder(60).toString().padLeft(2, '0');
    final s = d.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$m:$s';
  }

  void _cycleSpeed() {
    final speeds = [0.75, 1.0, 1.25, 1.5, 2.0];
    final idx = speeds.indexOf(_speed);
    final next = speeds[(idx + 1) % speeds.length];
    setState(() => _speed = next);
    _player.setSpeed(next);
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Text(_error!, style: const TextStyle(color: AppColors.error, fontSize: 13));
    }
    if (_isLoading) {
      return const SizedBox(
        height: 60,
        child: Center(child: CircularProgressIndicator(color: AppColors.accent)),
      );
    }

    return StreamBuilder<PlayerState>(
      stream: _player.playerStateStream,
      builder: (context, snapshot) {
        final state = snapshot.data;
        final isPlaying = state?.playing ?? false;
        final processing = state?.processingState;

        return Column(
          children: [
            // 진행바
            StreamBuilder<Duration>(
              stream: _player.positionStream,
              builder: (context, posSnap) {
                final pos = posSnap.data ?? Duration.zero;
                final dur = _player.duration ?? Duration.zero;
                final progress = dur.inMilliseconds > 0
                    ? pos.inMilliseconds / dur.inMilliseconds
                    : 0.0;

                return Column(
                  children: [
                    SliderTheme(
                      data: SliderTheme.of(context).copyWith(
                        trackHeight: 4,
                        activeTrackColor: AppColors.accent,
                        inactiveTrackColor: AppColors.surfaceLight,
                        thumbColor: AppColors.accent,
                        thumbShape: const RoundSliderThumbShape(
                          enabledThumbRadius: 7,
                        ),
                        overlayShape: const RoundSliderOverlayShape(
                          overlayRadius: 14,
                        ),
                      ),
                      child: Slider(
                        value: progress.clamp(0.0, 1.0),
                        onChanged: (v) {
                          _player.seek(Duration(
                            milliseconds: (v * dur.inMilliseconds).round(),
                          ));
                        },
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 8),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            _formatDuration(pos),
                            style: const TextStyle(
                              fontSize: 12,
                              color: AppColors.textTertiary,
                            ),
                          ),
                          Text(
                            _formatDuration(dur),
                            style: const TextStyle(
                              fontSize: 12,
                              color: AppColors.textTertiary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                );
              },
            ),

            const SizedBox(height: 8),

            // 컨트롤
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // 속도
                GestureDetector(
                  onTap: _cycleSpeed,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceLight,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Text(
                      '${_speed}x',
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: AppColors.accent,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 16),

                // 15초 뒤로
                IconButton(
                  icon: const Icon(Icons.replay_10_rounded, color: AppColors.textSecondary),
                  iconSize: 28,
                  onPressed: () {
                    final newPos = _player.position - const Duration(seconds: 15);
                    _player.seek(newPos < Duration.zero ? Duration.zero : newPos);
                  },
                ),

                // 재생/정지
                const SizedBox(width: 8),
                GestureDetector(
                  onTap: () {
                    if (processing == ProcessingState.loading ||
                        processing == ProcessingState.buffering) return;
                    isPlaying ? _player.pause() : _player.play();
                  },
                  child: Container(
                    width: 60,
                    height: 60,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: AppColors.accent,
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.accent.withOpacity(0.3),
                          blurRadius: 16,
                          spreadRadius: 2,
                        ),
                      ],
                    ),
                    child: processing == ProcessingState.loading ||
                            processing == ProcessingState.buffering
                        ? const Padding(
                            padding: EdgeInsets.all(16),
                            child: CircularProgressIndicator(
                              strokeWidth: 2.5,
                              color: Colors.white,
                            ),
                          )
                        : Icon(
                            isPlaying
                                ? Icons.pause_rounded
                                : Icons.play_arrow_rounded,
                            color: Colors.white,
                            size: 32,
                          ),
                  ),
                ),
                const SizedBox(width: 8),

                // 15초 앞으로
                IconButton(
                  icon: const Icon(Icons.forward_10_rounded, color: AppColors.textSecondary),
                  iconSize: 28,
                  onPressed: () {
                    final dur = _player.duration;
                    if (dur == null) return;
                    final newPos = _player.position + const Duration(seconds: 15);
                    _player.seek(newPos > dur ? dur : newPos);
                  },
                ),

                const SizedBox(width: 16),

                // Share
                IconButton(
                  icon: const Icon(Icons.share_rounded, color: AppColors.textTertiary),
                  iconSize: 22,
                  onPressed: () {},
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text(
                  'Powered by ',
                  style: TextStyle(fontSize: 10, color: AppColors.textTertiary),
                ),
                Text(
                  'SUPERTONE',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textTertiary.withOpacity(0.8),
                    letterSpacing: 1.2,
                  ),
                ),
              ],
            ),
          ],
        );
      },
    );
  }
}

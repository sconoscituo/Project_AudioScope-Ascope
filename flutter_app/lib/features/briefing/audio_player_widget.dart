import 'package:flutter/material.dart';
import 'package:just_audio/just_audio.dart';

/// 오디오 플레이어 위젯.
/// 재생/정지, 진행바, 재생 시간을 표시합니다.
class AudioPlayerWidget extends StatefulWidget {
  final String audioUrl;

  const AudioPlayerWidget({super.key, required this.audioUrl});

  @override
  State<AudioPlayerWidget> createState() => _AudioPlayerWidgetState();
}

class _AudioPlayerWidgetState extends State<AudioPlayerWidget> {
  late final AudioPlayer _player;
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _player = AudioPlayer();
    _initPlayer();
  }

  /// 오디오 플레이어를 초기화하고 URL을 로드합니다.
  Future<void> _initPlayer() async {
    setState(() => _isLoading = true);
    try {
      await _player.setUrl(widget.audioUrl);
    } catch (e) {
      if (mounted) {
        setState(() => _errorMessage = '오디오 로드 실패: $e');
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  /// Duration을 mm:ss 형식 문자열로 변환합니다.
  String _formatDuration(Duration? d) {
    if (d == null) return '--:--';
    final minutes = d.inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = d.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  @override
  Widget build(BuildContext context) {
    if (_errorMessage != null) {
      return Text(_errorMessage!,
          style: TextStyle(color: Theme.of(context).colorScheme.error));
    }

    if (_isLoading) {
      return const SizedBox(
        height: 48,
        child: Center(child: CircularProgressIndicator()),
      );
    }

    return StreamBuilder<PlayerState>(
      stream: _player.playerStateStream,
      builder: (context, playerSnapshot) {
        final playerState = playerSnapshot.data;
        final isPlaying = playerState?.playing ?? false;
        final processingState = playerState?.processingState;

        return Column(
          children: [
            // 진행바
            StreamBuilder<Duration>(
              stream: _player.positionStream,
              builder: (context, posSnapshot) {
                final position = posSnapshot.data ?? Duration.zero;
                final duration = _player.duration ?? Duration.zero;
                final progress = duration.inMilliseconds > 0
                    ? position.inMilliseconds / duration.inMilliseconds
                    : 0.0;

                return Column(
                  children: [
                    SliderTheme(
                      data: SliderTheme.of(context).copyWith(
                        trackHeight: 3,
                        thumbShape:
                            const RoundSliderThumbShape(enabledThumbRadius: 6),
                      ),
                      child: Slider(
                        value: progress.clamp(0.0, 1.0),
                        onChanged: (value) {
                          final seekTo = Duration(
                            milliseconds:
                                (value * duration.inMilliseconds).round(),
                          );
                          _player.seek(seekTo);
                        },
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 4),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            _formatDuration(position),
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                          Text(
                            _formatDuration(_player.duration),
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                  ],
                );
              },
            ),

            // 컨트롤 버튼
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // 10초 뒤로
                IconButton(
                  icon: const Icon(Icons.replay_10),
                  onPressed: () {
                    final newPos = _player.position - const Duration(seconds: 10);
                    _player.seek(newPos < Duration.zero ? Duration.zero : newPos);
                  },
                ),

                // 재생/정지
                const SizedBox(width: 8),
                Container(
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.primary,
                    shape: BoxShape.circle,
                  ),
                  child: processingState == ProcessingState.loading ||
                          processingState == ProcessingState.buffering
                      ? const Padding(
                          padding: EdgeInsets.all(12),
                          child: SizedBox(
                            width: 24,
                            height: 24,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          ),
                        )
                      : IconButton(
                          icon: Icon(
                            isPlaying ? Icons.pause : Icons.play_arrow,
                            color: Colors.white,
                            size: 28,
                          ),
                          onPressed: isPlaying ? _player.pause : _player.play,
                        ),
                ),
                const SizedBox(width: 8),

                // 10초 앞으로
                IconButton(
                  icon: const Icon(Icons.forward_10),
                  onPressed: () {
                    final duration = _player.duration;
                    if (duration == null) return;
                    final newPos = _player.position + const Duration(seconds: 10);
                    _player.seek(newPos > duration ? duration : newPos);
                  },
                ),
              ],
            ),
          ],
        );
      },
    );
  }
}

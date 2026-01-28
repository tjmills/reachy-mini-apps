# Reachy Mini references for agents

## Motion
- mini.goto_target(...) interpolated
- mini.set_target(...) realtime
- mini.enable_motors()

## Vision
- frame = mini.media.get_frame()  # (H,W,3) uint8 numpy

## Audio
- start_recording / get_audio_sample
- start_playing / push_audio_sample
- get_DoA

## Emotions

Import: `from emotions import happy, sad, curious, ...`

Static: `happy`, `sad`, `curious`, `neutral`, `surprised`, `angry`, `confused`, `sleepy`, `alert`

Animated: `greet`, `nod`, `shake_head`, `think`, `celebrate`, `disappointed`

Usage:
- `happy(mini)` - basic emotion
- `happy(mini, duration=1.0, intensity=0.5)` - customized
- `play_emotion(mini, "happy")` - by name
- `emotion_sequence(mini, [happy, sad])` - sequence

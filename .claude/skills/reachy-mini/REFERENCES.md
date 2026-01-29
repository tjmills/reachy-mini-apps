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

### Hand-crafted

Import: `from emotions import happy, sad, curious, ...`

Static: `happy`, `sad`, `curious`, `neutral`, `surprised`, `angry`, `confused`, `sleepy`, `alert`

Animated: `greet`, `nod`, `shake_head`, `think`, `celebrate`, `disappointed`

Usage:
- `happy(mini)` - basic emotion
- `happy(mini, duration=1.0, intensity=0.5)` - customized
- `play_emotion(mini, "happy")` - by name
- `emotion_sequence(mini, [happy, sad])` - sequence

### Pre-recorded (RecordedMoves)

Import: `from reachy_mini.motion.recorded_move import RecordedMoves`

Dataset: `pollen-robotics/reachy-mini-emotions-library`

Key methods:
- `emotions = RecordedMoves("pollen-robotics/reachy-mini-emotions-library")` - load dataset
- `emotions.list_moves()` - list all available emotion names
- `emotions.get("curious1")` - get a move by name
- `emotions.sounds.get("curious1")` - get the sound for an emotion (or None)
- `mini.play_move(move, initial_goto_duration=1.0)` - play motion trajectory
- `mini.media.play_sound(sound)` - play emotion sound

Emotions (30+): `amazed1`, `amused1`, `attentive1`, `attentive2`, `cheerful1`, `compassionate1`, `confused1`, `curious1`, `determined1`, `disappointed1`, `encouraging1`, `enthusiastic1`, `exhausted1`, `friendly1`, `grateful1`, `happy1`, `helpful1`, `impressed1`, `inspired1`, `interested1`, `joyful1`, `nostalgic1`, `optimistic1`, `pensive1`, `proud1`, `reassuring1`, `relieved1`, `sad1`, `surprised1`, `sympathetic1`, `thoughtful1`, `welcoming1`, `worried1`

Requires: `media_backend="default"` for sound playback

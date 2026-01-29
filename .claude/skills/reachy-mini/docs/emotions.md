# Emotions for Reachy Mini

Reachy Mini expresses emotions through motion patterns. There are two approaches:

## Two Approaches

| | Hand-Crafted | Pre-Recorded (RecordedMoves) |
|---|---|---|
| **How** | Custom Python functions using `goto_target()` | Load trajectories + sounds from HuggingFace dataset |
| **Sound** | No sound | Optional `.wav` per emotion |
| **Customization** | Full control (intensity, duration, sequences) | Play as-is, adjust `initial_goto_duration` |
| **Count** | ~15 emotions (you write them) | 30+ emotions from dataset |
| **Best for** | Learning the SDK, custom behaviors | Apps that need sound, quick prototyping |

---

## Pre-Recorded Emotions (RecordedMoves)

The SDK's `RecordedMoves` class loads emotion trajectories and sounds from a HuggingFace dataset.

### Loading and Listing

```python
from reachy_mini.motion.recorded_move import RecordedMoves

emotions = RecordedMoves("pollen-robotics/reachy-mini-emotions-library")
print(emotions.list_moves())  # all available emotion names
```

### Playing Emotions

```python
# Play a motion trajectory
move = emotions.get("curious1")
mini.play_move(move, initial_goto_duration=1.0)

# Play the associated sound (if present)
sound = emotions.sounds.get("curious1")
if sound is not None:
    mini.media.play_sound(sound)
```

The `initial_goto_duration` parameter controls how many seconds the robot takes to smoothly move into the first pose of the recorded trajectory before playback begins.

### Available Emotion Names (30+)

`amazed1`, `amused1`, `attentive1`, `attentive2`, `cheerful1`, `compassionate1`, `confused1`, `curious1`, `determined1`, `disappointed1`, `encouraging1`, `enthusiastic1`, `exhausted1`, `friendly1`, `grateful1`, `happy1`, `helpful1`, `impressed1`, `inspired1`, `interested1`, `joyful1`, `nostalgic1`, `optimistic1`, `pensive1`, `proud1`, `reassuring1`, `relieved1`, `sad1`, `surprised1`, `sympathetic1`, `thoughtful1`, `welcoming1`, `worried1`

### Requirements

- `media_backend="default"` (sound playback needs audio support on the robot)
- Dataset is downloaded automatically on first use

---

## Hand-Crafted Emotions

The SDK has no built-in emotion classes - hand-crafted emotions are created by combining antenna positions, head poses, and body rotation.

## How Emotions Work

### Antenna Language (Primary Indicator)
- **Up** (positive values): Happy, alert, excited, interested
- **Down** (negative values): Sad, tired, angry, dejected
- **Asymmetric**: Curious, confused, playful
- **Moving**: Thinking, celebrating, greeting

### Head Meaning
- **Pitch up**: Confident, happy, looking up
- **Pitch down**: Sad, tired, submissive
- **Roll tilt**: Curious, confused, playful
- **Z height up**: Alert, interested, engaged
- **Z height down**: Sad, sleepy, deflated

### Body Rotation
- **Swaying**: Celebratory, playful
- **Turning toward**: Interested, engaged
- **Turning away**: Disinterested, shy

## Available Emotions

### Static Emotions (Single Pose)

| Emotion | Antennas | Head | Notes |
|---------|----------|------|-------|
| `happy` | Up | Up, slight tilt | Friendly default |
| `sad` | Down | Drooped | Slow transition |
| `curious` | Asymmetric (L up, R down) | Tilted right | Inquisitive |
| `neutral` | Centered | Level | Reset pose |
| `surprised` | Sharp up | Back | Fast "cartoon" interpolation |
| `angry` | Forward/down | Thrust forward | Aggressive |
| `confused` | Asymmetric (L down, R up) | Tilted left | Opposite of curious |
| `sleepy` | Drooping | Nodding down | Very slow |
| `alert` | Quick up | Snap to attention | Fast response |

### Animated Behaviors (Sequences)

| Behavior | Description | Duration |
|----------|-------------|----------|
| `greet` | Wave antennas with nod | ~2s |
| `nod` | Up-down agreement | ~1s |
| `shake_head` | Side-to-side disagreement | ~1.2s |
| `think` | Tilt and hold | ~2s |
| `celebrate` | Excited wiggle with body sway | ~2.5s |
| `disappointed` | Deflate from hope to sad | ~2s |

## Usage

### Basic Usage

```python
from emotions import happy, sad, curious, neutral

# Play an emotion
happy(mini)

# Reset to neutral
neutral(mini)
```

### Customization

```python
# Adjust duration (seconds)
happy(mini, duration=1.5)

# Adjust intensity (0.0 to 1.0)
happy(mini, intensity=0.5)  # 50% strength

# Both
sad(mini, duration=2.0, intensity=0.3)
```

### Play by Name

```python
from emotions import play_emotion

play_emotion(mini, "happy")
play_emotion(mini, "celebrate", intensity=0.8)
```

### Emotion Sequences

```python
from emotions import emotion_sequence, happy, think, nod

# Simple sequence
emotion_sequence(mini, [happy, think, nod])

# With custom pause between
emotion_sequence(mini, [happy, sad], pause=0.5)

# With per-emotion settings
emotion_sequence(mini, [
    (happy, {"intensity": 0.5}),
    (sad, {"duration": 1.5}),
])
```

### List All Emotions

```python
from emotions import EMOTIONS

print(list(EMOTIONS.keys()))
# ['happy', 'sad', 'curious', 'neutral', 'surprised', ...]
```

## Creating Custom Emotions

Use the existing emotions as templates:

```python
import time
from reachy_mini.utils import create_head_pose

def my_emotion(mini, duration=1.0, intensity=1.0):
    """Custom emotion description."""
    # Scale values by intensity
    ant = 0.5 * intensity
    pitch = 10 * intensity

    pose = create_head_pose(z=5, roll=0, pitch=pitch, degrees=True, mm=True)
    mini.goto_target(pose, antennas=[ant, ant], duration=duration, method="minjerk")
```

### Tips for Natural Expressions

1. **Timing matters**: Fast motions ("cartoon") feel snappy/surprised; slow ("minjerk") feel thoughtful/sad
2. **Antennas lead**: Start antenna motion slightly before head for natural feel
3. **Intensity scaling**: Always scale values by intensity parameter for consistency
4. **Asymmetry adds character**: Slightly different left/right values feel more organic
5. **Use sequences**: Real emotions often transition - use `emotion_sequence` to chain

### Safety

All emotion values are designed to stay within safe limits:
- Antenna range: roughly ±1.0 radians
- Head pitch/roll: ±40 degrees
- Body yaw: ±160 degrees

Always call `mini.goto_sleep()` when done.

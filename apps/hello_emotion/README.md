# hello_emotion

Play recorded emotion moves on Reachy Mini. Discovers which emotion assets are installed on the robot and plays them in sequence.

## Usage

```bash
# Play all emotions once
make sync && make run

# Or run directly on the robot
python main.py

# List available emotions
python main.py --list

# Play specific emotions
python main.py --only sad surprised boredom

# Loop forever
python main.py --loop

# Preview without playing
python main.py --dry-run

# Adjust delay between emotions (default: 1.0s)
python main.py --delay 2.0

# Only canonical emotions (skip heuristic extras)
python main.py --no-extras
```

## Available Emotions

amazed, anxiety, boredom, cheerful, contempt, disgusted, displeased, downcast, enthusiastic, exhausted, fear, frustrated, furious, grateful, indifferent, irritated, lonely, loving, proud, rage, relief, resigned, sad, scared, serenity, shy, surprised, thoughtful, tired, uncertain, uncomfortable

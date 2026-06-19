# Canonicalization plan

## Goal

Provide a focused example of recorded move playback with optional synchronized
sound.

## Approach

- Package the app using `ReachyMiniApp` and register its dashboard entry point.
- Let `play_move()` own both motion and associated audio.
- Validate move names and support finite or repeated playback.
- Honor stop requests between blocking recorded moves.
- Cancel active playback and return to neutral during cleanup.
- Unit-test selection and sequence logic without hardware.

## Open questions

None.

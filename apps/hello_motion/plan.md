# Canonicalization plan

## Goal

Provide a small, production-shaped example of scripted and continuous motion.

## Approach

- Package the app using the official `ReachyMiniApp` entry-point contract.
- Use `goto_target()` for gestures and one `set_target()` control loop.
- Use monotonic timing and `stop_event.wait()` for responsive shutdown.
- Use `media_backend="no_media"` and return to neutral during cleanup.
- Test the pure trajectory calculations without requiring robot hardware.

## Open questions

None. The requested behavior is fully specified by the repository policy and
the developer motion playbooks.

# Canonicalization plan

## Goal

Provide the smallest robust example of reading and saving one camera frame.

## Approach

- Package the app with the official Python app entry-point contract.
- Prefer the SDK's `default` media backend and allow explicit CLI overrides.
- Retry frame capture while honoring the dashboard stop event.
- Avoid unrelated motor or wake/sleep commands.
- Validate image encoding and keep generated captures out of version control.
- Unit-test frame retry behavior with a fake media provider.

## Open questions

None.

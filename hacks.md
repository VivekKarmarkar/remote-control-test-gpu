# Hacks

## Hack 1: Lock in and launch before session breaks (Issue 2)

Everything needed to run training on the laptop GPU must be locked in and launched
before the remote session breaks.
We use `nohup` just as free insurance.
The phone session is only needed to *start* the run — not to sustain it.

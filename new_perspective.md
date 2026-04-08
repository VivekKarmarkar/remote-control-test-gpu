# New Perspective: What This Project Actually Is

## The Realization

This project started as "train a neural network on my laptop GPU from my phone while walking." A cool, weird, sci-fi experiment. But that was never the project. That was the demo.

**This project is RCP: Remote Control Protocol.**

The neural network training was the starting point, the experimental testbed, the breeding ground, and the killer demo — all at once. Through real friction, trial-and-error, and iteration, a generalized protocol emerged and was packaged as a reusable Claude Code skill (`remote-control-protocol`). In hindsight, the NN training was never the end. It was the start.

## How RCP Was Forged

Every rule in RCP maps to something that went wrong or almost went wrong:

- **Sleep Inhibit** exists because CUDA dies on suspend and can't recover
- **GPU Driver step** exists because nvidia_uvm doesn't load at boot
- **Git Public** exists because a private repo couldn't be accessed from a phone
- **Detached processes** exist because sessions drop and jobs die with them
- **Phone Connected** exists because you need to verify the link before walking away

None of these were designed upfront. Each was earned through failure. The protocol crystallized from friction, then generalized across projects.

## RCP and MCP: The Parallel

RCP rhymes with MCP, and not just phonetically.

- **MCP** (Model Context Protocol) formalizes how Claude connects to external tools. A handshake: are conditions met? Proceed.
- **RCP** (Remote Control Protocol) formalizes how a human remotely controls a compute session through Claude. Same structure: are conditions met? Proceed.

Both are state machines with a readiness gate. MCP is open-source and ecosystem-wide. RCP is personal and project-scoped. But structurally, they are the same idea: formalize a connection pattern so it's repeatable and reliable.

The parallel wasn't intentional. RCP was named in long-form and the connection only became obvious after building a local MCP server in a separate project.

## What Kind of Project Is This?

It borrows from established categories without belonging to any of them:

- The **motivation** of internal tooling — encode operational knowledge into something repeatable
- The **structure** of SRE runbooks — phased checklist with verification gates
- The **safety philosophy** of preflight checklists — all conditions must pass before go
- The **reusability** of a protocol — works across projects, not just the original

But none of these map cleanly because all of them assume a human operator. RCP assumes a **human-AI partnership** where the AI drives the sequence and the human provides judgment at critical gates. That inversion — AI as operator, human as approver — has no prior category.

**This is a Claude Code project in its truest sense.** Not because it was built with Claude Code (many projects are), but because Claude Code is both the platform it runs on and the operator that executes it. Remove Claude Code and RCP is conceptually incoherent — there's no protocol to formalize if there's no AI agent to hand off to.

## Summary

| Layer | What It Is |
|-------|-----------|
| The starting point | Training MNIST on a laptop GPU from a phone while walking |
| The role of NN training | Starting point, experimental testbed, breeding ground, killer demo |
| The actual project | RCP — Remote Control Protocol, packaged as a reusable Claude Code skill |
| The category | A Claude Code project in its truest sense — no clean prior box |
| The insight | Friction on a new platform produces tooling more valuable than the original task |

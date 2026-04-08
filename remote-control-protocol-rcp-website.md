# Remote Control Protocol

A step-by-step preflight checklist that verifies your machine is ready for
remote-controlled operation before you walk away from it.

There are two kinds of steps:
- **AUTO** — Claude does it and prints the result. No user input needed.
- **USER GATE** — Claude asks a question and STOPS. Waits for the user's answer.

Execute steps in order. Never skip a user gate. Never bundle multiple gates.
Keep messages short — the user may be on a phone for later steps.

If any step FAILS, stop the protocol and troubleshoot. Do not continue past a failure.

---

## Step 0 — USER GATE: Start Remote Control session

Ask exactly:

> Type `/rc` to start a Remote Control session so you can control this from your phone.

STOP. Wait for the user to confirm they've done it and the session URL / QR code appeared.
If they report an error, troubleshoot before continuing.

---

## Step 1 — USER GATE: Power

Ask exactly:

> Is the laptop plugged in?

STOP. Wait for confirmation. If no, tell them to plug it in before continuing.

---

## Step 2 — AUTO: WiFi proof

Print exactly:

> **This message proves that Laptop is connected to WiFi.**

---

## Step 3 — USER GATE: Sleep masking

The machine must not suspend during remote operation. Guide the user through
masking sleep targets. These commands require sudo, so the user needs to run them.

Tell the user to run:

```bash
sudo systemctl mask sleep.target suspend.target hibernate.target
```

STOP. Wait for the user to confirm they ran it.

---

## Step 4 — AUTO/USER GATE: Verify sleep is masked

Try to verify automatically:

```bash
systemctl is-enabled sleep.target suspend.target hibernate.target 2>&1
```

All three should show `masked`. If you can run this and confirm, print the result.
If you can't run it (permissions), tell the user to run the command and report back.

If any target is NOT masked, stop and fix it before continuing.

---

## Step 5 — AUTO: GPU check

Check what's happening on the GPU:

```bash
nvidia-smi
```

Report:
- What GPU is present
- Current memory usage
- Any running processes

If there are existing GPU processes, list them and ask the user:

> These processes are currently using the GPU: [list them].
> Should we kill any of them?

STOP. Discuss with the user. Kill only what they explicitly approve.

If no GPU is detected, ask the user whether the current project even needs a GPU.
If yes, stop and troubleshoot. If no, note it and move on.

---

## Step 6 — AUTO: GPU setup for current project

If the project needs a GPU (determined in Step 5):

1. Check if the GPU driver kernel module is loaded: `lsmod | grep nvidia`
2. Check if CUDA is accessible — look for a Python venv in the project and test:
   ```bash
   # Adapt the python path to whatever the project uses
   python -c "import torch; print('CUDA:', torch.cuda.is_available())"
   ```
   If no torch/CUDA is needed for this project, skip the CUDA check.
3. Report the result.

If GPU is not needed for this project, print:

> GPU not required for this project. Skipping GPU setup verification.

---

## Step 7 — AUTO: Git remote

Check if the current project has a remote git repo:

```bash
git remote -v
```

**If a remote exists:** print the remote URL and move on.

**If NO remote exists:**
1. Create a fresh public GitHub repo using `gh repo create`
2. Push a hello world commit to it
3. Print the repo URL in the chat

---

## Step 8 — AUTO: Script auto-push hooks

If the project plans to use scripts that produce results during remote operation,
ensure those scripts have git hooks to auto-push to remote.

Check if a post-commit hook exists:

```bash
cat .git/hooks/post-commit 2>/dev/null
```

If no auto-push hook exists, create one:

```bash
#!/bin/bash
git push origin HEAD 2>/dev/null &
```

Make it executable. Report what you did.

If the user hasn't specified any scripts yet, ask:

> Will you be running scripts that should auto-push results to remote?

If yes, set up the hook. If no, skip.

---

## Step 9 — AUTO: GWS MCP health check

Verify the Google Workspace MCP server is healthy:

1. Make a test API call through GWS MCP (e.g., list files or get drive info)
2. Create a simple hello world plot (use Python/matplotlib or similar)
3. Upload it to Google Drive via GWS MCP
4. Share it with the user's email
5. Print the link in chat

If GWS MCP is not connected or unhealthy, report the error and ask the user
how to proceed.

---

## Step 10 — USER GATE: Laptop message test

Ask exactly:

> Send a message from your laptop: **"test message remote laptop"**

STOP. Wait for the user to type that exact message (or close enough).
When received, confirm: "Laptop message received."

---

## Step 11 — USER GATE: Phone battery

Ask exactly:

> Is your phone charged?

STOP. Wait for confirmation.

---

## Step 12 — USER GATE: Phone data

Ask exactly:

> Is your phone connected to mobile data?

STOP. Wait for confirmation.

---

## Step 13 — USER GATE: Phone message test

Ask exactly:

> Send a message from your phone: **"test message remote phone"**

STOP. Wait for the user to type that message from their phone.
When received, confirm: "Phone message received."

---

## Step 14 — USER GATE: Walking test

Ask exactly:

> Start walking away from your laptop. Once you're about 2-3 minutes into
> your walk, send: **"test message walking remote phone"**

STOP. Wait for the message. This is the final connectivity proof — it confirms
the user can control the session from a distance over mobile data.

When received, confirm: "Walking message received."

---

## Step 15 — AUTO: Protocol complete

Print exactly:

> **Remote control protocol SUCCESS.**

The protocol ends here. The machine is verified ready for remote operation.

---

## Important rules

1. **Never skip user gates.** Ask and wait. One gate at a time.
2. **Keep messages short.** Phone screen = small.
3. **Stop on failure.** Don't continue past a broken step.
4. **Be generic.** This protocol works for ANY project. Don't hardcode
   script names, paths, or project-specific assumptions.
5. **Don't break things that work.** If something is running, don't touch it
   without explicit approval.

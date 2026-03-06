import os
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '0')

import sys
import time
import argparse
import threading
import subprocess
from datetime import datetime

import torch
import torch.nn as nn
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from torchvision import datasets

# ── Constants ────────────────────────────────────────────────────────────────

DURATION = 480
CHECKPOINT_INTERVAL = 120
BATCH_SIZE = 512
LR = 0.001
HIDDEN = 4096

C_TRAIN = '#0072B2'
C_VAL   = '#E69F00'
C_ERROR = '#D55E00'
C_GRAY  = '#999999'


# ── TeeLogger ───────────────────────────────────────────────────────────────

class TeeLogger:
    def __init__(self, path):
        self.file = open(path, 'w')
        self.stdout = sys.stdout

    def write(self, msg):
        self.stdout.write(msg)
        self.file.write(msg)
        self.file.flush()

    def flush(self):
        self.stdout.flush()
        self.file.flush()


# ── Style ────────────────────────────────────────────────────────────────────

def setup_style():
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['DejaVu Sans'],
        'axes.labelsize': 9,
        'xtick.labelsize': 7,
        'ytick.labelsize': 7,
        'axes.titlesize': 10,
        'axes.titleweight': 'bold',
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'axes.axisbelow': True,
        'grid.color': '#cccccc',
        'grid.linewidth': 0.5,
        'legend.frameon': False,
        'legend.fontsize': 8,
        'savefig.dpi': 150,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.05,
    })


# ── Model ────────────────────────────────────────────────────────────────────

class MLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(784, HIDDEN), nn.ReLU(),
            nn.Linear(HIDDEN, HIDDEN), nn.ReLU(),
            nn.Linear(HIDDEN, HIDDEN), nn.ReLU(),
            nn.Linear(HIDDEN, 10),
        )

    def forward(self, x):
        return self.net(x)


# ── Data ─────────────────────────────────────────────────────────────────────

def load_data():
    train_ds = datasets.MNIST(root='data', train=True, download=True)
    test_ds = datasets.MNIST(root='data', train=False, download=True)

    # Split 60K into 50K train + 10K val
    X_all = train_ds.data.float().div(255).view(-1, 784)
    y_all = train_ds.targets
    perm = torch.randperm(len(X_all))
    X_train = X_all[perm[:50000]].cuda()
    y_train = y_all[perm[:50000]].cuda()
    X_val = X_all[perm[50000:]].cuda()
    y_val = y_all[perm[50000:]].cuda()

    # 10K test set — held out, only used for final evaluation
    X_test = test_ds.data.float().div(255).view(-1, 784).cuda()
    y_test = test_ds.targets.cuda()

    print(f"Data loaded to GPU: train={X_train.shape}, val={X_val.shape}, test={X_test.shape}")
    return X_train, y_train, X_val, y_val, X_test, y_test


# ── Git push ─────────────────────────────────────────────────────────────────

git_lock = threading.Lock()


def git_push(message, add_path, retries=3, delay=5):
    def _worker():
        with git_lock:
            try:
                subprocess.run(["git", "add", add_path],
                               check=True, capture_output=True)
                subprocess.run(["git", "commit", "-m", message],
                               check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                print(f"  [git] commit failed: {e}")
                return
            for attempt in range(1, retries + 1):
                try:
                    subprocess.run(["git", "push", "origin", "main"],
                                   check=True, capture_output=True, timeout=30)
                    print(f"  [git] pushed: {message}")
                    return
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                    if attempt < retries:
                        print(f"  [git] push fail ({attempt}/{retries}), "
                              f"retry in {delay}s...")
                        time.sleep(delay)
                    else:
                        print(f"  [git] push failed after {retries} attempts: {e}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    print(f"  [git] push queued: {message}")
    return t


# ── Checkpoint plot ──────────────────────────────────────────────────────────

def plot_checkpoint(metrics, checkpoint_min, epoch, plots_dir):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    times = metrics['time']
    ax1.plot(times, metrics['train_loss'], color=C_TRAIN, label='Train')
    ax1.plot(times, metrics['val_loss'], color=C_VAL, linestyle='--', label='Val')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Loss')
    ax1.set_title('Loss')
    ax1.yaxis.grid(True)
    ax1.xaxis.grid(False)
    ax1.legend()

    ax2.plot(times, metrics['train_acc'], color=C_TRAIN, label='Train')
    ax2.plot(times, metrics['val_acc'], color=C_VAL, linestyle='--', label='Val')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Accuracy (%)')
    ax2.set_title('Accuracy')
    ax2.set_ylim(0, 100)
    ax2.yaxis.grid(True)
    ax2.xaxis.grid(False)
    ax2.legend()

    best_val = max(metrics['val_acc'])
    best_idx = metrics['val_acc'].index(best_val)
    ax2.annotate(f'Best val: {best_val:.1f}%',
                 xy=(times[best_idx], best_val),
                 fontsize=8, ha='center',
                 xytext=(0, 10), textcoords='offset points')

    fig.suptitle(f'Checkpoint \u2014 {checkpoint_min} min  |  '
                 f'Epoch {epoch}  |  Val acc: {best_val:.1f}%',
                 fontsize=10, fontweight='bold')
    fig.tight_layout()
    path = os.path.join(plots_dir, f'checkpoint_{checkpoint_min}min.png')
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Final: training curves ───────────────────────────────────────────────────

def plot_training_curves(metrics, results_dir):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    times = metrics['time']
    ax1.plot(times, metrics['train_loss'], color=C_TRAIN, label='Train')
    ax1.plot(times, metrics['val_loss'], color=C_VAL, linestyle='--', label='Val')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Loss')
    ax1.set_title('Loss')
    ax1.yaxis.grid(True)
    ax1.xaxis.grid(False)
    ax1.legend()

    ax2.plot(times, metrics['train_acc'], color=C_TRAIN, label='Train')
    ax2.plot(times, metrics['val_acc'], color=C_VAL, linestyle='--', label='Val')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Accuracy (%)')
    ax2.set_title('Accuracy')
    ax2.set_ylim(0, 100)
    ax2.yaxis.grid(True)
    ax2.xaxis.grid(False)
    ax2.legend()

    best_val = max(metrics['val_acc'])
    best_idx = metrics['val_acc'].index(best_val)
    best_time = times[best_idx]

    ax1.axvline(best_time, color='gray', linestyle='--', linewidth=0.8)
    ax2.axvline(best_time, color='gray', linestyle='--', linewidth=0.8)
    ax2.annotate(f'Best val acc: {best_val:.1f}% @ {best_time:.0f}s',
                 xy=(best_time, best_val),
                 fontsize=8, ha='center',
                 xytext=(0, 10), textcoords='offset points')

    fig.suptitle('Training Curves \u2014 Full Run',
                 fontsize=10, fontweight='bold')
    fig.tight_layout()
    path = os.path.join(results_dir, '01_training_curves.png')
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Sample grid (shared layout for 02, 03, 04) ──────────────────────────────

def plot_sample_grid(samples, subtitle, border_color, bar_colors_fn, save_path):
    fig, axes = plt.subplots(4, 6, figsize=(14, 10))

    for row in range(4):
        for col_pair in range(3):
            idx = row * 3 + col_pair
            img_ax = axes[row, col_pair * 2]
            bar_ax = axes[row, col_pair * 2 + 1]

            if idx < len(samples):
                img, true_label, pred_label, probs, conf = samples[idx]

                img_ax.imshow(img, cmap='gray', interpolation='nearest')
                img_ax.set_title(f'True: {true_label}  Pred: {pred_label}  '
                                 f'({conf:.1f}%)', fontsize=7)
                for spine in img_ax.spines.values():
                    spine.set_visible(True)
                    spine.set_color(border_color)
                    spine.set_linewidth(2)
                img_ax.set_xticks([])
                img_ax.set_yticks([])
                img_ax.grid(False)

                colors = bar_colors_fn(true_label, pred_label)
                y_pos = np.arange(10)
                bar_ax.barh(y_pos, probs, color=colors)
                bar_ax.set_yticks(y_pos)
                bar_ax.set_yticklabels([str(i) for i in range(10)])
                bar_ax.set_xlim(0, 1)
                bar_ax.set_xlabel('Probability', fontsize=7)
                bar_ax.invert_yaxis()
                bar_ax.grid(False)
            else:
                img_ax.set_visible(False)
                bar_ax.set_visible(False)

    fig.suptitle(subtitle, fontsize=10, fontweight='bold')
    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    print(f"  Saved: {save_path}")


def _get_predictions(model, X_val, y_val):
    model.eval()
    with torch.no_grad():
        logits = model(X_val)
        probs = torch.softmax(logits, dim=1)
        preds = logits.argmax(dim=1)
    return probs.cpu().numpy(), preds.cpu().numpy(), y_val.cpu().numpy()


# ── Final: easy wins ─────────────────────────────────────────────────────────

def plot_easy_wins(model, X_val, y_val, results_dir):
    probs, preds, labels = _get_predictions(model, X_val, y_val)
    correct = preds == labels
    correct_indices = np.where(correct)[0]
    confidences = probs[correct_indices, labels[correct_indices]]
    top12 = correct_indices[np.argsort(confidences)[::-1][:12]]

    samples = []
    for i in top12:
        img = X_val[i].cpu().numpy().reshape(28, 28)
        samples.append((img, labels[i], preds[i], probs[i], confidences[np.where(correct_indices == i)[0][0]] * 100))

    def bar_colors(true_label, pred_label):
        return [C_TRAIN if d == true_label else C_GRAY for d in range(10)]

    path = os.path.join(results_dir, '02_easy_wins.png')
    plot_sample_grid(samples, 'Easy wins \u2014 high-confidence correct predictions',
                     '#2ca02c', bar_colors, path)


# ── Final: edge cases ────────────────────────────────────────────────────────

def plot_edge_cases(model, X_val, y_val, results_dir):
    probs, preds, labels = _get_predictions(model, X_val, y_val)
    correct = preds == labels
    correct_indices = np.where(correct)[0]
    confidences = probs[correct_indices, labels[correct_indices]]
    bottom12 = correct_indices[np.argsort(confidences)[:12]]

    samples = []
    for i in bottom12:
        img = X_val[i].cpu().numpy().reshape(28, 28)
        conf = probs[i, labels[i]] * 100
        samples.append((img, labels[i], preds[i], probs[i], conf))

    def bar_colors(true_label, pred_label):
        return [C_TRAIN if d == true_label else C_GRAY for d in range(10)]

    path = os.path.join(results_dir, '03_edge_cases.png')
    plot_sample_grid(samples, 'Edge cases \u2014 correct but uncertain',
                     '#FFB300', bar_colors, path)


# ── Final: failures ──────────────────────────────────────────────────────────

def plot_failures(model, X_val, y_val, results_dir):
    probs, preds, labels = _get_predictions(model, X_val, y_val)
    wrong = preds != labels
    wrong_indices = np.where(wrong)[0]

    if len(wrong_indices) == 0:
        print("  No failures to plot!")
        return

    wrong_confidences = probs[wrong_indices, preds[wrong_indices]]
    top12 = wrong_indices[np.argsort(wrong_confidences)[::-1][:12]]

    samples = []
    for i in top12:
        img = X_val[i].cpu().numpy().reshape(28, 28)
        conf = probs[i, preds[i]] * 100
        samples.append((img, labels[i], preds[i], probs[i], conf))

    def bar_colors(true_label, pred_label):
        return [C_ERROR if d == pred_label else
                C_TRAIN if d == true_label else
                C_GRAY for d in range(10)]

    path = os.path.join(results_dir, '04_failures.png')
    plot_sample_grid(samples, 'Failures \u2014 what the model got wrong and why',
                     '#d62728', bar_colors, path)


# ── Final: confusion matrix ──────────────────────────────────────────────────

def plot_confusion_matrix(model, X_val, y_val, results_dir):
    probs, preds, labels = _get_predictions(model, X_val, y_val)

    cm = np.zeros((10, 10), dtype=int)
    for t, p in zip(labels, preds):
        cm[t, p] += 1

    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)

    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(cm_norm, cmap='Blues', vmin=0, vmax=1)

    for i in range(10):
        for j in range(10):
            color = 'white' if cm_norm[i, j] > 0.5 else 'black'
            ax.text(j, i, str(cm[i, j]), ha='center', va='center',
                    fontsize=8, color=color)

    ax.set_xticks(range(10))
    ax.set_yticks(range(10))
    ax.set_xlabel('Predicted Label')
    ax.set_ylabel('True Label')
    ax.set_title(f'Confusion Matrix \u2014 Test Set (N={len(labels):,})')
    ax.grid(False)
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()

    path = os.path.join(results_dir, '05_confusion_matrix.png')
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', default=datetime.now().strftime('%Y%m%d_%H%M%S'))
    args = parser.parse_args()
    tag = args.tag

    plots_dir = f'plots/plots_{tag}'
    results_dir = f'results/results_{tag}'
    os.makedirs(plots_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    log_path = f'logs/log_{tag}.log'
    sys.stdout = sys.stderr = TeeLogger(log_path)

    print(f"{'='*60}")
    print(f"Training run: {tag}")
    print(f"Plots:   {plots_dir}/")
    print(f"Results: {results_dir}/")
    print(f"Log:     {log_path}")
    print(f"{'='*60}")

    setup_style()
    X_train, y_train, X_val, y_val, X_test, y_test = load_data()

    model = MLP().cuda()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss()

    param_count = sum(p.numel() for p in model.parameters())
    print(f"Model: {param_count:,} parameters")
    print(f"Training for {DURATION}s, checkpoints every {CHECKPOINT_INTERVAL}s")
    print(f"{'='*60}")

    metrics = {'time': [], 'epoch': [], 'train_loss': [], 'val_loss': [],
               'train_acc': [], 'val_acc': []}

    push_threads = []
    start_time = time.time()
    next_checkpoint = CHECKPOINT_INTERVAL
    epoch = 0

    while True:
        elapsed = time.time() - start_time
        if elapsed >= DURATION:
            break

        epoch += 1

        perm = torch.randperm(X_train.shape[0], device='cuda')
        X_shuffled = X_train[perm]
        y_shuffled = y_train[perm]

        model.train()
        epoch_loss = 0.0
        correct = 0
        total = 0

        for i in range(0, X_train.shape[0], BATCH_SIZE):
            X_batch = X_shuffled[i:i + BATCH_SIZE]
            y_batch = y_shuffled[i:i + BATCH_SIZE]

            optimizer.zero_grad()
            out = model(X_batch)
            loss = criterion(out, y_batch)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item() * X_batch.shape[0]
            correct += (out.argmax(1) == y_batch).sum().item()
            total += X_batch.shape[0]

        train_loss = epoch_loss / total
        train_acc = 100 * correct / total

        model.eval()
        with torch.no_grad():
            val_out = model(X_val)
            val_loss = criterion(val_out, y_val).item()
            val_acc = 100 * (val_out.argmax(1) == y_val).sum().item() / y_val.shape[0]

        elapsed = time.time() - start_time
        metrics['time'].append(elapsed)
        metrics['epoch'].append(epoch)
        metrics['train_loss'].append(train_loss)
        metrics['val_loss'].append(val_loss)
        metrics['train_acc'].append(train_acc)
        metrics['val_acc'].append(val_acc)

        print(f"Epoch {epoch:4d} | {elapsed:6.1f}s | "
              f"train_loss={train_loss:.4f} train_acc={train_acc:.1f}% | "
              f"val_loss={val_loss:.4f} val_acc={val_acc:.1f}%")

        if elapsed >= next_checkpoint:
            checkpoint_min = int(next_checkpoint // 60)
            print(f"\n--- Checkpoint at {checkpoint_min} min ---")
            plot_checkpoint(metrics, checkpoint_min, epoch, plots_dir)
            push_threads.append(
                git_push(f"checkpoint {checkpoint_min}min [{tag}]", plots_dir))
            next_checkpoint += CHECKPOINT_INTERVAL
            print()

    # Final evaluation on held-out test set
    model.eval()
    with torch.no_grad():
        test_out = model(X_test)
        test_acc = 100 * (test_out.argmax(1) == y_test).sum().item() / y_test.shape[0]
        test_loss = criterion(test_out, y_test).item()

    print(f"\n{'='*60}")
    print("Training complete.")
    print(f"Test set: loss={test_loss:.4f}, acc={test_acc:.1f}%")
    print("Generating final visualizations (on test set)...")
    print(f"{'='*60}")

    plot_training_curves(metrics, results_dir)
    plot_easy_wins(model, X_test, y_test, results_dir)
    plot_edge_cases(model, X_test, y_test, results_dir)
    plot_failures(model, X_test, y_test, results_dir)
    plot_confusion_matrix(model, X_test, y_test, results_dir)

    push_threads.append(
        git_push(f"final results [{tag}]", results_dir))

    print("\nWaiting for pending pushes...")
    for t in push_threads:
        t.join(timeout=60)

    print("Done.")


if __name__ == '__main__':
    main()

"""Offline charts from caller data. Fonts and cutoff are explicit; no fetching."""
from pathlib import Path
import hashlib
import json
import math
import os
import warnings

import matplotlib
matplotlib.use('Agg')
from matplotlib import font_manager, ft2font, pyplot as plt
import numpy as np
import pandas as pd
from font_support import candidates, missing_message

NAVY = '#244B69'; BLUE = '#5C879B'; RED = '#A7443D'; GRAY = '#A7AFB7'; GREEN = '#4D786C'
plt.rcParams.update({'font.size': 9, 'axes.unicode_minus': False, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.edgecolor': '#999', 'axes.labelcolor': '#111',
                     'xtick.color': '#333', 'ytick.color': '#333', 'figure.facecolor': 'white',
                     'axes.facecolor': 'white', 'savefig.facecolor': 'white'})


def configure_font(font=None):
    explicit = font or os.environ.get('AIR_CHART_FONT')
    choices = [Path(explicit).expanduser()] if explicit else candidates('head')
    failures = []
    for path in choices:
        if not path.is_file():
            continue
        try:
            face = ft2font.FT2Font(str(path))
            font_manager.fontManager.addfont(str(path))
            family = font_manager.FontProperties(fname=str(path)).get_name()
            plt.rcParams['font.family'] = family
            return str(path.resolve()), set(face.get_charmap())
        except Exception as exc:
            failures.append(str(exc))
    raise ValueError(missing_message('chart', '; '.join(failures)))


class Charts:
    def __init__(self, run, font=None):
        self.font, self.glyphs = configure_font(font)
        self.run = Path(run).resolve()
        self.root = self.run / '03_models/charts'
        self.root.mkdir(parents=True, exist_ok=True)
        self.items = []

    def save(self, id, fig, source):
        if not id or Path(id).name != id or any(char in id for char in '/\\:') or id in ('.', '..'):
            plt.close(fig)
            raise ValueError('chart id must be a single filename stem')
        path = self.root / (id + '.png')
        try:
            # Missing glyph warnings are errors: a saved Chinese chart must be legible.
            with warnings.catch_warnings():
                warnings.filterwarnings('error', message=r'Glyph .* missing from font')
                fig.tight_layout(pad=1.2)
                fig.savefig(path, dpi=210, bbox_inches='tight')
        except UserWarning as exc:
            raise ValueError(missing_message('chart', str(exc))) from exc
        finally:
            plt.close(fig)
        self.items.append({'id': id, 'path': path.relative_to(self.run).as_posix(), 'source': source,
                           'font': self.font, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        return id

    def pair(self, id, labels, left, right, left_label, right_label, source, colors=None):
        fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.1)); x = np.arange(len(labels))
        for axis, vals, label, col in zip(axes, [left, right], [left_label, right_label], colors or [NAVY, BLUE]):
            axis.bar(x, vals, color=[col if v >= 0 else RED for v in vals]); axis.axhline(0, color='#777', lw=.6)
            axis.set(xticks=x, xticklabels=labels, ylabel=label); axis.grid(axis='y', color='#EEE', lw=.6); axis.set_axisbelow(True)
        return self.save(id, fig, source)

    def line(self, id, labels, series, ylabel, source):
        fig, ax = plt.subplots(figsize=(9.5, 3.05)); x = np.arange(len(labels))
        for j, (label, values) in enumerate(series.items()):
            ax.plot(x, values, 'o-', color=[NAVY, RED, BLUE, GRAY, GREEN][j % 5], label=label, lw=1.4, ms=4)
        ax.set(xticks=x, xticklabels=labels, ylabel=ylabel); ax.axhline(0, color='#888', lw=.6)
        ax.grid(axis='y', color='#EEE', lw=.6); ax.legend(frameon=False, fontsize=8, ncol=2); ax.set_axisbelow(True)
        return self.save(id, fig, source)

    def bars(self, id, labels, values, ylabel, source, horizontal=False):
        fig, ax = plt.subplots(figsize=(9.5, 3.1)); x = np.arange(len(labels)); cols = [NAVY if v >= 0 else RED for v in values]
        if horizontal:
            ax.barh(labels, values, color=cols); ax.invert_yaxis(); ax.set_xlabel(ylabel); ax.grid(axis='x', color='#EEE')
        else:
            ax.bar(x, values, color=cols); ax.set(xticks=x, xticklabels=labels, ylabel=ylabel); ax.grid(axis='y', color='#EEE')
        ax.axhline(0, color='#888', lw=.6); ax.set_axisbelow(True)
        return self.save(id, fig, source)

    def grouped(self, id, labels, series, ylabel, source, stacked=False):
        fig, ax = plt.subplots(figsize=(9.5, 3.1)); x = np.arange(len(labels)); palette = [NAVY, BLUE, GRAY, RED, GREEN]
        n = len(series); width = .75 / n; positive = np.zeros(len(labels)); negative = np.zeros(len(labels))
        for j, (label, vals) in enumerate(series.items()):
            values = np.asarray(vals)
            if stacked:
                bottom = np.where(values >= 0, positive, negative)
                ax.bar(x, values, bottom=bottom, color=palette[j % 5], label=label)
                positive += np.where(values >= 0, values, 0); negative += np.where(values < 0, values, 0)
            else:
                ax.bar(x - .375 + width * (j + .5), vals, width, color=palette[j % 5], label=label)
        ax.set(xticks=x, xticklabels=labels, ylabel=ylabel); ax.axhline(0, color='#888', lw=.6)
        ax.grid(axis='y', color='#EEE'); ax.legend(frameon=False, fontsize=8, ncol=min(n, 3)); ax.set_axisbelow(True)
        return self.save(id, fig, source)

    def heat(self, id, cols, rows, grid, xlabel, ylabel, source, unit='每股价值'):
        fig, ax = plt.subplots(figsize=(9.5, 3.1)); a = np.asarray(grid); im = ax.imshow(a, cmap='Blues', aspect='auto')
        ax.set(xticks=range(len(cols)), xticklabels=cols, yticks=range(len(rows)), yticklabels=rows, xlabel=xlabel, ylabel=ylabel)
        mid = (a.max() + a.min()) / 2
        for y in range(len(rows)):
            for x in range(len(cols)):
                ax.text(x, y, f'{a[y, x]:.1f}', ha='center', va='center', color='white' if a[y, x] > mid else '#111', fontsize=8)
        fig.colorbar(im, ax=ax, label=unit)
        return self.save(id, fig, source)

    def waterfall(self, id, labels, values, ylabel, source, *, tolerance=1e-6):
        if (len(values) < 2 or len(labels) != len(values) or not math.isfinite(tolerance) or tolerance < 0
                or not all(math.isfinite(value) for value in values)):
            raise ValueError('waterfall needs matching labels, finite values and nonnegative tolerance')
        subtotal = math.fsum(values[:-1])
        if not math.isclose(subtotal, values[-1], rel_tol=0, abs_tol=tolerance):
            raise ValueError(f'waterfall mismatch {id}: contributions={subtotal}, total={values[-1]}, tolerance={tolerance}')
        fig, ax = plt.subplots(figsize=(9.5, 3.2)); cumulative = 0
        for j, value in enumerate(values):
            total = j == len(values) - 1
            start = 0 if total else cumulative
            end = value if total else cumulative + value
            bottom = min(start, end)
            ax.bar(j, abs(value), bottom=bottom, color=NAVY if total else BLUE if value >= 0 else RED)
            ax.annotate(f'{value:.1f}' if total else f'{value:+.1f}', (j, max(start, end)),
                        xytext=(0, 5), textcoords='offset points', ha='center', fontsize=8)
            if not total:
                cumulative = end
        ax.set(xticks=range(len(labels)), xticklabels=labels, ylabel=ylabel)
        ax.axhline(0, color='#777', lw=.6); ax.grid(axis='y', color='#EEE'); ax.set_axisbelow(True)
        return self.save(id, fig, source)

    def price(self, id, csv_path, source, date_col='date', close_col='close', *, last):
        """Caller must supply cutoff YYYY-MM-DD, or explicit None for no cutoff."""
        frame = pd.read_csv(csv_path); frame[date_col] = pd.to_datetime(frame[date_col])
        if last is not None:
            frame = frame[frame[date_col] <= pd.Timestamp(last)].copy()
        frame = frame.sort_values(date_col)
        fig, ax = plt.subplots(figsize=(9.5, 3.2)); ax.plot(frame[date_col], frame[close_col], color='#222', lw=1, label='周收盘')
        for n, col in [(20, BLUE), (50, RED), (200, GRAY)]:
            ax.plot(frame[date_col], frame[close_col].rolling(n).mean(), color=col, label=f'{n}周均线', lw=1)
        ax.set_ylabel('价格 / 原交易币种'); ax.legend(frameon=False, ncol=4, fontsize=8); ax.grid(axis='y', color='#EEE')
        return self.save(id, fig, source)

    def finish(self):
        (self.root / 'chart-manifest.json').write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding='utf-8')
        return self.items

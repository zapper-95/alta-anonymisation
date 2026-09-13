#!/usr/bin/env python3
"""
Side-by-side viewer for comparing any number of folders of text files that
share filenames.

Usage:
    python diff_viewer.py <folder_1> <folder_2> [<folder_3> ...]
    python diff_viewer.py                # pick folders one at a time

One folder acts as the reference and is shown unhighlighted. Every other
column is highlighted against it, so with three or more folders you are
always reading "how does this differ from the reference", never an
ill-defined multi-way diff.

Keys:
    n / Right   next document
    p / Left    previous document
    s           toggle synchronised scrolling
    1-9         make that column the reference
"""

import sys
import re
import difflib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# ---------------------------------------------------------------- appearance

BG = "#fbfbfa"
FG = "#1f2020"
DELETE_BG = "#ffb3ae"   # in the reference, absent here
INSERT_BG = "#d4f4d7"   # here, absent from the reference
REPLACE_BG = "#ffe9c4"  # differing span
REF_BORDER = "#7a8ba0"
GUTTER = "#e8e8e6"

BODY_FONT = ("Georgia", 14)
UI_FONT = ("Helvetica", 12)
MONO_FONT = ("Menlo", 11)

TEXT_SUFFIXES = {".txt", ".md", ".text", ".json", ".jsonl", ""}
GAP_MARKER = "\u2009"  # thin space, tagged, marks where text was removed

WHEEL_UNITS = 3        # lines moved per wheel notch
OVERSCROLL_NOTCHES = 1  # notches past the edge before changing document


# ---------------------------------------------------------------- diff logic

def tokenize(text):
    """Split into tokens that keep their trailing whitespace, so that
    ''.join(tokens) == text exactly."""
    return re.findall(r"\S+\s*|\s+", text)


def diff_against_reference(reference, other):
    """Highlight `other` relative to `reference`.

    Returns (spans, fraction_unchanged) where spans is a list of
    (tag, string) pairs covering the whole of `other`, plus thin markers
    at points where reference content is missing.
    """
    a, b = tokenize(reference), tokenize(other)
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)

    spans = []
    unchanged = 0

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            spans.append(("equal", "".join(b[j1:j2])))
            unchanged += (i2 - i1)
        elif op == "insert":
            spans.append(("insert", "".join(b[j1:j2])))
        elif op == "replace":
            spans.append(("replace", "".join(b[j1:j2])))
        elif op == "delete":
            # nothing here to colour, so leave a sliver where it went
            spans.append(("delete", GAP_MARKER))

    fraction = unchanged / len(a) if a else 1.0
    return spans, fraction


# ---------------------------------------------------------------- file groups

def collect_groups(dirs):
    """Return (groups, orphan_note) where groups is a list of
    (name, [path_per_folder]) for filenames present in every folder."""
    def index(d):
        return {
            p.name: p
            for p in sorted(Path(d).iterdir())
            if p.is_file()
            and not p.name.startswith(".")
            and p.suffix.lower() in TEXT_SUFFIXES
        }

    indices = [index(d) for d in dirs]
    if not indices:
        return [], ""

    shared = set(indices[0])
    for idx in indices[1:]:
        shared &= set(idx)

    groups = [(n, [idx[n] for idx in indices]) for n in sorted(shared)]

    notes = []
    for d, idx in zip(dirs, indices):
        missing = len(set(idx) - shared)
        if missing:
            notes.append(f"{Path(d).name}: {missing} unmatched")
    return groups, "   ".join(notes)


def read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:  # an unreadable file should not kill the viewer
        return f"[could not read {path.name}: {exc}]"


# ---------------------------------------------------------------- the viewer

class DiffViewer(tk.Tk):
    def __init__(self, groups, labels, orphans):
        super().__init__()
        self.groups = groups
        self.labels = labels
        self.n = len(labels)
        self.index = 0
        self.reference = 0
        self.sync = tk.BooleanVar(value=False)
        self._syncing = False
        self._overscroll = 0

        self.title(f"Side-by-side diff  ({self.n} folders)")
        self.geometry(f"{min(1800, 300 + 420 * self.n)}x900")
        self.configure(bg=BG)

        self.ref_choice = tk.StringVar(value=labels[0])

        self._build_toolbar(orphans)
        self._build_panes()
        self._build_sidebar()
        self._bind_keys()

        self.show(0)

    # -- layout ------------------------------------------------------------

    def _build_toolbar(self, orphans):
        bar = tk.Frame(self, bg=GUTTER, padx=10, pady=8)
        bar.pack(side="top", fill="x")

        tk.Button(bar, text="< Prev", font=UI_FONT,
                  command=self.prev).pack(side="left")
        tk.Button(bar, text="Next >", font=UI_FONT,
                  command=self.next).pack(side="left", padx=(6, 16))

        self.counter = tk.Label(bar, text="", font=UI_FONT, bg=GUTTER, fg=FG)
        self.counter.pack(side="left")

        self.hint = tk.Label(bar, text="", font=(UI_FONT[0], 11),
                             bg=GUTTER, fg="#8a7a55")
        self.hint.pack(side="left", padx=(14, 0))

        tk.Checkbutton(bar, text="sync scroll", font=UI_FONT, bg=GUTTER,
                       variable=self.sync).pack(side="right", padx=12)

        picker = ttk.Combobox(bar, values=self.labels, state="readonly",
                              textvariable=self.ref_choice, width=22,
                              font=UI_FONT)
        picker.pack(side="right")
        picker.bind("<<ComboboxSelected>>", self._on_reference_change)
        tk.Label(bar, text="reference:", font=UI_FONT,
                 bg=GUTTER, fg="#555").pack(side="right", padx=(0, 6))

        legend = tk.Frame(self, bg=BG, padx=10, pady=4)
        legend.pack(side="top", fill="x")
        for colour, text in ((REPLACE_BG, "changed"),
                            (INSERT_BG, "added"),
                            (DELETE_BG, "removed (marker)")):
            tk.Label(legend, text=f"  {text}  ", font=UI_FONT,
                     bg=colour, fg=FG).pack(side="left", padx=(0, 10))
        if orphans:
            tk.Label(legend, text=orphans, font=UI_FONT,
                     bg=BG, fg="#a33").pack(side="right")

    def _build_panes(self):
        body = tk.Frame(self, bg=BG)
        body.pack(side="top", fill="both", expand=True)
        self.body = body

        body.rowconfigure(0, weight=1)
        self.texts, self.scrolls, self.headings, self.frames = [], [], [], []

        for col, label in enumerate(self.labels):
            # uniform= forces every column to exactly the same width
            body.columnconfigure(col, weight=1, uniform="panes")
            self._make_pane(body, label, col)

    def _make_pane(self, parent, heading, column):
        frame = tk.Frame(parent, bg=BG)
        frame.grid(row=0, column=column, sticky="nsew", padx=5, pady=6)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        head = tk.Label(frame, text=heading, font=(UI_FONT[0], 11, "bold"),
                        bg=BG, fg="#555", anchor="w")
        head.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        wrap = tk.Frame(frame, bg=BG)
        wrap.grid(row=1, column=0, sticky="nsew")

        scroll = tk.Scrollbar(wrap)
        scroll.pack(side="right", fill="y")

        # width/height of 1 stops the widget requesting its default 80x24
        # characters, so the grid weights decide the size instead
        text = tk.Text(
            wrap, wrap="word", font=BODY_FONT, bg=BG, fg=FG,
            width=1, height=1,
            padx=14, pady=12, relief="solid", borderwidth=1,
            spacing1=2, spacing2=3, spacing3=8,
            highlightthickness=0, takefocus=0,
        )
        text.pack(side="left", fill="both", expand=True)

        idx = len(self.texts)
        text.config(yscrollcommand=lambda f, l, i=idx: self._on_scroll(i, f, l))
        scroll.config(command=lambda *a, i=idx: self._on_drag(i, *a))

        # take over the wheel so overscrolling can change document
        text.bind("<MouseWheel>", lambda e, i=idx: self._on_wheel(i, e))
        text.bind("<Button-4>", lambda e, i=idx: self._on_wheel(i, e))
        text.bind("<Button-5>", lambda e, i=idx: self._on_wheel(i, e))
        text.bind("<Shift-MouseWheel>", lambda e: "break")

        text.tag_config("equal", background=BG)
        text.tag_config("delete", background=DELETE_BG)
        text.tag_config("insert", background=INSERT_BG)
        text.tag_config("replace", background=REPLACE_BG)

        self.frames.append(frame)
        self.headings.append(head)
        self.texts.append(text)
        self.scrolls.append(scroll)

    def _build_sidebar(self):
        side = tk.Frame(self, bg=GUTTER, width=220)
        side.pack(side="right", fill="y", before=self.body)
        side.pack_propagate(False)

        tk.Label(side, text="files", font=(UI_FONT[0], 11, "bold"),
                 bg=GUTTER, fg="#555").pack(anchor="w", padx=10, pady=(10, 4))

        bar = tk.Scrollbar(side)
        bar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            side, font=MONO_FONT, bg=BG, fg=FG, borderwidth=0,
            highlightthickness=0, activestyle="none",
            selectbackground="#cfd8e3", yscrollcommand=bar.set,
        )
        self.listbox.pack(side="left", fill="both", expand=True, padx=(8, 0))
        bar.config(command=self.listbox.yview)

        for name, _ in self.groups:
            self.listbox.insert("end", name)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

    def _bind_keys(self):
        self.bind("<Right>", lambda e: self.next())
        self.bind("<Left>", lambda e: self.prev())
        self.bind("n", lambda e: self.next())
        self.bind("p", lambda e: self.prev())
        self.bind("s", lambda e: self.sync.set(not self.sync.get()))
        for i in range(min(self.n, 9)):
            self.bind(str(i + 1), lambda e, i=i: self._set_reference(i))

    # -- scrolling ---------------------------------------------------------

    def _on_scroll(self, i, first, last):
        self.scrolls[i].set(first, last)
        if self.sync.get() and not self._syncing:
            self._syncing = True
            for j, other in enumerate(self.texts):
                if j != i:
                    other.yview_moveto(first)
            self._syncing = False

    def _on_drag(self, i, *args):
        self.texts[i].yview(*args)
        if self.sync.get() and not self._syncing:
            self._syncing = True
            top = self.texts[i].yview()[0]
            for j, other in enumerate(self.texts):
                if j != i:
                    other.yview_moveto(top)
            self._syncing = False

    def _on_wheel(self, i, event):
        """Scroll the pane under the cursor. Scrolling past either end
        accumulates, and once past the threshold moves to the neighbouring
        document, so the whole set can be read without touching a button."""
        direction = self._wheel_direction(event)
        if direction == 0:
            return "break"

        text = self.texts[i]
        first, last = text.yview()
        at_bottom = last >= 0.999
        at_top = first <= 0.001

        if (direction > 0 and at_bottom) or (direction < 0 and at_top):
            # already parked against the edge, so count the overscroll
            if self._overscroll and (self._overscroll > 0) != (direction > 0):
                self._overscroll = 0  # reversed, start again
            self._overscroll += direction

            if abs(self._overscroll) >= OVERSCROLL_NOTCHES:
                self._overscroll = 0
                if direction > 0:
                    self.next(land_at_top=True)
                else:
                    self.prev(land_at_bottom=True)
            else:
                self._update_hint(direction)
            return "break"

        self._overscroll = 0
        self.hint.config(text="")
        text.yview_scroll(direction * WHEEL_UNITS, "units")
        return "break"

    @staticmethod
    def _wheel_direction(event):
        """Normalise wheel events across platforms to -1, 0 or 1."""
        if getattr(event, "num", None) == 4:
            return -1
        if getattr(event, "num", None) == 5:
            return 1
        delta = getattr(event, "delta", 0)
        if delta == 0:
            return 0
        return -1 if delta > 0 else 1

    def _update_hint(self, direction):
        remaining = OVERSCROLL_NOTCHES - abs(self._overscroll)
        if direction > 0:
            arrow, word = "\u2193", "next"
            available = self.index < len(self.groups) - 1
        else:
            arrow, word = "\u2191", "previous"
            available = self.index > 0
        if available:
            self.hint.config(text=f"{arrow} keep scrolling for {word} ({remaining})")
        else:
            self.hint.config(text=f"{arrow} end of set")

    # -- reference ---------------------------------------------------------

    def _on_reference_change(self, _event=None):
        self._set_reference(self.labels.index(self.ref_choice.get()))

    def _set_reference(self, i):
        if not 0 <= i < self.n:
            return
        self.reference = i
        self.ref_choice.set(self.labels[i])
        self.show(self.index)

    # -- navigation --------------------------------------------------------

    def show(self, i, land_at_bottom=False):
        if not self.groups:
            return
        self.index = max(0, min(i, len(self.groups) - 1))
        self._overscroll = 0
        self.hint.config(text="")
        name, paths = self.groups[self.index]

        contents = [read(p) for p in paths]
        reference_text = contents[self.reference]

        for col, content in enumerate(contents):
            if col == self.reference:
                spans, note = [("equal", content)], "reference"
                border = REF_BORDER
            else:
                spans, fraction = diff_against_reference(reference_text, content)
                note = f"{fraction:.0%} kept"
                border = "#d5d5d2"

            self._render(self.texts[col], spans)
            self.texts[col].config(highlightthickness=2,
                                   highlightbackground=border)
            self.headings[col].config(
                text=f"{self.labels[col]}   ·   {note}",
                fg="#333" if col == self.reference else "#777",
            )

        self.counter.config(
            text=f"{self.index + 1} / {len(self.groups)}    {name}")

        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(self.index)
        self.listbox.see(self.index)

        if land_at_bottom:
            for text in self.texts:
                text.yview_moveto(1.0)

    def _render(self, widget, spans):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        for tag, chunk in spans:
            widget.insert("end", chunk, tag)
        widget.config(state="disabled")
        widget.yview_moveto(0)

    def next(self, land_at_top=False):
        self.show(self.index + 1)

    def prev(self, land_at_bottom=False):
        self.show(self.index - 1, land_at_bottom=land_at_bottom)

    def _on_select(self, _event):
        sel = self.listbox.curselection()
        if sel:
            self.show(sel[0])


# ---------------------------------------------------------------- entry point

def pick_folders():
    root = tk.Tk()
    root.withdraw()
    dirs = []
    while True:
        title = f"Folder {len(dirs) + 1} (cancel when done)"
        chosen = filedialog.askdirectory(title=title)
        if not chosen:
            break
        dirs.append(chosen)
    root.destroy()
    return dirs


def fail(message):
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Nothing to compare", message)
    root.destroy()


def main():
    dirs = sys.argv[1:] or pick_folders()

    if len(dirs) < 2:
        fail("Give at least two folders to compare.")
        return

    missing = [d for d in dirs if not Path(d).is_dir()]
    if missing:
        fail("Not a folder:\n" + "\n".join(missing))
        return

    groups, orphans = collect_groups(dirs)
    if not groups:
        fail("No filenames are present in all of the folders given.")
        return

    labels = [Path(d).name or str(d) for d in dirs]
    DiffViewer(groups, labels, orphans).mainloop()


if __name__ == "__main__":
    main()
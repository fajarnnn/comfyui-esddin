# hf_compare_dirs_ui.py
# pip install -U huggingface_hub
import os
import threading
import traceback
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from queue import Queue, Empty

from huggingface_hub import HfFileSystem


def _load_cache_set(path: str) -> set:
    s = set()
    if not path:
        return s
    if not os.path.isfile(path):
        return s
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if name and not name.startswith("#"):
                s.add(name)
    return s


def _save_cache_set(path: str, items: set):
    if not path:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for name in sorted(items):
            f.write(name + "\n")


class HFDirCompareUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HF Repo Folder Diff (Tkinter UI)")
        self.geometry("1020x700")

        self.log_q = Queue()
        self.worker = None
        self.stop_flag = threading.Event()

        # -------- Variables (input-able) --------
        self.var_hf_token = tk.StringVar(value="")

        self.var_repotype1 = tk.StringVar(value="datasets")
        self.var_repoid1   = tk.StringVar(value="jpesddin/raw-ig")
        self.var_lv1dir1   = tk.StringVar(value="raw")

        self.var_repotype2 = tk.StringVar(value="datasets")
        self.var_repoid2   = tk.StringVar(value="nutakuesddin/raw-ign/")
        self.var_lv1dir2   = tk.StringVar(value="renamed")

        # Checkbox: has level2 folder
        self.var_has_level2 = tk.BooleanVar(value=True)

        # Cache file path
        self.var_cache_path = tk.StringVar(value="has_level2_cache.txt")
        self.var_use_cache  = tk.BooleanVar(value=True)   # enable cache usage

        self._build_ui()
        self.after(80, self._drain_log)

    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill="x", **pad)

        # Row 0: Token
        ttk.Label(frm, text="HF_TOKEN").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_hf_token, width=95, show="*").grid(
            row=0, column=1, columnspan=7, sticky="we", **pad
        )

        # Row 1: Repo 1
        ttk.Label(frm, text="repotype1").grid(row=1, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_repotype1, width=12).grid(row=1, column=1, sticky="w", **pad)
        ttk.Label(frm, text="repoid1").grid(row=1, column=2, sticky="w")
        ttk.Entry(frm, textvariable=self.var_repoid1, width=30).grid(row=1, column=3, sticky="w", **pad)
        ttk.Label(frm, text="lv1dir1").grid(row=1, column=4, sticky="w")
        ttk.Entry(frm, textvariable=self.var_lv1dir1, width=18).grid(row=1, column=5, sticky="w", **pad)

        # Row 2: Repo 2
        ttk.Label(frm, text="repotype2").grid(row=2, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_repotype2, width=12).grid(row=2, column=1, sticky="w", **pad)
        ttk.Label(frm, text="repoid2").grid(row=2, column=2, sticky="w")
        ttk.Entry(frm, textvariable=self.var_repoid2, width=30).grid(row=2, column=3, sticky="w", **pad)
        ttk.Label(frm, text="lv1dir2").grid(row=2, column=4, sticky="w")
        ttk.Entry(frm, textvariable=self.var_lv1dir2, width=18).grid(row=2, column=5, sticky="w", **pad)

        # Row 3: Cache
        ttk.Checkbutton(frm, text="Use cache txt", variable=self.var_use_cache).grid(
            row=3, column=0, columnspan=2, sticky="w", **pad
        )
        ttk.Label(frm, text="cache_path").grid(row=3, column=2, sticky="w")
        ttk.Entry(frm, textvariable=self.var_cache_path, width=40).grid(row=3, column=3, sticky="w", **pad)
        ttk.Button(frm, text="Browse", command=self._browse_cache).grid(row=3, column=4, sticky="w", **pad)

        # Row 4: options + buttons
        ttk.Checkbutton(
            frm,
            text="Has level2 folders filter (ON: hanya folder yg punya subfolder)",
            variable=self.var_has_level2
        ).grid(row=4, column=0, columnspan=5, sticky="w", **pad)

        btnfrm = ttk.Frame(frm)
        btnfrm.grid(row=4, column=5, columnspan=3, sticky="e", **pad)

        self.btn_run = ttk.Button(btnfrm, text="Run", command=self.on_run)
        self.btn_run.pack(side="left", padx=6)

        self.btn_stop = ttk.Button(btnfrm, text="Stop", command=self.on_stop, state="disabled")
        self.btn_stop.pack(side="left", padx=6)

        self.btn_clear = ttk.Button(btnfrm, text="Clear Log", command=self.clear_log)
        self.btn_clear.pack(side="left", padx=6)

        frm.columnconfigure(3, weight=1)
        frm.columnconfigure(7, weight=1)

        # Log output
        logfrm = ttk.Frame(self)
        logfrm.pack(fill="both", expand=True, **pad)

        self.txt = tk.Text(logfrm, wrap="word", font=("Consolas", 10))
        self.txt.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(logfrm, orient="vertical", command=self.txt.yview)
        sb.pack(side="right", fill="y")
        self.txt.configure(yscrollcommand=sb.set)

    def _browse_cache(self):
        path = filedialog.asksaveasfilename(
            title="Select cache txt",
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("All files", "*.*")]
        )
        if path:
            self.var_cache_path.set(path)

    def log(self, s: str):
        self.log_q.put(s)

    def _drain_log(self):
        try:
            while True:
                s = self.log_q.get_nowait()
                self.txt.insert("end", s + "\n")
                self.txt.see("end")
        except Empty:
            pass
        self.after(80, self._drain_log)

    def clear_log(self):
        self.txt.delete("1.0", "end")

    def on_stop(self):
        self.stop_flag.set()
        self.log(">> Stop requested... (akan berhenti setelah iterasi aktif selesai)")

    def on_run(self):
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("Info", "Masih running. Klik Stop dulu.")
            return

        self.stop_flag.clear()
        self.btn_run.config(state="disabled")
        self.btn_stop.config(state="normal")

        args = {
            "HF_TOKEN": self.var_hf_token.get(),
            "repotype1": self.var_repotype1.get().strip(),
            "repotype2": self.var_repotype2.get().strip(),
            "repoid1": self.var_repoid1.get().strip(),
            "repoid2": self.var_repoid2.get().strip(),
            "lv1dir1": self.var_lv1dir1.get().strip().strip("/"),
            "lv1dir2": self.var_lv1dir2.get().strip().strip("/"),
            "has_level2": bool(self.var_has_level2.get()),
            "use_cache": bool(self.var_use_cache.get()),
            "cache_path": self.var_cache_path.get().strip(),
        }

        self.worker = threading.Thread(target=self._run_logic, args=(args,), daemon=True)
        self.worker.start()
        self.after(200, self._poll_worker_done)

    def _poll_worker_done(self):
        if self.worker and self.worker.is_alive():
            self.after(200, self._poll_worker_done)
            return
        self.btn_run.config(state="normal")
        self.btn_stop.config(state="disabled")

    # ================== LOGIC (tetap) + cache optimization ==================
    def _run_logic(self, args):
        try:
            HF_TOKEN = args["HF_TOKEN"]
            fs = HfFileSystem(token=HF_TOKEN)

            repotype1 = args["repotype1"]
            repotype2 = args["repotype2"]
            repoid1 = args["repoid1"]
            repoid2 = args["repoid2"]
            lv1dir1 = args["lv1dir1"]
            lv1dir2 = args["lv1dir2"]
            has_level2 = args["has_level2"]
            use_cache = args["use_cache"]
            cache_path = args["cache_path"]

            # Path safety
            repoid1_path = repoid1.rstrip("/")
            repoid2_path = repoid2.rstrip("/")

            # Load cache (set of folder names known to have level2)
            cache_set = _load_cache_set(cache_path) if use_cache else set()
            if use_cache:
                self.log(f">> Cache loaded: {len(cache_set)} entries from: {cache_path}")

            # List level1 dirs in repo1/lv1dir1
            base1 = f"{repotype1}/{repoid1_path}/{lv1dir1}"
            files_and_folders = fs.ls(base1, detail=True)
            folders = [item["name"].split("/")[-1] for item in files_and_folders if item["type"] == "directory"]
            folders = [f.replace("_qwen", "") for f in folders]

            self.log("=============Has level 2 folders:============")

            if not has_level2:
                # sama seperti sebelumnya: kalau filter OFF, semua folder lolos
                f3 = set(folders)
                self.log("(SKIP) cek level2 folder: OFF -> semua folder level1 dianggap lolos")
            else:
                f3 = set()
                newly_found = set()
                no_level2 = set()
                for folder in folders:
                    if self.stop_flag.is_set():
                        self.log(">> Stopped before finishing level2 scan.")
                        # tetap simpan cache yang mungkin sudah nambah
                        if use_cache and newly_found:
                            cache_set |= newly_found
                            _save_cache_set(cache_path, cache_set)
                            self.log(f">> Cache saved (partial): +{len(newly_found)} new -> total {len(cache_set)}")
                        return

                    # ====== NEW: cek cache dulu ======
                    if use_cache and folder in cache_set:
                        self.log(f"{folder}  (from cache)")
                        f3.add(folder)
                        continue

                    # kalau gak ada di cache -> baru cek repo (logic kamu)
                    lv2 = fs.ls(f"{repotype1}/{repoid1_path}/{lv1dir1}/{folder}", detail=True)
                    lv2folders = [item["name"].split("/")[-1] for item in lv2 if item["type"] == "directory"]
                    if len(lv2folders) > 0:
                        self.log(folder)
                        f3.add(folder)
                        if use_cache:
                            newly_found.add(folder)
                    else:
                        no_level2.add(folder)

                # Print no level2
                self.log("=============No level 2 folders:============")
                for nf in sorted(no_level2):
                    if self.stop_flag.is_set():
                        self.log(">> Stopped while printing no level2.")
                        # tetap simpan cache yang mungkin sudah nambah
                        if use_cache and newly_found:
                            cache_set |= newly_found
                            _save_cache_set(cache_path, cache_set)
                            self.log(f">> Cache saved (partial): +{len(newly_found)} new -> total {len(cache_set)}")
                        return
                    self.log(nf)

                # Save cache after scan
                if use_cache and newly_found:
                    cache_set |= newly_found
                    _save_cache_set(cache_path, cache_set)
                    self.log(f">> Cache saved: +{len(newly_found)} new -> total {len(cache_set)}")

            # Repo2 list
            if self.stop_flag.is_set():
                self.log(">> Stopped before scanning repo2.")
                return

            files_and_folders2 = fs.ls(f"{repotype2}/{repoid2_path}/{lv1dir2}/", detail=True)
            folders2 = [item["name"].split("/")[-1] for item in files_and_folders2 if item["type"] == "directory"]
            folders2 = [f.replace("_qwen", "") for f in folders2]
            f2 = set(folders2)

            self.log("=============In repo 1 but not in repo 2 and has level 2 folders:============")
            diff = f3 - f2
            for df in sorted(diff):
                if self.stop_flag.is_set():
                    self.log(">> Stopped while printing diff.")
                    return
                self.log(df)

            self.log(">> Done.")

        except Exception:
            self.log("!! ERROR !!")
            self.log(traceback.format_exc())


if __name__ == "__main__":
    app = HFDirCompareUI()
    app.mainloop()

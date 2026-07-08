import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class FTIRViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("FTIR Spectra Viewer")

        self.datasets = []

        self.create_gui()

    def create_gui(self):

        left_frame = ttk.Frame(self.root)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        right_frame = ttk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # File controls
        ttk.Button(
            left_frame,
            text="Add XLSX",
            command=self.load_file
        ).pack(fill="x", pady=2)

        ttk.Button(
            left_frame,
            text="Remove",
            command=self.remove_selected
        ).pack(fill="x", pady=2)

        ttk.Button(
            left_frame,
            text="Move Up",
            command=self.move_up
        ).pack(fill="x", pady=2)

        ttk.Button(
            left_frame,
            text="Move Down",
            command=self.move_down
        ).pack(fill="x", pady=2)

        ttk.Separator(left_frame).pack(fill="x", pady=5)

        self.legend_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(
            left_frame,
            text="Show Legend",
            variable=self.legend_var,
            command=self.update_plot
        ).pack(anchor="w")

        self.reverse_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(
            left_frame,
            text="Reverse FTIR Axis",
            variable=self.reverse_var,
            command=self.update_plot
        ).pack(anchor="w")

        # Stack spectra option
        self.stack_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(
            left_frame,
            text="Stack Spectra",
            variable=self.stack_var,
            command=self.update_plot
        ).pack(anchor="w")

        ttk.Label(
            left_frame,
            text="Stack Spacing"
        ).pack(anchor="w", pady=(5, 0))

        self.offset_var = tk.DoubleVar(value=1.2)

        offset_spinbox = ttk.Spinbox(
            left_frame,
            from_=0.1,
            to=10.0,
            increment=0.1,
            textvariable=self.offset_var,
            width=8,
            command=self.update_plot
        )
        offset_spinbox.pack(anchor="w")

        # Update plot when user types a value manually
        self.offset_var.trace_add(
            "write",
            lambda *args: self.update_plot()
        )

        ttk.Button(
            left_frame,
            text="Save Figure",
            command=self.save_figure
        ).pack(fill="x", pady=5)

        ttk.Separator(left_frame).pack(fill="x", pady=5)

        self.listbox = tk.Listbox(left_frame, height=15)
        self.listbox.pack(fill="both", expand=True)

        # Plot
        self.fig, self.ax = plt.subplots(figsize=(8, 5))

        self.canvas = FigureCanvasTkAgg(
            self.fig,
            master=right_frame
        )

        self.canvas.get_tk_widget().pack(
            fill=tk.BOTH,
            expand=True
        )

    def load_file(self):
        filenames = filedialog.askopenfilenames(
            filetypes=[("Excel Files", "*.xlsx *.xls")]
        )

        for filename in filenames:
            try:
                df = pd.read_excel(filename, header=None)

                # Find row containing cm-1
                header_row = None

                for i in range(len(df)):
                    first = str(df.iloc[i, 0]).strip().lower()

                    if "cm" in first:
                        header_row = i
                        break

                if header_row is None:
                    raise ValueError(
                        "Could not find FTIR header row"
                    )

                data = df.iloc[
                    header_row + 1:,
                    :2
                ].copy()

                data.columns = ["cm-1", "%T"]

                data["cm-1"] = pd.to_numeric(
                    data["cm-1"],
                    errors="coerce"
                )

                data["%T"] = pd.to_numeric(
                    data["%T"],
                    errors="coerce"
                )

                data = data.dropna()

                x = data["cm-1"]
                y = data["%T"]

                # Normalize between 0 and 1
                y_norm = (
                    (y - y.min())
                    / (y.max() - y.min())
                )

                name = filename.split("/")[-1]
                name = name.split("\\")[-1]

                self.datasets.append({
                    "name": name,
                    "x": x,
                    "y": y_norm
                })

                self.listbox.insert(
                    tk.END,
                    name
                )

            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Could not load:\n{filename}\n\n{e}"
                )

        self.update_plot()

    def remove_selected(self):
        sel = self.listbox.curselection()

        if not sel:
            return

        idx = sel[0]

        self.listbox.delete(idx)
        self.datasets.pop(idx)

        self.update_plot()

    def move_up(self):
        sel = self.listbox.curselection()

        if not sel:
            return

        idx = sel[0]

        if idx == 0:
            return

        self.datasets[idx], self.datasets[idx - 1] = (
            self.datasets[idx - 1],
            self.datasets[idx]
        )

        self.refresh_listbox(idx - 1)

    def move_down(self):
        sel = self.listbox.curselection()

        if not sel:
            return

        idx = sel[0]

        if idx >= len(self.datasets) - 1:
            return

        self.datasets[idx], self.datasets[idx + 1] = (
            self.datasets[idx + 1],
            self.datasets[idx]
        )

        self.refresh_listbox(idx + 1)

    def refresh_listbox(self, selected):
        self.listbox.delete(0, tk.END)

        for ds in self.datasets:
            self.listbox.insert(
                tk.END,
                ds["name"]
            )

        self.listbox.selection_set(selected)

        self.update_plot()

    def update_plot(self):

        self.ax.clear()

        stacked = self.stack_var.get()

        try:
            offset_amount = float(
                self.offset_var.get()
            )
        except:
            offset_amount = 1.2

        total = len(self.datasets)

        for i, ds in enumerate(self.datasets):

            if stacked:
                # First spectrum at top (common FTIR style)
                offset = (
                    (total - i - 1)
                    * offset_amount
                )

                y_plot = ds["y"] + offset
            else:
                y_plot = ds["y"]

            self.ax.plot(
                ds["x"],
                y_plot,
                linewidth=1.5,
                label=ds["name"]
            )

        self.ax.set_xlabel("Wavenumber (cm⁻¹)")

        if stacked:
            self.ax.set_ylabel("")
            self.ax.set_yticks([])
        else:
            self.ax.set_ylabel("Normalized %T")

        if self.reverse_var.get():
            self.ax.invert_xaxis()

        if self.legend_var.get():
            self.ax.legend()

        self.ax.grid(True, alpha=0.3)

        # Cleaner FTIR style
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)

        self.fig.tight_layout()
        self.canvas.draw()

    def save_figure(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG", "*.png"),
                ("PDF", "*.pdf"),
                ("SVG", "*.svg")
            ]
        )

        if filename:
            self.fig.savefig(
                filename,
                dpi=300,
                bbox_inches="tight"
            )


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x700")

    app = FTIRViewer(root)

    root.mainloop()

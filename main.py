import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import OpenEXR, Imath, array, numpy as np
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import webbrowser

class EXRInspectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 EXR Metadata Inspector (Pro)")
        self.root.geometry("1250x800")
        self.root.configure(bg="#2C2F33")

        self.exr_file = None
        self.header = None
        self.channels = []
        self.width = 0
        self.height = 0
        self.preview_img = None
        self.current_array = None

        # Title
        title = tk.Label(root, text="🔍 EXR Metadata Inspector",
                         font=("Segoe UI", 16, "bold"),
                         fg="white", bg="#2C2F33")
        title.pack(pady=10)

        # Browse
        browse_btn = tk.Button(root, text="📂 Open EXR File",
                               command=self.load_exr,
                               bg="#3498DB", fg="white", relief="flat",
                               font=("Segoe UI", 11, "bold"))
        browse_btn.pack(pady=5)

        # Dropdown
        self.channel_var = tk.StringVar()
        self.channel_menu = ttk.Combobox(root, textvariable=self.channel_var, state="readonly", width=60)
        self.channel_menu.pack(pady=5)
        self.channel_menu.bind("<<ComboboxSelected>>", self.update_preview)

        # View mode (grayscale / false color)
        self.view_mode = tk.StringVar(value="grayscale")
        view_frame = tk.Frame(root, bg="#2C2F33")
        view_frame.pack(pady=3)
        tk.Radiobutton(view_frame, text="Grayscale", variable=self.view_mode, value="grayscale",
                       bg="#2C2F33", fg="white", selectcolor="#23272A",
                       command=self.update_preview).pack(side="left", padx=10)
        tk.Radiobutton(view_frame, text="False Color", variable=self.view_mode, value="falsecolor",
                       bg="#2C2F33", fg="white", selectcolor="#23272A",
                       command=self.update_preview).pack(side="left", padx=10)

        # Buttons
        btn_frame = tk.Frame(root, bg="#2C2F33")
        btn_frame.pack(pady=5)

        export_btn = tk.Button(btn_frame, text="💾 Export Report", command=self.export_report,
                               bg="#2ECC71", fg="white", relief="flat", width=18)
        export_btn.grid(row=0, column=0, padx=5)

        save_btn = tk.Button(btn_frame, text="🖼️ Save Preview", command=self.save_preview,
                             bg="#E67E22", fg="white", relief="flat", width=18)
        save_btn.grid(row=0, column=1, padx=5)

        hist_btn = tk.Button(btn_frame, text="📊 Show Histogram", command=self.show_histogram,
                             bg="#9B59B6", fg="white", relief="flat", width=18)
        hist_btn.grid(row=0, column=2, padx=5)

        # Layout
        content_frame = tk.Frame(root, bg="#2C2F33")
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.output_box = scrolledtext.ScrolledText(content_frame, width=70, height=35,
                                                    bg="#23272A", fg="white",
                                                    font=("Consolas", 10))
        self.output_box.pack(side="left", padx=10, fill="y")

        self.preview_label = tk.Label(content_frame, bg="#2C2F33")
        self.preview_label.pack(side="right", expand=True)

        # Footer credit
        footer = tk.Label(root,
                          text="Created by Dwiky Gilang Imrodhani  |  https://github.com/dwikygilang",
                          font=("Segoe UI", 9),
                          fg="#7289DA", bg="#2C2F33", cursor="hand2", anchor="w")
        footer.pack(side="bottom", anchor="w", padx=10, pady=5)

        # Bind click event
        footer.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/dwikygilang"))


    def load_exr(self):
        filepath = filedialog.askopenfilename(filetypes=[("OpenEXR files", "*.exr")])
        if not filepath:
            return

        try:
            self.exr_file = OpenEXR.InputFile(filepath)
            self.header = self.exr_file.header()
            self.channels = list(self.header["channels"].keys())

            dw = self.header["dataWindow"]
            self.width = dw.max.x - dw.min.x + 1
            self.height = dw.max.y - dw.min.y + 1

            pixel_types = {c: self.header["channels"][c].type.v for c in self.channels}

            report = []
            report.append(f"📁 File       : {filepath}")
            report.append(f"🖼️ Resolution : {self.width} x {self.height}")
            report.append(f"🎚️ Channels   : {len(self.channels)}\n")

            for c in self.channels:
                report.append(f" - {c}  (Type: {pixel_types[c]})")

            report.append("\n📝 Extra Metadata Keys:")
            for k, v in self.header.items():
                if k not in ("channels", "dataWindow", "displayWindow"):
                    report.append(f" - {k}: {v}")

            self.output_box.delete(1.0, tk.END)
            self.output_box.insert(tk.END, "\n".join(report))

            combo_list = ["[AUTO] RGB Preview", "[AUTO] RGBA Preview"] + self.channels
            self.channel_menu["values"] = combo_list
            self.channel_menu.current(0)
            self.update_preview()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open EXR:\n{e}")

    def read_channel(self, ch):
        try:
            pt = Imath.PixelType(Imath.PixelType.FLOAT)
            raw = self.exr_file.channel(ch, pt)
            arr = array.array('f', raw)
            return np.array(arr).reshape(self.height, self.width)
        except Exception:
            return np.zeros((self.height, self.width), np.float32)

    def update_preview(self, event=None):
        if not self.exr_file:
            return

        ch = self.channel_var.get()
        self.current_array = None

        if ch == "[AUTO] RGB Preview":
            rgb = self.get_rgb_image()
            if rgb is not None:
                self.show_image(rgb)
                return
            self.preview_label.config(text="⚠️ No RGB channels found", fg="red")
            return

        if ch == "[AUTO] RGBA Preview":
            rgba = self.get_rgba_image()
            if rgba is not None:
                self.show_image(rgba)
                return
            self.preview_label.config(text="⚠️ No RGBA channels found", fg="red")
            return

        arr = self.read_channel(ch)
        if arr.size == 0:
            self.preview_label.config(text="⚠️ Cannot preview channel", fg="red")
            return

        self.current_array = arr
        mode = self.view_mode.get()

        if mode == "falsecolor":
            arr_norm = self.normalize_f32(arr)
            colored = cm.plasma(arr_norm)
            img = Image.fromarray((colored[:, :, :3] * 255).astype(np.uint8), mode="RGB")
        else:
            arr_norm = self.normalize(arr)
            img = Image.fromarray(arr_norm, mode="L")

        self.show_image(img)

    def get_rgb_image(self):
        grouped = {}
        for ch in self.channels:
            if ch.endswith(".R") or ch.endswith(".G") or ch.endswith(".B"):
                base, suffix = ch.rsplit(".", 1)
                grouped.setdefault(base, {})[suffix] = ch

        for base, chans in grouped.items():
            if all(s in chans for s in ("R", "G", "B")):
                R = self.normalize(self.read_channel(chans["R"]))
                G = self.normalize(self.read_channel(chans["G"]))
                B = self.normalize(self.read_channel(chans["B"]))
                return Image.merge("RGB", [Image.fromarray(R),
                                           Image.fromarray(G),
                                           Image.fromarray(B)])

        if all(c in self.channels for c in ("R", "G", "B")):
            R = self.normalize(self.read_channel("R"))
            G = self.normalize(self.read_channel("G"))
            B = self.normalize(self.read_channel("B"))
            return Image.merge("RGB", [Image.fromarray(R),
                                       Image.fromarray(G),
                                       Image.fromarray(B)])
        return None

    def get_rgba_image(self):
        grouped = {}
        for ch in self.channels:
            if ch.endswith((".R", ".G", ".B", ".A")):
                base, suffix = ch.rsplit(".", 1)
                grouped.setdefault(base, {})[suffix] = ch

        for base, chans in grouped.items():
            if all(s in chans for s in ("R", "G", "B", "A")):
                R = self.normalize(self.read_channel(chans["R"]))
                G = self.normalize(self.read_channel(chans["G"]))
                B = self.normalize(self.read_channel(chans["B"]))
                A = self.normalize(self.read_channel(chans["A"]))
                return Image.merge("RGBA", [Image.fromarray(R),
                                            Image.fromarray(G),
                                            Image.fromarray(B),
                                            Image.fromarray(A)])
        return None

    def normalize(self, arr):
        arr = arr - np.min(arr)
        if np.max(arr) > 0:
            arr = arr / np.max(arr)
        return (arr * 255).astype(np.uint8)

    def normalize_f32(self, arr):
        arr = arr - np.min(arr)
        if np.max(arr) > 0:
            arr = arr / np.max(arr)
        return arr.astype(np.float32)

    def show_image(self, img):
        img.thumbnail((600, 600))
        self.preview_img = ImageTk.PhotoImage(img)
        self.preview_label.config(image=self.preview_img, text="")

    def export_report(self):
        if not self.header:
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if not filepath:
            return
        text = self.output_box.get(1.0, tk.END)
        with open(filepath, "w") as f:
            f.write(text)
        messagebox.showinfo("Success", f"Report saved to {filepath}")

    def save_preview(self):
        if not self.preview_img:
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not filepath:
            return
        img = self.preview_img._PhotoImage__photo
        img.write(filepath, format="png")
        messagebox.showinfo("Success", f"Preview saved to {filepath}")

    def show_histogram(self):
        if self.current_array is None:
            messagebox.showwarning("No Data", "Load a single channel first")
            return
        flat = self.current_array.flatten()
        plt.figure("Histogram")
        plt.hist(flat, bins=256, color="blue", alpha=0.7)
        plt.title("Histogram")
        plt.xlabel("Value")
        plt.ylabel("Frequency")
        plt.show()


if __name__ == "__main__":
    root = tk.Tk()
    app = EXRInspectorApp(root)
    root.mainloop()

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import OpenEXR, Imath, array, numpy as np
from PIL import Image, ImageTk, ImageDraw
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import webbrowser

class EXRInspectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 EXR Inspector Pro Studio")
        self.root.geometry("1400x900")
        self.root.configure(bg="#2C2F33")

        # EXR data
        self.exr_file = None
        self.header = None
        self.channels = []
        self.width = 0
        self.height = 0
        self.preview_pil = None
        self.current_array = None

        # Cache
        self.channel_cache = {}
        self.thumbnail_cache = {}

        # Zoom/Pan
        self.zoom_scale = 1.0
        self.offset_x = 0
        self.offset_y = 0

        # Multi-channel toggle
        self.channel_flags = {"R": tk.IntVar(value=1),
                              "G": tk.IntVar(value=1),
                              "B": tk.IntVar(value=1),
                              "A": tk.IntVar(value=1)}

        # Title
        tk.Label(root, text="🔍 EXR Inspector Pro Studio",
                 font=("Segoe UI", 16, "bold"),
                 fg="white", bg="#2C2F33").pack(pady=10)

        # File Browse
        tk.Button(root, text="📂 Open EXR File", command=self.load_exr,
                  bg="#3498DB", fg="white", relief="flat",
                  font=("Segoe UI", 11, "bold")).pack(pady=5)

        # Channel selection
        self.channel_var = tk.StringVar()
        self.channel_menu = ttk.Combobox(root, textvariable=self.channel_var, state="readonly", width=60)
        self.channel_menu.pack(pady=5)
        self.channel_menu.bind("<<ComboboxSelected>>", self.update_preview)

        # Color mode selection
        self.view_mode = tk.StringVar(value="original")  # default Original
        view_frame = tk.Frame(root, bg="#2C2F33")
        view_frame.pack(pady=3)
        modes = ["Original", "Grayscale", "False Color", "Jet", "Viridis"]
        for m in modes:
            tk.Radiobutton(view_frame, text=m, variable=self.view_mode, value=m.lower(),
                           bg="#2C2F33", fg="white", selectcolor="#23272A",
                           command=self.update_preview).pack(side="left", padx=6)

        # Multi-channel toggle UI
        toggle_frame = tk.Frame(root, bg="#2C2F33")
        toggle_frame.pack(pady=3)
        for ch in ["R","G","B","A"]:
            tk.Checkbutton(toggle_frame, text=ch, variable=self.channel_flags[ch],
                           bg="#2C2F33", fg="white", selectcolor="#23272A",
                           command=self.update_preview).pack(side="left", padx=5)

        # Buttons
        btn_frame = tk.Frame(root, bg="#2C2F33")
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="💾 Export Report", command=self.export_report,
                  bg="#2ECC71", fg="white", relief="flat", width=18).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="🖼️ Save Preview", command=self.save_preview,
                  bg="#E67E22", fg="white", relief="flat", width=18).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="📊 Show Histogram", command=self.show_histogram,
                  bg="#9B59B6", fg="white", relief="flat", width=18).grid(row=0, column=2, padx=5)

        # Layout
        content_frame = tk.Frame(root, bg="#2C2F33")
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Metadata box
        self.output_box = scrolledtext.ScrolledText(content_frame, width=70, height=35,
                                                    bg="#23272A", fg="white",
                                                    font=("Consolas", 10), wrap="none")
        self.output_box.pack(side="left", padx=10, fill="y")

        # Preview canvas
        self.preview_canvas = tk.Canvas(content_frame, bg="#2C2F33", width=600, height=600)
        self.preview_canvas.pack(side="right", expand=True)
        self.preview_canvas.bind("<MouseWheel>", self.zoom)
        self.preview_canvas.bind("<ButtonPress-1>", self.start_pan)
        self.preview_canvas.bind("<B1-Motion>", self.do_pan)
        self.canvas_image_id = None

        # Footer
        footer = tk.Label(root, text="Created by Dwiky Gilang Imrodhani  |  https://github.com/dwikygilang",
                          font=("Segoe UI", 9), fg="#7289DA", bg="#2C2F33", cursor="hand2", anchor="w")
        footer.pack(side="bottom", anchor="w", padx=10, pady=5)
        footer.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/dwikygilang"))

    # =================== EXR Loading ===================
    def load_exr(self):
        filepath = filedialog.askopenfilename(filetypes=[("OpenEXR files", "*.exr")])
        if not filepath: return
        try:
            self.exr_file = OpenEXR.InputFile(filepath)
            self.header = self.exr_file.header()
            self.channels = list(self.header["channels"].keys())
            dw = self.header["dataWindow"]
            self.width = dw.max.x - dw.min.x + 1
            self.height = dw.max.y - dw.min.y + 1

            self.channel_cache.clear()
            self.thumbnail_cache.clear()

            # Metadata
            pixel_types = {c: self.header["channels"][c].type.v for c in self.channels}
            report = [f"📁 File       : {filepath}",
                      f"🖼️ Resolution : {self.width} x {self.height}",
                      f"🎚️ Channels   : {len(self.channels)}\n"]
            for c in self.channels: report.append(f" - {c} (Type: {pixel_types[c]})")
            report.append("\n📝 Extra Metadata Keys:")
            for k, v in self.header.items():
                if k not in ("channels","dataWindow","displayWindow"):
                    report.append(f" - {k}: {v}")
            self.output_box.delete(1.0, tk.END)
            self.output_box.insert(tk.END, "\n".join(report))

            # Channel dropdown: RGBA default
            combo_list = ["[AUTO] RGBA Preview", "[AUTO] RGB Preview"] + self.channels
            self.channel_menu["values"] = combo_list
            if "[AUTO] RGBA Preview" in combo_list:
                self.channel_menu.current(combo_list.index("[AUTO] RGBA Preview"))
            else:
                self.channel_menu.current(0)

            self.update_preview()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open EXR:\n{e}")

    # =================== Channel Reading ===================
    def read_channel(self, ch):
        if ch in self.channel_cache:
            return self.channel_cache[ch]
        try:
            pt = Imath.PixelType(Imath.PixelType.FLOAT)
            raw = self.exr_file.channel(ch, pt)
            arr = array.array('f', raw)
            arr = np.array(arr).reshape(self.height, self.width)
            self.channel_cache[ch] = arr
            return arr
        except:
            arr = np.zeros((self.height, self.width), np.float32)
            self.channel_cache[ch] = arr
            return arr

    # =================== Preview ===================
    def update_preview(self, event=None):
        if not self.exr_file: return
        ch = self.channel_var.get()
        mode = self.view_mode.get()
        key = f"{ch}_{mode}_" + "".join([str(self.channel_flags[c].get()) for c in "RGBA"])
        if key in self.thumbnail_cache:
            self.show_image(self.thumbnail_cache[key])
            return

        img = None
        self.current_array = None

        if ch == "[AUTO] RGBA Preview":
            img = self.get_rgba_image()
            if img is None:
                img = self.get_rgb_image()
        elif ch == "[AUTO] RGB Preview":
            img = self.get_rgb_image()
        else:
            arr = self.read_channel(ch)
            self.current_array = arr
            if mode=="grayscale" or (mode=="original" and arr.ndim==2):
                img = Image.fromarray(self.normalize(arr), mode="L")
            else:
                cmap = {"false color": cm.plasma,"jet":cm.jet,"viridis":cm.viridis}.get(mode, cm.plasma)
                img = Image.fromarray((cmap(self.normalize_f32(arr))[:,:,:3]*255).astype(np.uint8), mode="RGB")

        # Apply multi-channel toggle
        if img.mode in ("RGB","RGBA"):
            arrs = []
            for i,chn in enumerate(img.getbands()):
                if chn=="R" and not self.channel_flags["R"].get(): arrs.append(np.zeros((img.height,img.width),np.uint8))
                elif chn=="G" and not self.channel_flags["G"].get(): arrs.append(np.zeros((img.height,img.width),np.uint8))
                elif chn=="B" and not self.channel_flags["B"].get(): arrs.append(np.zeros((img.height,img.width),np.uint8))
                elif chn=="A" and not self.channel_flags["A"].get(): arrs.append(np.zeros((img.height,img.width),np.uint8))
                else:
                    arrs.append(np.array(img.getchannel(chn)))
            img = Image.merge(img.mode, [Image.fromarray(a) for a in arrs])

        if img.mode=="RGBA" or "A" in self.channels:
            img = self.add_checkerboard(img)

        img.thumbnail((600,600))
        self.thumbnail_cache[key] = img.copy()
        self.show_image(img)

    # =================== RGB/RGBA Helpers ===================
    def get_rgb_image(self):
        grouped = {}
        for ch in self.channels:
            if ch.endswith((".R",".G",".B")):
                base,suffix = ch.rsplit(".",1)
                grouped.setdefault(base,{})[suffix]=ch
        for base,chans in grouped.items():
            if all(s in chans for s in ("R","G","B")):
                R=self.normalize(self.read_channel(chans["R"]))
                G=self.normalize(self.read_channel(chans["G"]))
                B=self.normalize(self.read_channel(chans["B"]))
                return Image.merge("RGB",[Image.fromarray(R),Image.fromarray(G),Image.fromarray(B)])
        if all(c in self.channels for c in ("R","G","B")):
            R=self.normalize(self.read_channel("R"))
            G=self.normalize(self.read_channel("G"))
            B=self.normalize(self.read_channel("B"))
            return Image.merge("RGB",[Image.fromarray(R),Image.fromarray(G),Image.fromarray(B)])
        return None

    def get_rgba_image(self):
        grouped = {}
        for ch in self.channels:
            if ch.endswith((".R",".G",".B",".A")):
                base,suffix = ch.rsplit(".",1)
                grouped.setdefault(base,{})[suffix]=ch
        for base,chans in grouped.items():
            if all(s in chans for s in ("R","G","B","A")):
                R=self.normalize(self.read_channel(chans["R"]))
                G=self.normalize(self.read_channel(chans["G"]))
                B=self.normalize(self.read_channel(chans["B"]))
                A=self.normalize(self.read_channel(chans["A"]))
                return Image.merge("RGBA",[Image.fromarray(R),Image.fromarray(G),Image.fromarray(B),Image.fromarray(A)])
        return None

    # =================== Normalization ===================
    def normalize(self, arr):
        arr=arr-np.min(arr)
        if np.max(arr)>0: arr=arr/np.max(arr)
        return (arr*255).astype(np.uint8)

    def normalize_f32(self, arr):
        arr=arr-np.min(arr)
        if np.max(arr)>0: arr=arr/np.max(arr)
        return arr.astype(np.float32)

    # =================== Checkerboard for transparency ===================
    def add_checkerboard(self, img, size=8):
        bg = Image.new("RGBA", img.size, (0,0,0,0))
        draw = ImageDraw.Draw(bg)
        w,h = img.size
        colors=[(180,180,180,255),(230,230,230,255)]
        for y in range(0,h,size):
            for x in range(0,w,size):
                draw.rectangle([x,y,x+size-1,y+size-1], fill=colors[(x//size + y//size)%2])
        img = Image.alpha_composite(bg,img.convert("RGBA"))
        return img

    # =================== Show Image ===================
    def show_image(self,img):
        self.preview_pil = img.copy()
        self.preview_img = ImageTk.PhotoImage(img)
        self.preview_canvas.delete("all")
        self.canvas_image_id = self.preview_canvas.create_image(300,300,image=self.preview_img)

    # =================== Zoom / Pan ===================
    def zoom(self,event):
        if not self.preview_pil: return
        factor = 1.1 if event.delta>0 else 0.9
        self.zoom_scale *= factor
        self.apply_zoom_pan()

    def start_pan(self,event):
        self.pan_start=(event.x,event.y)

    def do_pan(self,event):
        dx=event.x-self.pan_start[0]
        dy=event.y-self.pan_start[1]
        self.offset_x+=dx
        self.offset_y+=dy
        self.pan_start=(event.x,event.y)
        self.apply_zoom_pan()

    def apply_zoom_pan(self):
        if not self.preview_pil: return
        img=self.preview_pil.copy()
        w,h=img.size
        img=img.resize((int(w*self.zoom_scale),int(h*self.zoom_scale)),Image.LANCZOS)
        self.preview_img=ImageTk.PhotoImage(img)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(300+self.offset_x,300+self.offset_y,image=self.preview_img)

    # =================== Export / Save / Histogram ===================
    def export_report(self):
        if not self.header: return
        filepath=filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text","*.txt")])
        if not filepath: return
        text=self.output_box.get(1.0,tk.END)
        with open(filepath,"w") as f: f.write(text)
        messagebox.showinfo("Success",f"Report saved to {filepath}")

    def save_preview(self):
        if not self.preview_pil: return
        filepath=filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png")])
        if not filepath: return
        self.preview_pil.save(filepath)
        messagebox.showinfo("Success",f"Preview saved to {filepath}")

    def show_histogram(self):
        if self.current_array is None:
            messagebox.showwarning("No Data","Load a single channel first")
            return
        flat=self.current_array.flatten()
        plt.figure("Histogram")
        plt.hist(flat,bins=256,color="blue",alpha=0.7)
        plt.title("Histogram")
        plt.xlabel("Value")
        plt.ylabel("Frequency")
        plt.show()


if __name__=="__main__":
    root=tk.Tk()
    app=EXRInspectorApp(root)
    root.mainloop()

# 🎨 EXR Metadata Inspector Pro

A desktop application for inspecting and visualizing **OpenEXR files**.  
Built with **Python + Tkinter**, this tool is designed for **VFX artists, compositors, and technical directors** who need a quick way to explore EXR metadata, preview channels, and analyze histograms.



## ✨ Features
- 📂 Open any `.exr` file  
- 🔎 Inspect metadata and header information  
- 🎚️ Preview individual channels  
- 🖼️ Auto RGB / RGBA preview  
- 🌈 Grayscale or false-color visualization  
- 📊 Histogram analysis  
- 💾 Export metadata report (TXT)  
- 🖼️ Save channel preview as PNG  
- ✅ Cross-platform (Windows, macOS, Linux)  



## 🛠️ Installation Guide

### 1. Install Python
- Download and install **Python 3.10+** from [python.org](https://www.python.org/downloads/).  
- During installation, check **"Add Python to PATH"**.

### 2. Clone the Repository
```bash
git clone https://github.com/dwikygilang/exr-metadata-inspector.git  
cd exr-metadata-inspector
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 📦 Dependencies
The app requires:
- `numpy`  
- `Pillow`  
- `matplotlib`  
- `OpenEXR`  
- `Imath`  
- `tkinter` (usually included with Python)  

Or install them manually:
```bash
pip install numpy Pillow matplotlib openexr Imath
```

### 4. Run the Application 🚀
```bash
python main.py
```



## 📖 Usage
1. Launch the app.  
2. Click **"📂 Open EXR File"** and select a `.exr` file.  
3. Explore:  
   - Select channels from the dropdown.  
   - Switch between **Grayscale** and **False Color** modes.  
   - Use **[AUTO] RGB Preview** or **[AUTO] RGBA Preview** if available.  

### 🔘 Buttons
- **💾 Export Report** → Save metadata to TXT  
- **🖼️ Save Preview** → Save current preview as PNG  
- **📊 Show Histogram** → View channel histogram  



## 📸 Screenshot
<img width="1247" height="827" alt="image" src="https://github.com/user-attachments/assets/eef6b3eb-5ced-4615-bd4e-e6fe4dc4dc5b" />
<img width="1879" height="831" alt="image" src="https://github.com/user-attachments/assets/b1d6ef0b-b28a-48eb-a43a-4f4a1e7bfd0e" />




## 👨‍💻 Author
Created by **Dwiky Gilang Imrodhani**  
🔗 [GitHub Profile](https://github.com/dwikygilang)

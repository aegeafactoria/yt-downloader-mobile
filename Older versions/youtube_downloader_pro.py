import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from pathlib import Path
import re
import math
import subprocess
import time
from datetime import datetime

# Try to import yt_dlp
try:
    import yt_dlp
except ImportError:
    yt_dlp = None

class ModernDarkTheme:
    """Configuración de colores y estilos para el tema oscuro"""
    BG_COLOR = "#2b2b2b"
    FG_COLOR = "#ffffff"
    ACCENT_COLOR = "#3498db"  # Azul brillante
    ACCENT_HOVER = "#2980b9"
    SECONDARY_BG = "#3c3f41"
    TEXT_AREA_BG = "#1e1e1e"
    SUCCESS_COLOR = "#2ecc71"
    WARNING_COLOR = "#e74c3c"
    
    FONT_MAIN = ('Segoe UI', 10)
    FONT_TITLE = ('Segoe UI', 16, 'bold')
    FONT_BOLD = ('Segoe UI', 10, 'bold')
    FONT_SMALL = ('Segoe UI', 9)

class YouTubeDownloaderPro(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("YouTube Downloader Pro")
        self.geometry("800x700")
        self.configure(bg=ModernDarkTheme.BG_COLOR)
        
        # Variables de estado
        self.download_path = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.download_type = tk.StringVar(value="audio")
        self.playlist_mode = tk.StringVar(value="single")
        self.quality_var = tk.StringVar(value="192")
        self.status_var = tk.StringVar(value="Listo")
        self.progress_var = tk.DoubleVar(value=0)
        self.stats_var = tk.StringVar(value="")
        
        self.is_downloading = False
        
        # Iniciar UI
        self.setup_styles()
        self.create_widgets()
        self.check_dependencies()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar estilos de TTK para que coincidan con el tema oscuro
        style.configure("TFrame", background=ModernDarkTheme.BG_COLOR)
        style.configure("TLabel", background=ModernDarkTheme.BG_COLOR, foreground=ModernDarkTheme.FG_COLOR, font=ModernDarkTheme.FONT_MAIN)
        style.configure("TButton", 
            background=ModernDarkTheme.SECONDARY_BG, 
            foreground=ModernDarkTheme.FG_COLOR, 
            font=ModernDarkTheme.FONT_BOLD,
            borderwidth=1,
            focuscolor=ModernDarkTheme.ACCENT_COLOR
        )
        style.map("TButton", 
            background=[('active', ModernDarkTheme.ACCENT_COLOR)],
            foreground=[('active', 'white')]
        )
        
        style.configure("TRadiobutton", 
            background=ModernDarkTheme.BG_COLOR, 
            foreground=ModernDarkTheme.FG_COLOR, 
            font=ModernDarkTheme.FONT_MAIN,
            indicatorcolor=ModernDarkTheme.BG_COLOR,
            indicatorrelief='flat'
        )
        style.map("TRadiobutton", 
            indicatorcolor=[('selected', ModernDarkTheme.ACCENT_COLOR)]
        )
        
        style.configure("Horizontal.TProgressbar", 
            troughcolor=ModernDarkTheme.SECONDARY_BG, 
            background=ModernDarkTheme.ACCENT_COLOR, 
            borderwidth=0, 
            thickness=10
        )
        
        style.configure("TLabelframe", background=ModernDarkTheme.BG_COLOR, foreground=ModernDarkTheme.FG_COLOR, bordercolor=ModernDarkTheme.SECONDARY_BG)
        style.configure("TLabelframe.Label", background=ModernDarkTheme.BG_COLOR, foreground=ModernDarkTheme.ACCENT_COLOR, font=ModernDarkTheme.FONT_BOLD)

    def create_widgets(self):
        main_container = ttk.Frame(self)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # === HEADER ===
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill='x', pady=(0, 20))
        
        lbl_title = tk.Label(header_frame, text="⬇ YouTube Downloader Pro", 
                             font=ModernDarkTheme.FONT_TITLE, 
                             bg=ModernDarkTheme.BG_COLOR, fg=ModernDarkTheme.ACCENT_COLOR)
        lbl_title.pack(side='left')
        
        lbl_version = tk.Label(header_frame, text="v2.0", 
                               font=ModernDarkTheme.FONT_SMALL, 
                               bg=ModernDarkTheme.BG_COLOR, fg="#888")
        lbl_version.pack(side='left', padx=10, pady=(10,0))

        # === INPUT SECTION ===
        input_frame = ttk.LabelFrame(main_container, text="URLs (Videos o Playlists)")
        input_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # Toolbar para Input
        input_toolbar = ttk.Frame(input_frame)
        input_toolbar.pack(fill='x', padx=5, pady=5)
        
        btn_paste = tk.Button(input_toolbar, text="📋 Pegar Portapapeles", 
                              command=self.paste_from_clipboard,
                              bg=ModernDarkTheme.SECONDARY_BG, fg=ModernDarkTheme.FG_COLOR,
                              relief='flat', padx=10)
        btn_paste.pack(side='left', padx=2)
        
        btn_clear_input = tk.Button(input_toolbar, text="🗑 Limpiar", 
                                    command=lambda: self.url_text.delete("1.0", tk.END),
                                    bg=ModernDarkTheme.SECONDARY_BG, fg=ModernDarkTheme.FG_COLOR,
                                    relief='flat', padx=10)
        btn_clear_input.pack(side='left', padx=2)

        self.url_text = scrolledtext.ScrolledText(input_frame, height=5, 
                                                  bg=ModernDarkTheme.TEXT_AREA_BG, 
                                                  fg=ModernDarkTheme.FG_COLOR,
                                                  insertbackground='white',
                                                  font=('Consolas', 10))
        self.url_text.pack(fill='both', expand=True, padx=5, pady=5)

        # === OPTIONS SECTION ===
        options_container = ttk.Frame(main_container)
        options_container.pack(fill='x', pady=(0, 15))
        
        # Columna 1: Tipo y Calidad
        config_frame = ttk.LabelFrame(options_container, text="Configuración")
        config_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        type_frame = ttk.Frame(config_frame)
        type_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Radiobutton(type_frame, text="🎵 Audio (MP3)", variable=self.download_type, value="audio", command=self.update_quality_options).pack(side='left', padx=10)
        ttk.Radiobutton(type_frame, text="🎬 Video (MP4)", variable=self.download_type, value="video", command=self.update_quality_options).pack(side='left', padx=10)
        
        mode_frame = ttk.Frame(config_frame)
        mode_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Radiobutton(mode_frame, text="📌 Canción / Vídeo único", variable=self.playlist_mode, value="single").pack(side='left', padx=10)
        ttk.Radiobutton(mode_frame, text="📜 Lista de reproducción completa", variable=self.playlist_mode, value="playlist").pack(side='left', padx=10)

        self.quality_frame = ttk.Frame(config_frame)
        self.quality_frame.pack(fill='x', padx=10, pady=5)
        self.update_quality_options() # Inicializar opciones

        # Columna 2: Carpeta
        path_frame = ttk.LabelFrame(options_container, text="Destino")
        path_frame.pack(side='left', fill='both', expand=True)
        
        path_inner = ttk.Frame(path_frame)
        path_inner.pack(fill='x', padx=10, pady=15)
        
        self.entry_path = tk.Entry(path_inner, textvariable=self.download_path, 
                                   bg=ModernDarkTheme.TEXT_AREA_BG, fg=ModernDarkTheme.FG_COLOR,
                                   relief='flat', readonlybackground=ModernDarkTheme.SECONDARY_BG)
        self.entry_path.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        tk.Button(path_inner, text="📂", command=self.browse_folder, 
                  bg=ModernDarkTheme.ACCENT_COLOR, fg='white', relief='flat').pack(side='left')
        
        tk.Button(path_inner, text="Abrir", command=self.open_download_folder, 
                  bg=ModernDarkTheme.SECONDARY_BG, fg='white', relief='flat').pack(side='left', padx=(2,0))

        # === ACTIONS & PROGRESS ===
        action_frame = ttk.Frame(main_container)
        action_frame.pack(fill='x', pady=(0, 10))
        
        self.btn_download = tk.Button(action_frame, text="INICIAR DESCARGA", 
                                      command=self.start_download_thread,
                                      bg=ModernDarkTheme.SUCCESS_COLOR, fg='white',
                                      font=('Segoe UI', 12, 'bold'), relief='flat', height=2)
        self.btn_download.pack(fill='x')
        
        # Progress Info
        progress_info_frame = ttk.Frame(main_container)
        progress_info_frame.pack(fill='x', pady=(10, 5))
        
        lbl_status = tk.Label(progress_info_frame, textvariable=self.status_var, 
                              font=('Segoe UI', 9), anchor='w', bg=ModernDarkTheme.BG_COLOR, fg="#aaa")
        lbl_status.pack(side='left')
        
        lbl_stats = tk.Label(progress_info_frame, textvariable=self.stats_var, 
                             font=('Segoe UI', 9, 'bold'), anchor='e', bg=ModernDarkTheme.BG_COLOR, fg=ModernDarkTheme.ACCENT_COLOR)
        lbl_stats.pack(side='right')
        
        self.progress_bar = ttk.Progressbar(main_container, variable=self.progress_var, maximum=100, style="Horizontal.TProgressbar")
        self.progress_bar.pack(fill='x', pady=(0, 15))

        # === LOG AREA ===
        log_frame = ttk.LabelFrame(main_container, text="Registro")
        log_frame.pack(fill='both', expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, 
                                                  state='disabled',
                                                  bg=ModernDarkTheme.TEXT_AREA_BG, 
                                                  fg="#cccccc",
                                                  font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)

    def log_message(self, message, level="INFO"):
        """Agrega un mensaje al log con timestamp y color"""
        now = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{now}] {message}\n"
        
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, full_msg)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def check_dependencies(self):
        if yt_dlp is None:
            messagebox.showwarning("Falta yt-dlp", "El módulo 'yt-dlp' no está instalado. Instálalo para usar la app.")
            self.log_message("ERROR: yt-dlp no encontrado.", "ERROR")
            self.btn_download.config(state='disabled')
        else:
            self.log_message("Sistema listo. yt-dlp detectado.")

    def paste_from_clipboard(self):
        try:
            data = self.clipboard_get()
            self.url_text.insert(tk.END, data + "\n")
        except:
            pass

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)

    def open_download_folder(self):
        path = self.download_path.get()
        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showerror("Error", "La carpeta no existe")

    def update_quality_options(self):
        # Limpiar frame de calidad
        for widget in self.quality_frame.winfo_children():
            widget.destroy()
            
        tk.Label(self.quality_frame, text="Calidad:", bg=ModernDarkTheme.BG_COLOR, fg=ModernDarkTheme.FG_COLOR).pack(side='left')
        
        if self.download_type.get() == "audio":
            options = [("320 kbps", "320"), ("192 kbps", "192"), ("128 kbps", "128")]
            self.quality_var.set("192")
        else:
            options = [("1080p", "1080"), ("720p", "720"), ("480p", "480")]
            self.quality_var.set("720")
            
        for text, val in options:
            rb = ttk.Radiobutton(self.quality_frame, text=text, variable=self.quality_var, value=val)
            rb.pack(side='left', padx=10)

    # === LOGIC FOR DOWNLOADING ===
    def start_download_thread(self):
        urls = self.url_text.get("1.0", tk.END).strip().splitlines()
        urls = [u.strip() for u in urls if u.strip()]
        
        if not urls:
            messagebox.showwarning("Aviso", "Pega al menos una URL de YouTube.")
            return
            
        if self.is_downloading:
            return
            
        self.is_downloading = True
        self.btn_download.config(state='disabled', text="DESCARGANDO...", bg=ModernDarkTheme.SECONDARY_BG)
        self.progress_var.set(0)
        self.log_message(f"Iniciando descarga de {len(urls)} enlaces...")
        
        threading.Thread(target=self.process_queue, args=(urls,), daemon=True).start()

    def process_queue(self, urls):
        total = len(urls)
        errors = 0
        
        for i, url in enumerate(urls):
            self.status_var.set(f"Procesando ({i+1}/{total}): {url}")
            try:
                if self.download_type.get() == "audio":
                    self.download_audio(url)
                else:
                    self.download_video(url)
                self.log_message(f"✅ Completado: {url}")
            except Exception as e:
                errors += 1
                self.log_message(f"❌ Error en {url}: {str(e)}")
            
        self.is_downloading = False
        self.btn_download.config(state='normal', text="INICIAR DESCARGA", bg=ModernDarkTheme.SUCCESS_COLOR)
        self.status_var.set("Finalizado.")
        self.stats_var.set("")
        self.progress_var.set(100)
        
        if errors > 0:
            messagebox.showwarning("Finalizado", f"Proceso terminado con {errors} errores.")
        else:
            messagebox.showinfo("Éxito", "Todas las descargas completadas.")

    def download_audio(self, url):
        path = self.download_path.get()
        quality = self.quality_var.get()
        is_single = (self.playlist_mode.get() == "single")
        
        opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
            'noplaylist': is_single,
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'android', 'ios'],
                }
            },
            'progress_hooks': [self.progress_hook],
            'ignoreerrors': True,
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    def download_video(self, url):
        path = self.download_path.get()
        quality = self.quality_var.get()
        is_single = (self.playlist_mode.get() == "single")
        
        # Formato: Seleccionar video con altura <= calidad + mejor audio
        fmt = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best"
        
        opts = {
            'format': fmt,
            'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'noplaylist': is_single,
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'android', 'ios'],
                }
            },
            'progress_hooks': [self.progress_hook],
            'ignoreerrors': True,
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            # Calcular porcentaje
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes') or 0
            
            if total > 0:
                percent = (downloaded / total) * 100
                self.progress_var.set(percent)
            
            # Texto de estado
            filename = os.path.basename(d.get('filename', 'video'))
            # Acortar nombre si es muy largo
            if len(filename) > 40:
                filename = filename[:37] + "..."
                
            self.status_var.set(f"Descargando: {filename}")
            
            # Stats (Velocidad, ETA)
            speed_str = d.get('_speed_str', 'N/A')
            eta_str = d.get('_eta_str', 'N/A')
            size_str = d.get('_total_bytes_str') or d.get('_total_bytes_estimate_str') or "N/A"
            
            self.stats_var.set(f"Vel: {speed_str} | ETA: {eta_str} | Tamaño: {size_str}")
            
        elif d['status'] == 'finished':
            self.status_var.set("Procesando/Convirtiendo...")
            self.stats_var.set("")
            self.progress_var.set(100)

if __name__ == "__main__":
    app = YouTubeDownloaderPro()
    app.mainloop()

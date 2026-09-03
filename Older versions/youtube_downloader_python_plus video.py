import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from pathlib import Path
import re

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Audio/Video Downloader")
        self.root.geometry("650x900")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.download_path = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Listo para descargar")
        
        self.setup_ui()
        self.check_dependencies()
    
    def check_dependencies(self):
        """Verificar si yt-dlp está instalado"""
        if yt_dlp is None:
            messagebox.showwarning(
                "Dependencia faltante",
                "yt-dlp no está instalado.\n\n"
                "Instálalo con: pip install yt-dlp\n\n"
                "La aplicación funcionará en modo demo."
            )
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Título
        title_frame = tk.Frame(self.root, bg='#f0f0f0')
        title_frame.pack(pady=15)
        
        title = tk.Label(
            title_frame, 
            text="🎵 YouTube Audio/Video Downloader", 
            font=('Arial', 18, 'bold'),
            bg='#f0f0f0',
            fg='#333'
        )
        title.pack()
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(padx=20, pady=10, fill='both', expand=True)
        
        # URL Input
        url_frame = tk.LabelFrame(main_frame, text="URL(s) del Video o Playlist (una por línea)", padx=10, pady=10)
        url_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        self.url_text = scrolledtext.ScrolledText(
            url_frame, 
            font=('Arial', 11),
            height=6,
            wrap='word'
        )
        self.url_text.pack(fill='both', expand=True)
        
        # Carpeta de destino
        path_frame = tk.LabelFrame(main_frame, text="Carpeta de Destino", padx=10, pady=10)
        path_frame.pack(fill='x', pady=(0, 10))
        
        self.path_entry = tk.Entry(
            path_frame, 
            textvariable=self.download_path,
            font=('Arial', 11),
            state='readonly'
        )
        self.path_entry.pack(side='left', fill='x', expand=True)
        
        browse_btn = tk.Button(
            path_frame,
            text="📁 Explorar",
            command=self.browse_folder,
            bg='#2196F3',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        browse_btn.pack(side='right', padx=(10, 0))
        
        # Tipo de descarga (Audio o Video)
        type_frame = tk.LabelFrame(main_frame, text="Tipo de Descarga", padx=10, pady=10)
        type_frame.pack(fill='x', pady=(0, 10))
        
        self.download_type = tk.StringVar(value="audio")
        
        tk.Radiobutton(
            type_frame,
            text="🎵 Audio (MP3)",
            variable=self.download_type,
            value="audio",
            font=('Arial', 10, 'bold'),
            command=self.update_quality_options
        ).pack(anchor='w')
        
        tk.Radiobutton(
            type_frame,
            text="🎬 Video (MP4)",
            variable=self.download_type,
            value="video",
            font=('Arial', 10, 'bold'),
            command=self.update_quality_options
        ).pack(anchor='w')
        
        # Opciones de calidad
        self.quality_frame = tk.LabelFrame(main_frame, text="Calidad de Audio", padx=10, pady=10)
        self.quality_frame.pack(fill='x', pady=(0, 10))
        
        self.quality_var = tk.StringVar(value="192")
        
        # Frame interno para los radiobuttons de calidad
        self.quality_inner_frame = tk.Frame(self.quality_frame)
        self.quality_inner_frame.pack(fill='x')
        
        self.update_quality_options()
        
        # Barra de progreso
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill='x', pady=(5, 5))
        
        # Estado
        self.status_label = tk.Label(
            main_frame,
            textvariable=self.status_var,
            font=('Arial', 10),
            bg='#f0f0f0'
        )
        self.status_label.pack(pady=(5, 10))
        
        # Botones
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill='x')
        
        self.download_btn = tk.Button(
            button_frame,
            text="⬇️ Descargar Todo",
            command=self.start_download_thread,
            bg='#FF5722',
            fg='white',
            font=('Arial', 12, 'bold'),
            height=2
        )
        self.download_btn.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        self.clear_btn = tk.Button(
            button_frame,
            text="🗑️ Limpiar",
            command=self.clear_form,
            bg='#9E9E9E',
            fg='white',
            font=('Arial', 12, 'bold'),
            height=2
        )
        self.clear_btn.pack(side='right', fill='x', expand=True, padx=(5, 0))
    
    def update_quality_options(self):
        """Actualizar las opciones de calidad según el tipo de descarga"""
        # Limpiar opciones anteriores
        for widget in self.quality_inner_frame.winfo_children():
            widget.destroy()
        
        if self.download_type.get() == "audio":
            self.quality_frame.config(text="Calidad de Audio")
            qualities = [
                ("320 kbps (Mejor)", "320"),
                ("192 kbps (Buena)", "192"),
                ("128 kbps (Estándar)", "128")
            ]
            self.quality_var.set("192")
        else:
            self.quality_frame.config(text="Calidad de Video")
            qualities = [
                ("1080p (Full HD)", "1080"),
                ("720p (HD)", "720"),
                ("480p (SD)", "480"),
                ("360p (Baja)", "360")
            ]
            self.quality_var.set("720")
        
        for text, value in qualities:
            tk.Radiobutton(
                self.quality_inner_frame,
                text=text,
                variable=self.quality_var,
                value=value,
                font=('Arial', 10)
            ).pack(anchor='w')
    
    def browse_folder(self):
        """Seleccionar carpeta de destino"""
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)
    
    def is_valid_youtube_url(self, url):
        """Validar URL de YouTube"""
        youtube_regex = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'((watch\?v=)|(playlist\?list=)|(embed/)|(v/)|(shorts/)|(live/)|.+\?v=)?([^&=%\?]{11,})'
        )
        return youtube_regex.match(url) is not None

    def start_download_thread(self):
        """Validar y empezar el hilo de descarga de la cola."""
        urls_text = self.url_text.get("1.0", tk.END).strip()
        urls = [url.strip() for url in urls_text.splitlines() if url.strip()]

        if not urls:
            messagebox.showwarning("Error", "Por favor, introduce al menos una URL.")
            return

        if not os.path.exists(self.download_path.get()):
            messagebox.showerror("Error", "La carpeta de destino no existe.")
            return

        self.download_btn.config(state='disabled', text="Descargando...")
        self.clear_btn.config(state='disabled')
        
        # Iniciar el proceso de descarga en un hilo separado
        threading.Thread(target=self._process_download_queue, args=(urls,), daemon=True).start()

    def _process_download_queue(self, urls):
        """Procesa una lista de URLs, descargándolas una por una."""
        total_urls = len(urls)
        download_type_text = "audio" if self.download_type.get() == "audio" else "video"
        self.status_var.set(f"Preparando para descargar {total_urls} {download_type_text}(s)...")
        
        has_errors = False
        for i, url in enumerate(urls):
            self.progress_var.set(0)
            self.status_var.set(f"Procesando {i+1}/{total_urls}: {url}")
            
            if not self.is_valid_youtube_url(url):
                print(f"URL inválida, saltando: {url}")
                continue

            try:
                if self.download_type.get() == "audio":
                    self._download_single_audio(url, i + 1, total_urls)
                else:
                    self._download_single_video(url, i + 1, total_urls)
            except Exception as e:
                has_errors = True
                print(f"Error descargando {url}: {e}")
                messagebox.showwarning("Error en Descarga", f"Falló la descarga de:\n{url}\n\nError: {e}\n\nContinuando con el siguiente.")

        # Finalización
        if has_errors:
            self.status_var.set(f"Descarga completada con errores.")
            messagebox.showinfo("Proceso Terminado", "La cola de descargas ha terminado, pero algunas URLs fallaron.")
        else:
            self.status_var.set("¡Todas las descargas completadas con éxito!")
            messagebox.showinfo("Éxito", f"Todos los archivos han sido descargados correctamente.")
        
        self.download_btn.config(state='normal', text="⬇️ Descargar Todo")
        self.clear_btn.config(state='normal')
        self.progress_var.set(0)

    def _download_single_audio(self, url, current_num, total_num):
        """Descarga el audio para una sola URL (puede ser un video o una playlist)."""
        output_path = self.download_path.get()
        quality = self.quality_var.get()
        
        if yt_dlp is None:
            self.simulate_download()
            return

        # Configuración de yt-dlp para audio con mejor compatibilidad
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_path, '%(playlist_index)s - %(title)s.%(ext)s' if 'playlist' in url else '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
            'progress_hooks': [lambda d: self.progress_hook(d, current_num, total_num)],
            'ignoreerrors': True,
            'quiet': False,  # Ver errores
            'no_warnings': False,  # Ver advertencias
            # Opciones adicionales para evitar problemas con YouTube
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def _download_single_video(self, url, current_num, total_num):
        """Descarga el video para una sola URL (puede ser un video o una playlist)."""
        output_path = self.download_path.get()
        quality = self.quality_var.get()
        
        if yt_dlp is None:
            self.simulate_download()
            return

        # Configuración de yt-dlp para video con formatos más flexibles
        ydl_opts = {
            # Formato más flexible y compatible
            'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best',
            'outtmpl': os.path.join(output_path, '%(playlist_index)s - %(title)s.%(ext)s' if 'playlist' in url else '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'progress_hooks': [lambda d: self.progress_hook(d, current_num, total_num)],
            'ignoreerrors': True,
            'quiet': False,  # Cambiado para ver errores
            'no_warnings': False,  # Ver advertencias
            # Opciones adicionales para evitar problemas con YouTube
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def progress_hook(self, d, current_num, total_num):
        """Hook para actualizar el progreso, ahora con contexto de la cola."""
        title = d.get('info_dict', {}).get('title', 'archivo')
        status_prefix = f"Descargando {current_num}/{total_num}: {title[:30]}..."

        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total_bytes:
                percent = (d['downloaded_bytes'] / total_bytes) * 100
                self.progress_var.set(percent)
                self.status_var.set(f"{status_prefix} {percent:.1f}%")
        
        elif d['status'] == 'finished':
            self.progress_var.set(100)
            self.status_var.set(f"Procesando '{title[:40]}...'")

    def simulate_download(self):
        """Simular descarga para modo demo"""
        import time
        self.status_var.set("Descarga simulada iniciada...")
        for i in range(101):
            self.progress_var.set(i)
            self.status_var.set(f"Simulando descarga... {i}%")
            time.sleep(0.03)
        messagebox.showinfo("Demo", "Descarga simulada completada.")

    def clear_form(self):
        """Limpiar formulario"""
        self.url_text.delete("1.0", tk.END)
        self.progress_var.set(0)
        self.status_var.set("Listo para descargar")

def main():
    root = tk.Tk()
    app = YouTubeDownloader(root)
    
    # Centrar ventana
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
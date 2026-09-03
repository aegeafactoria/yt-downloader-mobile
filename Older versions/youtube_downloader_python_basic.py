import tkinter as tk
from tkinter import ttk, filedialog, messagebox
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
        self.root.title("YouTube Audio Downloader")
        self.root.geometry("600x400")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.download_path = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.url_var = tk.StringVar()
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
        title_frame.pack(pady=20)
        
        title = tk.Label(
            title_frame, 
            text="🎵 YouTube Audio Downloader", 
            font=('Arial', 18, 'bold'),
            bg='#f0f0f0',
            fg='#333'
        )
        title.pack()
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(padx=20, pady=10, fill='both', expand=True)
        
        # URL Input
        url_frame = tk.LabelFrame(main_frame, text="URL del Video", padx=10, pady=10)
        url_frame.pack(fill='x', pady=(0, 10))
        
        self.url_entry = tk.Entry(
            url_frame, 
            textvariable=self.url_var,
            font=('Arial', 11),
            width=50
        )
        self.url_entry.pack(side='left', fill='x', expand=True)
        
        # Botón para obtener info
        info_btn = tk.Button(
            url_frame,
            text="ℹ Info",
            command=self.get_video_info,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        info_btn.pack(side='right', padx=(10, 0))
        
        # Información del video
        self.info_frame = tk.LabelFrame(main_frame, text="Información del Video", padx=10, pady=10)
        self.info_frame.pack(fill='x', pady=(0, 10))
        
        self.info_text = tk.Text(self.info_frame, height=4, wrap='word', state='disabled')
        self.info_text.pack(fill='x')
        
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
        
        # Opciones de calidad
        quality_frame = tk.LabelFrame(main_frame, text="Calidad de Audio", padx=10, pady=10)
        quality_frame.pack(fill='x', pady=(0, 10))
        
        self.quality_var = tk.StringVar(value="192")
        qualities = [("320 kbps (Mejor)", "320"), ("192 kbps (Buena)", "192"), ("128 kbps (Estándar)", "128")]
        
        for text, value in qualities:
            tk.Radiobutton(
                quality_frame,
                text=text,
                variable=self.quality_var,
                value=value,
                font=('Arial', 10)
            ).pack(anchor='w')
        
        # Barra de progreso
        progress_frame = tk.Frame(main_frame)
        progress_frame.pack(fill='x', pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            style='TProgressbar'
        )
        self.progress_bar.pack(fill='x')
        
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
            text="🎵 Descargar MP3",
            command=self.start_download,
            bg='#FF5722',
            fg='white',
            font=('Arial', 12, 'bold'),
            height=2
        )
        self.download_btn.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        clear_btn = tk.Button(
            button_frame,
            text="🗑 Limpiar",
            command=self.clear_form,
            bg='#9E9E9E',
            fg='white',
            font=('Arial', 12, 'bold'),
            height=2
        )
        clear_btn.pack(side='right', fill='x', expand=True, padx=(5, 0))
    
    def browse_folder(self):
        """Seleccionar carpeta de destino"""
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)
    
    def get_video_info(self):
        """Obtener información del video"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Error", "Por favor, introduce una URL")
            return
        
        if not self.is_valid_youtube_url(url):
            messagebox.showerror("Error", "URL de YouTube no válida")
            return
        
        def fetch_info():
            try:
                self.status_var.set("Obteniendo información...")
                
                if yt_dlp is None:
                    # Modo demo
                    info = {
                        'title': 'Video de Ejemplo',
                        'uploader': 'Canal de Ejemplo',
                        'duration': 180,
                        'view_count': 1000000
                    }
                else:
                    # Usar yt-dlp real
                    ydl_opts = {'quiet': True}
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                
                # Mostrar información
                self.display_video_info(info)
                self.status_var.set("Información obtenida")
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo obtener la información: {str(e)}")
                self.status_var.set("Error al obtener información")
        
        threading.Thread(target=fetch_info, daemon=True).start()
    
    def display_video_info(self, info):
        """Mostrar información del video"""
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        
        title = info.get('title', 'N/A')
        uploader = info.get('uploader', 'N/A')
        duration = info.get('duration', 0)
        views = info.get('view_count', 0)
        
        duration_str = f"{duration//60}:{duration%60:02d}" if duration else "N/A"
        views_str = f"{views:,}" if views else "N/A"
        
        info_text = f"Título: {title}\n"
        info_text += f"Canal: {uploader}\n"
        info_text += f"Duración: {duration_str}\n"
        info_text += f"Visualizaciones: {views_str}"
        
        self.info_text.insert(1.0, info_text)
        self.info_text.config(state='disabled')
    
    def is_valid_youtube_url(self, url):
        """Validar URL de YouTube"""
        youtube_regex = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        return youtube_regex.match(url) is not None
    
    def start_download(self):
        """Iniciar descarga en un hilo separado"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Error", "Por favor, introduce una URL")
            return
        
        if not self.is_valid_youtube_url(url):
            messagebox.showerror("Error", "URL de YouTube no válida")
            return
        
        if not os.path.exists(self.download_path.get()):
            messagebox.showerror("Error", "La carpeta de destino no existe")
            return
        
        self.download_btn.config(state='disabled', text="Descargando...")
        threading.Thread(target=self.download_audio, args=(url,), daemon=True).start()
    
    def download_audio(self, url):
        """Descargar audio del video"""
        try:
            output_path = self.download_path.get()
            quality = self.quality_var.get()
            
            if yt_dlp is None:
                # Simulación para modo demo
                self.simulate_download()
                return
            
            # Configuración de yt-dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                }],
                'progress_hooks': [self.progress_hook],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.status_var.set("Descargando...")
                ydl.download([url])
            
            self.status_var.set("¡Descarga completada!")
            messagebox.showinfo("Éxito", "Audio descargado correctamente")
            
        except Exception as e:
            self.status_var.set("Error en la descarga")
            messagebox.showerror("Error", f"Error durante la descarga: {str(e)}")
        
        finally:
            self.download_btn.config(state='normal', text="🎵 Descargar MP3")
            self.progress_var.set(0)
    
    def simulate_download(self):
        """Simular descarga para modo demo"""
        import time
        
        for i in range(101):
            self.progress_var.set(i)
            self.status_var.set(f"Descargando... {i}%")
            time.sleep(0.05)
        
        self.status_var.set("¡Descarga simulada completada!")
        messagebox.showinfo("Demo", "Descarga simulada (instala yt-dlp para funcionalidad real)")
    
    def progress_hook(self, d):
        """Hook para actualizar progreso de descarga"""
        if d['status'] == 'downloading':
            if 'total_bytes' in d and d['total_bytes']:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                self.progress_var.set(percent)
                self.status_var.set(f"Descargando... {percent:.1f}%")
        elif d['status'] == 'finished':
            self.progress_var.set(100)
            self.status_var.set("Procesando audio...")
    
    def clear_form(self):
        """Limpiar formulario"""
        self.url_var.set("")
        self.progress_var.set(0)
        self.status_var.set("Listo para descargar")
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state='disabled')

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

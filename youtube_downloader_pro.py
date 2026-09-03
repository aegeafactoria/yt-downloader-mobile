import os
import sys
import threading
import re
import traceback
from pathlib import Path
from datetime import datetime

# Gestor de dependencias y captura global de excepciones tempranas
try:
    import dependency_manager
    if not dependency_manager.is_android():
        def _global_crash_handler(exctype, value, tb):
            err_str = "".join(traceback.format_exception(exctype, value, tb))
            dependency_manager.log_msg(f"[CRASH AL INICIAR]:\n{err_str}")
            dependency_manager.show_native_error_popup("Crash al Iniciar - YouTube Downloader Pro", err_str)
        sys.excepthook = _global_crash_handler
        dependency_manager.ensure_dependencies(auto_install=True)
except Exception as _e:
    pass

# Silence Kivy verbose framework startup logs in the console
os.environ["KIVY_NO_CONSOLELOG"] = "1"

# Try to import yt_dlp
try:
    import yt_dlp
except ImportError:
    yt_dlp = None

# Kivy imports
import kivy
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.utils import platform
from kivy.metrics import dp
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

# KivyMD UIX widgets (importados explícitamente para registro en Kivy Factory y PyInstaller)
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import (
    MDFlatButton,
    MDRoundFlatIconButton,
    MDFillRoundFlatIconButton,
    MDFloatingActionButton,
    MDIconButton,
)
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import OneLineListItem

# Minimum Kivy version required
kivy.require('2.1.0')

# Configure window size on desktop to fit nicely on half the screen
if platform != 'android':
    Window.size = (460, 730)

# Layout using KV language
KV = '''
MDScreen:
    md_bg_color: 0.07, 0.09, 0.13, 1

    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: "YouTube Downloader Pro"
            anchor_title: "left"
            left_action_items: [["youtube", lambda x: None]]
            right_action_items: [["cloud-sync", lambda x: app.show_dependencies_dialog()], ["information-outline", lambda x: app.show_info()]]
            elevation: 2
            md_bg_color: 0.11, 0.14, 0.2, 1
            specific_text_color: 0.02, 0.71, 0.83, 1

        MDBoxLayout:
            orientation: 'vertical'
            padding: dp(10)
            spacing: dp(8)

            # 1. URLs Section Card
            MDCard:
                orientation: 'vertical'
                padding: dp(10)
                spacing: dp(6)
                adaptive_height: True
                md_bg_color: 0.12, 0.15, 0.22, 1
                radius: [12, 12, 12, 12]
                elevation: 2

                MDBoxLayout:
                    orientation: 'horizontal'
                    adaptive_height: True
                    spacing: dp(6)

                    MDIcon:
                        icon: "link-variant"
                        theme_text_color: "Custom"
                        text_color: 0.02, 0.71, 0.83, 1
                        size_hint: None, None
                        size: dp(20), dp(20)
                        pos_hint: {"center_y": .5}

                    MDLabel:
                        text: "URLs de YouTube"
                        theme_text_color: "Custom"
                        text_color: 0.9, 0.9, 0.9, 1
                        font_style: "Body2"
                        bold: True
                        pos_hint: {"center_y": .5}

                    MDFillRoundFlatIconButton:
                        icon: "content-paste"
                        text: "Pegar"
                        font_size: "11sp"
                        md_bg_color: 0.15, 0.23, 0.37, 1
                        text_color: 0.38, 0.71, 0.98, 1
                        icon_color: 0.38, 0.71, 0.98, 1
                        padding: dp(6)
                        on_release: app.paste_from_clipboard()

                    MDRoundFlatIconButton:
                        icon: "trash-can-outline"
                        text: "Limpiar"
                        font_size: "11sp"
                        text_color: 0.94, 0.38, 0.38, 1
                        icon_color: 0.94, 0.38, 0.38, 1
                        line_color: 0.94, 0.38, 0.38, 0.5
                        padding: dp(6)
                        on_release: app.clear_urls()

                MDTextField:
                    id: url_input
                    hint_text: "Pega una o varias URLs (una por línea)..."
                    multiline: True
                    max_height: dp(65)
                    mode: "fill"
                    fill_color: 0.07, 0.09, 0.13, 1
                    font_size: "12sp"
                    active_line: True
                    text_color_normal: 1, 1, 1, 1
                    text_color_focus: 1, 1, 1, 1
                    hint_text_color_normal: 0.5, 0.5, 0.5, 1
                    hint_text_color_focus: 0.02, 0.71, 0.83, 1
                    line_color_focus: 0.02, 0.71, 0.83, 1

            # 2. Config Section Card
            MDCard:
                orientation: 'vertical'
                padding: dp(10)
                spacing: dp(6)
                adaptive_height: True
                md_bg_color: 0.12, 0.15, 0.22, 1
                radius: [12, 12, 12, 12]
                elevation: 2

                MDBoxLayout:
                    orientation: 'horizontal'
                    adaptive_height: True
                    spacing: dp(6)

                    MDIcon:
                        icon: "tune-vertical"
                        theme_text_color: "Custom"
                        text_color: 0.02, 0.71, 0.83, 1
                        size_hint: None, None
                        size: dp(20), dp(20)
                        pos_hint: {"center_y": .5}

                    MDLabel:
                        text: "Configuración"
                        theme_text_color: "Custom"
                        text_color: 0.9, 0.9, 0.9, 1
                        font_style: "Body2"
                        bold: True
                        pos_hint: {"center_y": .5}

                # Row 1: Audio / Video & Quality
                MDBoxLayout:
                    orientation: 'horizontal'
                    adaptive_height: True
                    spacing: dp(8)

                    MDBoxLayout:
                        orientation: 'horizontal'
                        adaptive_width: True
                        spacing: dp(2)
                        MDCheckbox:
                            id: chk_audio
                            group: 'download_type'
                            active: True
                            size_hint: None, None
                            size: dp(28), dp(28)
                            color_active: 0.02, 0.71, 0.83, 1
                            on_active: app.on_type_change("audio", self.active)
                        MDLabel:
                            text: "🎵 MP3"
                            theme_text_color: "Custom"
                            text_color: 0.9, 0.9, 0.9, 1
                            font_size: "12sp"
                            adaptive_size: True
                            pos_hint: {"center_y": .5}

                    MDBoxLayout:
                        orientation: 'horizontal'
                        adaptive_width: True
                        spacing: dp(2)
                        MDCheckbox:
                            id: chk_video
                            group: 'download_type'
                            active: False
                            size_hint: None, None
                            size: dp(28), dp(28)
                            color_active: 0.02, 0.71, 0.83, 1
                            on_active: app.on_type_change("video", self.active)
                        MDLabel:
                            text: "🎬 MP4"
                            theme_text_color: "Custom"
                            text_color: 0.9, 0.9, 0.9, 1
                            font_size: "12sp"
                            adaptive_size: True
                            pos_hint: {"center_y": .5}

                    Widget:

                    MDFillRoundFlatIconButton:
                        id: quality_selector
                        icon: "chevron-down"
                        text: "192 kbps"
                        font_size: "11sp"
                        md_bg_color: 0.18, 0.23, 0.33, 1
                        text_color: 0.02, 0.71, 0.83, 1
                        icon_color: 0.02, 0.71, 0.83, 1
                        padding: dp(4)
                        on_release: app.open_quality_menu()

                # Row 2: Single vs Playlist
                MDBoxLayout:
                    orientation: 'horizontal'
                    adaptive_height: True
                    spacing: dp(8)

                    MDBoxLayout:
                        orientation: 'horizontal'
                        adaptive_width: True
                        spacing: dp(2)
                        MDCheckbox:
                            id: chk_single
                            group: 'playlist_mode'
                            active: True
                            size_hint: None, None
                            size: dp(28), dp(28)
                            color_active: 0.02, 0.71, 0.83, 1
                        MDLabel:
                            text: "📌 Canción / Vídeo"
                            theme_text_color: "Custom"
                            text_color: 0.9, 0.9, 0.9, 1
                            font_size: "12sp"
                            adaptive_size: True
                            pos_hint: {"center_y": .5}

                    MDBoxLayout:
                        orientation: 'horizontal'
                        adaptive_width: True
                        spacing: dp(2)
                        MDCheckbox:
                            id: chk_playlist
                            group: 'playlist_mode'
                            active: False
                            size_hint: None, None
                            size: dp(28), dp(28)
                            color_active: 0.02, 0.71, 0.83, 1
                        MDLabel:
                            text: "📜 Lista completa"
                            theme_text_color: "Custom"
                            text_color: 0.9, 0.9, 0.9, 1
                            font_size: "12sp"
                            adaptive_size: True
                            pos_hint: {"center_y": .5}

            # 3. Destination Section Card
            MDCard:
                orientation: 'vertical'
                padding: dp(10)
                spacing: dp(6)
                adaptive_height: True
                md_bg_color: 0.12, 0.15, 0.22, 1
                radius: [12, 12, 12, 12]
                elevation: 2

                MDBoxLayout:
                    orientation: 'horizontal'
                    adaptive_height: True
                    spacing: dp(6)

                    MDIcon:
                        icon: "folder-download-outline"
                        theme_text_color: "Custom"
                        text_color: 0.02, 0.71, 0.83, 1
                        size_hint: None, None
                        size: dp(20), dp(20)
                        pos_hint: {"center_y": .5}

                    MDLabel:
                        text: "Destino:"
                        theme_text_color: "Custom"
                        text_color: 0.9, 0.9, 0.9, 1
                        font_style: "Body2"
                        bold: True
                        adaptive_width: True
                        pos_hint: {"center_y": .5}

                    MDTextField:
                        id: path_input
                        text: ""
                        hint_text: "Ruta de destino..."
                        mode: "fill"
                        fill_color: 0.07, 0.09, 0.13, 1
                        font_size: "11sp"
                        active_line: True
                        text_color_normal: 1, 1, 1, 1
                        text_color_focus: 1, 1, 1, 1
                        hint_text_color_normal: 0.5, 0.5, 0.5, 1
                        hint_text_color_focus: 0.02, 0.71, 0.83, 1
                        line_color_focus: 0.02, 0.71, 0.83, 1
                        pos_hint: {"center_y": .5}

                    MDIconButton:
                        icon: "folder-search-outline"
                        icon_color: 0.02, 0.71, 0.83, 1
                        md_bg_color: 0.18, 0.23, 0.33, 1
                        size_hint: None, None
                        size: dp(32), dp(32)
                        pos_hint: {"center_y": .5}
                        on_release: app.browse_folder()

            # 4. Action Buttons (Download & Stop)
            MDBoxLayout:
                orientation: 'horizontal'
                spacing: dp(8)
                adaptive_height: True

                MDFillRoundFlatIconButton:
                    id: btn_download
                    icon: "download"
                    text: "INICIAR DESCARGA"
                    md_bg_color: 0.06, 0.78, 0.54, 1
                    text_color: 1, 1, 1, 1
                    icon_color: 1, 1, 1, 1
                    font_size: "13sp"
                    bold: True
                    size_hint_x: 0.72
                    padding: dp(10)
                    on_release: app.start_download()

                MDFillRoundFlatIconButton:
                    id: btn_stop
                    icon: "stop-circle"
                    text: "PARAR"
                    md_bg_color: (0.85, 0.22, 0.22, 1) if not self.disabled else (0.2, 0.23, 0.3, 0.5)
                    text_color: (1, 1, 1, 1) if not self.disabled else (0.5, 0.5, 0.5, 1)
                    icon_color: (1, 1, 1, 1) if not self.disabled else (0.5, 0.5, 0.5, 1)
                    font_size: "13sp"
                    bold: True
                    size_hint_x: 0.28
                    padding: dp(10)
                    disabled: True
                    on_release: app.stop_download()

            # 5. Progress Info Section Card
            MDCard:
                orientation: 'vertical'
                padding: dp(8)
                spacing: dp(6)
                adaptive_height: True
                md_bg_color: 0.1, 0.12, 0.18, 1
                radius: [12, 12, 12, 12]
                elevation: 2

                MDBoxLayout:
                    orientation: 'horizontal'
                    adaptive_height: True
                    
                    MDLabel:
                        id: status_label
                        text: "Listo para iniciar"
                        theme_text_color: "Custom"
                        text_color: 0.7, 0.7, 0.7, 1
                        font_style: "Caption"
                        font_size: "11sp"
                        halign: "left"
                        
                    MDLabel:
                        id: stats_label
                        text: ""
                        theme_text_color: "Custom"
                        text_color: 0.02, 0.71, 0.83, 1
                        font_style: "Caption"
                        font_size: "11sp"
                        bold: True
                        halign: "right"

                MDProgressBar:
                    id: progress_bar
                    value: 0
                    color: 0.02, 0.71, 0.83, 1

            # 6. Log Console Card
            MDCard:
                orientation: 'vertical'
                padding: dp(8)
                spacing: dp(4)
                size_hint_y: 1
                md_bg_color: 0.05, 0.07, 0.1, 1
                radius: [12, 12, 12, 12]
                elevation: 2

                MDBoxLayout:
                    orientation: 'horizontal'
                    adaptive_height: True
                    spacing: dp(6)

                    MDIcon:
                        icon: "console"
                        theme_text_color: "Custom"
                        text_color: 0.5, 0.5, 0.5, 1
                        size_hint: None, None
                        size: dp(16), dp(16)

                    MDLabel:
                        text: "Consola de Actividad"
                        theme_text_color: "Custom"
                        text_color: 0.5, 0.5, 0.5, 1
                        font_style: "Caption"
                        font_size: "10sp"
                        bold: True

                ScrollView:
                    id: log_scroll
                    do_scroll_x: False
                    
                    MDLabel:
                        id: log_text
                        text: ""
                        font_name: "Roboto"
                        font_size: "10sp"
                        theme_text_color: "Custom"
                        text_color: 0.75, 0.85, 0.95, 1
                        size_hint_y: None
                        height: self.texture_size[1]
                        text_size: self.width, None
                        valign: "top"
'''

class YTDownloaderApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        
        self.dialog = None
        self.menu = None
        self.is_downloading = False
        self.cancel_requested = False
        
        return Builder.load_string(KV)

    def on_start(self):
        # Set default path
        self.root.ids.path_input.text = self.get_default_path()
        
        # Check permissions on Android
        self.check_android_permissions()
        
        # Log system status
        if yt_dlp is None:
            self.append_log("⚠️ ADVERTENCIA: Módulo 'yt-dlp' no instalado en este entorno de Python.")
            self.append_log("Para probar localmente, instálalo con: pip install yt-dlp")
        else:
            self.append_log("ℹ️ Sistema listo. yt-dlp cargado correctamente.")

        # Diagnóstico y comprobación de actualizaciones en Desktop
        if platform != 'android':
            try:
                import dependency_manager
                ff_ok, ff_path = dependency_manager.check_ffmpeg()
                if ff_ok:
                    self.append_log(f"🎬 FFmpeg detectado: {os.path.basename(ff_path)}")
                else:
                    self.append_log("⚠️ FFmpeg no encontrado en PATH del sistema. Es recomendable para conversiones.")

                if not dependency_manager.is_frozen():
                    threading.Thread(target=self._check_updates_background, daemon=True).start()
                else:
                    self.append_log("✨ Aplicación iniciada en modo ejecutable (.EXE).")
            except Exception as e:
                self.append_log(f"⚠️ Nota de diagnóstico: {str(e)}")

    def _check_updates_background(self):
        try:
            import dependency_manager
            if dependency_manager.is_frozen():
                return
            outdated = dependency_manager.check_outdated_dependencies(check_only_critical=True)
            if outdated:
                for item in outdated:
                    self.append_log(
                        f"💡 Actualización disponible para {item['name']}: "
                        f"{item['installed_version']} -> {item['latest_version']}. "
                        f"(Toca el icono de nube en la barra superior para actualizar)"
                    )
        except Exception:
            pass

    def get_default_path(self):
        if platform == 'android':
            return "/storage/emulated/0/Download"
        else:
            return str(Path.home() / "Downloads")

    def check_android_permissions(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                def callback(permissions, results):
                    if all(results):
                        self.append_log("✅ Permisos de almacenamiento concedidos.")
                    else:
                        self.append_log("⚠️ Advertencia: Algunos permisos fueron denegados. Las descargas pueden fallar.")
                
                request_permissions([
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ], callback)
            except Exception as e:
                self.append_log(f"⚠️ Error al solicitar permisos Android: {str(e)}")

    def append_log(self, message):
        now = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{now}] {message}\n"
        
        def _update(dt):
            self.root.ids.log_text.text += full_msg
            # Scroll to bottom
            self.root.ids.log_scroll.scroll_y = 0
        Clock.schedule_once(_update)

    def set_status(self, text):
        Clock.schedule_once(lambda dt: setattr(self.root.ids.status_label, 'text', text))

    def set_stats(self, text):
        Clock.schedule_once(lambda dt: setattr(self.root.ids.stats_label, 'text', text))

    def set_progress(self, val):
        Clock.schedule_once(lambda dt: setattr(self.root.ids.progress_bar, 'value', val))

    def show_alert(self, title, text):
        def _show(dt):
            if self.dialog:
                self.dialog.dismiss()
            self.dialog = MDDialog(
                title=title,
                text=text,
                buttons=[
                    MDFlatButton(
                        text="ACEPTAR",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=lambda x: self.dialog.dismiss()
                    )
                ],
            )
            self.dialog.open()
        Clock.schedule_once(_show)

    def paste_from_clipboard(self):
        try:
            clipboard_text = Clipboard.paste()
            if clipboard_text:
                current_text = self.root.ids.url_input.text
                if current_text.strip():
                    self.root.ids.url_input.text = current_text.strip() + "\n" + clipboard_text
                else:
                    self.root.ids.url_input.text = clipboard_text
                self.append_log("📋 Enlace pegado desde el portapapeles.")
            else:
                self.show_alert("Aviso", "El portapapeles está vacío.")
        except Exception as e:
            self.append_log(f"⚠️ Error al pegar: {str(e)}")

    def clear_urls(self):
        self.root.ids.url_input.text = ""
        self.append_log("🗑 Lista de URLs limpiada.")

    def on_type_change(self, download_type, is_active):
        if not is_active:
            return
        
        if download_type == "audio":
            self.root.ids.quality_selector.text = "192 kbps"
        else:
            self.root.ids.quality_selector.text = "720p"
            
        self.append_log(f"⚙️ Formato cambiado a: {download_type.upper()}")

    def open_quality_menu(self):
        is_audio = self.root.ids.chk_audio.active
        if is_audio:
            items_list = ["320 kbps", "192 kbps", "128 kbps"]
        else:
            items_list = ["1080p", "720p", "480p"]

        menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": item,
                "on_release": lambda x=item: self.set_quality(x),
            } for item in items_list
        ]

        if self.menu:
            self.menu.dismiss()

        self.menu = MDDropdownMenu(
            caller=self.root.ids.quality_selector,
            items=menu_items,
            width=dp(150),
        )
        self.menu.open()

    def set_quality(self, text_val):
        self.root.ids.quality_selector.text = text_val
        self.menu.dismiss()
        self.append_log(f"⚙️ Calidad seleccionada: {text_val}")

    def browse_folder(self):
        if platform == 'android':
            self.show_alert("Destino en Android", "En dispositivos móviles las descargas se guardan en la carpeta pública 'Download'.")
            return

        try:
            # Import plyer at runtime for desktop folder selection
            from plyer import filechooser
            paths = filechooser.choose_dir(title="Seleccionar carpeta de descarga")
            if paths and len(paths) > 0:
                self.root.ids.path_input.text = paths[0]
                self.append_log(f"📂 Carpeta destino cambiada a: {paths[0]}")
        except Exception as e:
            self.append_log(f"⚠️ Error al abrir selector de carpetas: {str(e)}")
            self.append_log("Puedes escribir la ruta de la carpeta directamente en el campo de texto.")

    def start_download(self):
        if self.is_downloading:
            return

        urls = self.root.ids.url_input.text.strip().splitlines()
        urls = [u.strip() for u in urls if u.strip()]

        if not urls:
            self.show_alert("Aviso", "Introduce al menos una URL válida.")
            return

        self.is_downloading = True
        self.cancel_requested = False
        self.root.ids.btn_download.disabled = True
        self.root.ids.btn_download.icon = "sync"
        self.root.ids.btn_download.text = "DESCARGANDO..."
        self.root.ids.btn_stop.disabled = False
        self.root.ids.btn_stop.text = "PARAR"
        self.set_progress(0)
        self.append_log(f"🚀 Iniciando descarga de {len(urls)} enlace(s)...")

        # Start downloading in a separate background thread
        threading.Thread(target=self.process_queue, args=(urls,), daemon=True).start()

    def stop_download(self):
        if not self.is_downloading:
            return
        self.cancel_requested = True
        self.root.ids.btn_stop.disabled = True
        self.root.ids.btn_stop.text = "PARANDO..."
        self.set_status("Deteniendo descarga...")
        self.append_log("🛑 Solicitud de parada enviada por el usuario...")

    def process_queue(self, urls):
        total = len(urls)
        errors = 0
        was_cancelled = False

        # Retrieve configuration
        is_audio = self.root.ids.chk_audio.active
        is_single = self.root.ids.chk_single.active
        quality_str = self.root.ids.quality_selector.text
        
        # Convert quality text
        if is_audio:
            # "192 kbps" -> "192"
            quality = quality_str.split()[0]
        else:
            # "720p" -> "720"
            quality = quality_str.replace("p", "")

        path = self.root.ids.path_input.text.strip()
        if not path:
            path = self.get_default_path()

        # Ensure directory exists (desktop)
        if platform != 'android':
            os.makedirs(path, exist_ok=True)

        for i, url in enumerate(urls):
            if self.cancel_requested:
                was_cancelled = True
                break

            self.set_status(f"Descargando ({i+1}/{total})...")
            self.append_log(f"⬇️ Descargando enlace {i+1} de {total}: {url}")
            
            try:
                if is_audio:
                    self.download_audio(url, path, quality, noplaylist=is_single)
                else:
                    self.download_video(url, path, quality, noplaylist=is_single)
                self.append_log(f"✅ Descarga exitosa: {url}")
            except Exception as e:
                if self.cancel_requested or "CANCELADO_POR_USUARIO" in str(e):
                    was_cancelled = True
                    self.append_log(f"🛑 Descarga cancelada por el usuario.")
                    break
                else:
                    errors += 1
                    self.append_log(f"❌ Error en {url}: {str(e)}")

        self.is_downloading = False
        self.cancel_requested = False

        # Reset UI elements safely on main thread
        def _finish_ui(dt):
            self.root.ids.btn_download.disabled = False
            self.root.ids.btn_download.icon = "download"
            self.root.ids.btn_download.text = "INICIAR DESCARGA"
            self.root.ids.btn_stop.disabled = True
            self.root.ids.btn_stop.text = "PARAR"
            
            if was_cancelled:
                self.root.ids.status_label.text = "Proceso cancelado."
                self.root.ids.stats_label.text = ""
                self.show_alert("Cancelado", "El proceso de descarga ha sido detenido por el usuario.")
            else:
                self.root.ids.status_label.text = "Finalizado."
                self.root.ids.stats_label.text = ""
                self.root.ids.progress_bar.value = 100
                
                if errors > 0:
                    self.show_alert("Finalizado", f"Descargas finalizadas con {errors} error(es). Revisa la consola de registro.")
                else:
                    self.show_alert("Éxito", "Todas las descargas se han completado con éxito.")

        Clock.schedule_once(_finish_ui)

    def download_audio(self, url, path, quality, noplaylist=True):
        if not yt_dlp:
            raise Exception("La librería yt-dlp no está instalada.")

        # Comprobar disponibilidad de FFmpeg
        ff_ok = False
        ff_dir = None
        try:
            import dependency_manager
            ff_ok, ff_path = dependency_manager.check_ffmpeg()
            if ff_ok and ff_path:
                ff_dir = os.path.dirname(ff_path)
        except Exception:
            pass

        opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
            'noplaylist': noplaylist,
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'android', 'ios'],
                }
            },
            'progress_hooks': [self.progress_hook],
            'logger': YtDlpLogger(self),
            'ignoreerrors': False,
            'nocheckcertificate': True,
        }

        if ff_ok:
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }]
            if ff_dir:
                opts['ffmpeg_location'] = ff_dir

        with yt_dlp.YoutubeDL(opts) as ydl:
            res = ydl.download([url])
            if res != 0:
                raise Exception(f"Código de error de descarga: {res}")

    def download_video(self, url, path, quality, noplaylist=True):
        if not yt_dlp:
            raise Exception("La librería yt-dlp no está instalada.")

        # Comprobar disponibilidad de FFmpeg
        ff_ok = False
        ff_dir = None
        try:
            import dependency_manager
            ff_ok, ff_path = dependency_manager.check_ffmpeg()
            if ff_ok and ff_path:
                ff_dir = os.path.dirname(ff_path)
        except Exception:
            pass

        if ff_ok:
            fmt = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best"
        else:
            fmt = f"best[height<={quality}]/best"

        opts = {
            'format': fmt,
            'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
            'noplaylist': noplaylist,
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'android', 'ios'],
                }
            },
            'progress_hooks': [self.progress_hook],
            'logger': YtDlpLogger(self),
            'ignoreerrors': False,
            'nocheckcertificate': True,
        }

        if ff_ok:
            opts['merge_output_format'] = 'mp4'
            if ff_dir:
                opts['ffmpeg_location'] = ff_dir

        with yt_dlp.YoutubeDL(opts) as ydl:
            res = ydl.download([url])
            if res != 0:
                raise Exception(f"Código de error de descarga: {res}")

    def progress_hook(self, d):
        if self.cancel_requested:
            raise Exception("CANCELADO_POR_USUARIO")

        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes') or 0

            if total > 0:
                percent = (downloaded / total) * 100
                self.set_progress(percent)

            filename = os.path.basename(d.get('filename', 'video'))
            if len(filename) > 30:
                filename = filename[:27] + "..."

            self.set_status(f"Descargando: {filename}")

            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            size = d.get('_total_bytes_str') or d.get('_total_bytes_estimate_str') or 'N/A'

            self.set_stats(f"Vel: {speed} | ETA: {eta} | Tam: {size}")

        elif d['status'] == 'finished':
            self.set_status("Procesando / Convirtiendo...")
            self.set_stats("")
            self.set_progress(100)

    def show_info(self):
        info_text = (
            "YouTube Downloader Pro v2.0\n\n"
            "Desarrollado en Python con KivyMD.\n"
            "Utiliza la librería yt-dlp para descargar archivos.\n\n"
            "En Android, los archivos de audio MP3 y vídeo MP4 se guardan automáticamente en tu carpeta pública de descargas (Download)."
        )
        self.show_alert("Información", info_text)

    def show_dependencies_dialog(self):
        try:
            import dependency_manager
            status = dependency_manager.verify_all_dependencies()
            ff_ok, ff_path = dependency_manager.check_ffmpeg()

            lines = ["[b]Diagnóstico de Dependencias:[/b]\n"]
            for name, info in status.items():
                icon = "•"
                ver = f"v{info['version']}" if info['installed'] else "Faltante"
                lines.append(f"{icon} [b]{name}[/b]: {ver}")

            ff_desc = f"Encontrado ({os.path.basename(ff_path)})" if ff_ok else "No encontrado en PATH"
            lines.append(f"\n• [b]FFmpeg[/b]: {ff_desc}")

            if dependency_manager.is_frozen():
                lines.append("\n[size=12sp](Ejecutando como binario .EXE. Todas las dependencias están integradas.)[/size]")
            elif platform == 'android':
                lines.append("\n[size=12sp](En Android las librerías van integradas en la aplicación)[/size]")

            content_text = "\n".join(lines)

            if platform != 'android' and not dependency_manager.is_frozen():
                def _do_update(x):
                    self.dialog.dismiss()
                    self.start_dependency_update()

                buttons = [
                    MDFlatButton(
                        text="CERRAR",
                        on_release=lambda x: self.dialog.dismiss()
                    ),
                    MDFlatButton(
                        text="ACTUALIZAR YT-DLP",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=_do_update
                    )
                ]
            else:
                buttons = [
                    MDFlatButton(
                        text="CERRAR",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=lambda x: self.dialog.dismiss()
                    )
                ]

            if self.dialog:
                self.dialog.dismiss()

            self.dialog = MDDialog(
                title="Sincronización y Dependencias",
                text=content_text,
                buttons=buttons
            )
            self.dialog.open()
        except Exception as e:
            self.show_alert("Error", f"No se pudo consultar el estado: {str(e)}")

    def start_dependency_update(self):
        self.append_log("🔄 Iniciando proceso de actualización de yt-dlp...")
        self.set_status("Actualizando componentes...")

        def _worker():
            try:
                import dependency_manager
                success, output = dependency_manager.upgrade_ytdlp(
                    on_output=lambda line: self.append_log(f"📦 {line.strip()}")
                )

                def _notify(dt):
                    self.set_status("Sistema listo.")
                    if success:
                        global yt_dlp
                        try:
                            import importlib
                            if yt_dlp:
                                importlib.reload(yt_dlp)
                            else:
                                import yt_dlp
                        except Exception:
                            pass
                        self.append_log("✅ ¡yt-dlp ha sido actualizado exitosamente!")
                        self.show_alert("Actualización Completada", "yt-dlp se ha actualizado correctamente a la última versión disponible en PyPI.")
                    else:
                        self.append_log("❌ Error durante la actualización de yt-dlp.")
                        self.show_alert("Error", "No se pudo completar la actualización. Revisa la consola de registros.")
                Clock.schedule_once(_notify)
            except Exception as e:
                Clock.schedule_once(lambda dt: self.append_log(f"❌ Error en actualización: {str(e)}"))

        threading.Thread(target=_worker, daemon=True).start()


class YtDlpLogger:
    def __init__(self, app):
        self.app = app

    def debug(self, msg):
        # Filtrar mensajes de depuración muy ruidosos pero dejar pasar información útil
        if msg.startswith('[download]'):
            pass
        elif 'Extracting URL' in msg or 'Downloading webpage' in msg:
            pass

    def info(self, msg):
        pass

    def warning(self, msg):
        if self.app and msg:
            self.app.append_log(f"⚠️ {msg}")

    def error(self, msg):
        if self.app and msg:
            self.app.append_log(f"❌ {msg}")

if __name__ == "__main__":
    try:
        YTDownloaderApp().run()
    except Exception as e:
        import traceback
        try:
            import dependency_manager
            dependency_manager.pause_and_exit(
                1,
                f"Error crítico al ejecutar YouTube Downloader Pro:\n{str(e)}\n\nTraza:\n{traceback.format_exc()}"
            )
        except Exception:
            print(f"Error crítico: {e}")
            traceback.print_exc()
            input("Presiona [ENTER] para salir...")
            sys.exit(1)

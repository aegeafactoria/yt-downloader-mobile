"""
Entry point for Buildozer / Android APK packaging and generic execution.
Lanza la aplicación YouTube Downloader Pro desde youtube_downloader_pro.py
con verificación, auto-instalación previa y protección contra cierres silenciosos.
"""
import sys
import traceback
import dependency_manager

if __name__ == "__main__":
    try:
        # Verifica e instala automáticamente dependencias faltantes sólo en Desktop
        if not dependency_manager.is_android():
            dependency_manager.ensure_dependencies(auto_install=True, pause_on_fail=True)

        from youtube_downloader_pro import YTDownloaderApp
        YTDownloaderApp().run()
    except Exception as e:
        error_details = f"Excepción crítica al iniciar la aplicación:\n{str(e)}\n\nTraza completa:\n{traceback.format_exc()}"
        print(error_details)

        # Guardar log en el almacenamiento del dispositivo Android para diagnóstico
        try:
            for log_path in [
                "/storage/emulated/0/Download/ytdownloader_error.log",
                "/sdcard/Download/ytdownloader_error.log",
                "/storage/emulated/0/ytdownloader_error.log",
                "startup_crash.log"
            ]:
                try:
                    with open(log_path, "w", encoding="utf-8") as f:
                        f.write(error_details)
                    break
                except Exception:
                    pass
        except Exception:
            pass

        if not dependency_manager.is_android():
            dependency_manager.pause_and_exit(1, error_details)
        else:
            # En Android, mostrar una pantalla nativa de Kivy con el error exacto
            # para que la aplicación NO se cierre sola y el usuario pueda leer la traza
            try:
                from kivy.app import App
                from kivy.uix.boxlayout import BoxLayout
                from kivy.uix.scrollview import ScrollView
                from kivy.uix.label import Label
                from kivy.uix.button import Button

                class EmergencyErrorApp(App):
                    def build(self):
                        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
                        title = Label(
                            text="⚠️ ERROR AL INICIAR LA APLICACIÓN",
                            font_size="16sp",
                            bold=True,
                            color=(1, 0.3, 0.3, 1),
                            size_hint_y=None,
                            height=40
                        )
                        layout.add_widget(title)

                        scroll = ScrollView(size_hint=(1, 1))
                        lbl = Label(
                            text=error_details,
                            font_size="11sp",
                            color=(1, 1, 1, 1),
                            size_hint_y=None,
                            halign="left",
                            valign="top"
                        )
                        lbl.bind(texture_size=lambda instance, val: setattr(instance, 'height', val[1]))
                        lbl.bind(width=lambda instance, val: setattr(instance, 'text_size', (val, None)))
                        scroll.add_widget(lbl)
                        layout.add_widget(scroll)

                        btn = Button(
                            text="CERRAR",
                            size_hint_y=None,
                            height=50,
                            background_color=(0.8, 0.2, 0.2, 1)
                        )
                        btn.bind(on_release=lambda x: sys.exit(1))
                        layout.add_widget(btn)

                        return layout

                EmergencyErrorApp().run()
            except Exception as crash_err:
                print(f"No se pudo lanzar EmergencyErrorApp: {crash_err}")


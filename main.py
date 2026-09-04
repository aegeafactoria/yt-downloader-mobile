"""
Entry point for Buildozer / Android APK packaging and generic execution.
Lanza la aplicación YouTube Downloader Pro desde youtube_downloader_pro.py
con verificación, auto-instalación previa y protección contra cierres silenciosos.
"""
import sys
import traceback
import dependency_manager

def log_android_crash(err_text):
    print("FATAL ANDROID STARTUP EXCEPTION:\n", err_text)
    for p in [
        "/storage/emulated/0/Download/yt_downloader_crash.log",
        "/sdcard/Download/yt_downloader_crash.log"
    ]:
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write(err_text)
            break
        except Exception:
            pass

sys.excepthook = lambda exctype, value, tb: log_android_crash("".join(traceback.format_exception(exctype, value, tb)))

if __name__ == "__main__":
    try:
        # Verifica e instala automáticamente dependencias faltantes sólo en Desktop
        if not dependency_manager.is_android():
            dependency_manager.ensure_dependencies(auto_install=True, pause_on_fail=True)

        from youtube_downloader_pro import YTDownloaderApp
        YTDownloaderApp().run()
    except Exception as e:
        error_details = f"Excepción crítica al iniciar la aplicación:\n{str(e)}\n\nTraza completa:\n{traceback.format_exc()}"
        log_android_crash(error_details)
        if not dependency_manager.is_android():
            dependency_manager.pause_and_exit(1, error_details)

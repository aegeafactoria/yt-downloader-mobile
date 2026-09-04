"""
Gestor de Dependencias y Diagnóstico para YouTube Downloader Pro.
Verifica, instala y actualiza automáticamente las librerías necesarias con control
estricto de versiones compatibles (evitando versiones incompatibles como KivyMD 2.0+),
registra errores en startup.log y evita el cierre repentino de la ventana de CMD.
Soporta ejecución en desarrollo, entorno virtual, Android y .EXE compilado (PyInstaller).
"""

import sys
import os
import shutil
import subprocess
import json
import urllib.request
import re
import traceback
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Callable

# Asegurar compatibilidad de salida UTF-8 en consolas Windows
if hasattr(sys.stdout, "reconfigure") and sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure") and sys.stderr is not None:
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Determinar directorio base (compatible con PyInstaller y ejecución directa)
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_FILE_PATH = os.path.join(BASE_DIR, "startup.log")


def version_tuple(ver_str: str) -> tuple:
    """Convierte una cadena de versión semántica (ej. '1.2.0') en tupla numérica (1, 2, 0)."""
    try:
        nums = re.findall(r"\d+", str(ver_str))
        return tuple(map(int, nums[:3]))
    except Exception:
        return (0, 0, 0)


def is_frozen() -> bool:
    """Comprueba si la app se ejecuta empaquetada como binario compilado (.EXE con PyInstaller)."""
    return getattr(sys, "frozen", False)


def is_android() -> bool:
    """Comprueba si la app se está ejecutando en el entorno Android de Kivy."""
    if "ANDROID_ARGUMENT" in os.environ or "PYTHON_SERVICE_ARGUMENT" in os.environ or sys.platform == "android":
        return True
    try:
        from kivy.utils import platform
        return platform == "android"
    except Exception:
        return False


def log_msg(msg: str, also_print: bool = True):
    """Guarda un mensaje en startup.log con timestamp y opcionalmente lo muestra por pantalla."""
    if also_print and sys.stdout is not None:
        try:
            print(msg)
        except Exception:
            pass
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE_PATH, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"[{now}] {msg}\n")
    except Exception:
        pass


def show_native_error_popup(title: str, message: str):
    """Muestra una ventana modal de error nativa en Windows para que el usuario pueda leer el error."""
    if sys.platform == "win32":
        try:
            import ctypes
            if hasattr(ctypes, "windll"):
                # MB_ICONERROR = 0x10, MB_SYSTEMMODAL = 0x1000
                ctypes.windll.user32.MessageBoxW(0, message, title, 0x10 | 0x1000)
        except Exception:
            pass


def pause_and_exit(code: int = 1, error_msg: str = ""):
    """Pausa la consola y muestra un popup nativo antes de terminar para evitar el cierre inmediato del CMD."""
    if is_android():
        log_msg(f"[ERROR ANDROID]: {error_msg}")
        return

    if error_msg:
        log_msg("=" * 65)
        log_msg(f"[ERROR CRÍTICO]: {error_msg}")
        log_msg(f"Archivo de registro guardado en:\n  {LOG_FILE_PATH}")
        log_msg("=" * 65)
        show_native_error_popup(
            "Error de Inicio - YouTube Downloader Pro",
            f"{error_msg}\n\n"
            f"El informe completo ha quedado guardado en:\n{LOG_FILE_PATH}\n\n"
            f"Presiona Aceptar para continuar."
        )

    if sys.stdout is not None:
        try:
            print("\n" + "-" * 65)
            if sys.stdin and sys.stdin.isatty():
                input("Presiona la tecla [ENTER] para salir...")
            else:
                import time
                time.sleep(3)
        except Exception:
            pass
    sys.exit(code)


# Lista de dependencias requeridas para la aplicación con restricciones de versión
REQUIRED_PACKAGES = [
    {
        "name": "yt-dlp",
        "pip_spec": "yt-dlp",
        "import_name": "yt_dlp",
        "min_version": "2024.1.1",
        "critical": True,
        "description": "Motor de descarga y extracción de audio/vídeo",
    },
    {
        "name": "kivy",
        "pip_spec": "kivy>=2.2.0",
        "import_name": "kivy",
        "min_version": "2.2.0",
        "critical": True,
        "description": "Framework de interfaz gráfica multiplataforma",
    },
    {
        "name": "kivymd",
        "pip_spec": "kivymd>=1.1.1,<2.0.0",
        "import_name": "kivymd",
        "min_version": "1.1.1",
        "max_version": "2.0.0",  # KivyMD 2.0 rompe la compatibilidad con MDTopAppBar/MDRoundFlatButton
        "critical": True,
        "description": "Componentes Material Design para Kivy (v1.2.0)",
    },
    {
        "name": "pillow",
        "pip_spec": "pillow",
        "import_name": "PIL",
        "critical": False,
        "description": "Procesamiento de miniaturas e imágenes",
    },
    {
        "name": "plyer",
        "pip_spec": "plyer",
        "import_name": "plyer",
        "critical": False,
        "description": "Integración con funciones del sistema (portapapeles, etc.)",
    },
    {
        "name": "certifi",
        "pip_spec": "certifi",
        "import_name": "certifi",
        "critical": False,
        "description": "Validación de certificados SSL seguros",
    },
    {
        "name": "urllib3",
        "pip_spec": "urllib3",
        "import_name": "urllib3",
        "critical": False,
        "description": "Gestor de conexiones de red HTTP/HTTPS",
    },
    {
        "name": "requests",
        "pip_spec": "requests",
        "import_name": "requests",
        "critical": False,
        "description": "Consultas web y descargas directas",
    },
]


def get_installed_version(package_name: str, import_name: str) -> Optional[str]:
    """Obtiene la versión instalada de un paquete."""
    try:
        import importlib.metadata
        return importlib.metadata.version(package_name)
    except Exception:
        pass

    try:
        mod = __import__(import_name)
        return getattr(mod, "__version__", "desconocida")
    except Exception:
        return None


def get_latest_pypi_version(package_name: str, timeout: int = 4) -> Optional[str]:
    """Consulta la API de PyPI para obtener la última versión pública disponible."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "YT-Downloader-Pro/DependencyChecker"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                return data.get("info", {}).get("version")
    except Exception:
        return None
    return None


def check_ffmpeg() -> Tuple[bool, Optional[str]]:
    """
    Comprueba si el binario FFmpeg está disponible.
    Busca en:
    1. Directorio de bibliotecas nativas de Android (lib/arm64-v8a/libffmpeg.so).
    2. Directorio de la aplicación (versión portable / .EXE).
    3. PATH del sistema.
    4. Variables de entorno personalizadas (FFMPG, FFMPEG, FFMPEG_PATH, etc.).
    5. Rutas comunes de instalación en Windows (C:\ffmpeg\bin, etc.).
    Si lo encuentra, inyecta su directorio en os.environ["PATH"] y LD_LIBRARY_PATH.
    """
    # 0. Comprobar en Android (biblioteca nativa extraída en nativeLibraryDir)
    if is_android():
        android_candidates = []
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            if activity:
                native_dir = activity.getApplicationInfo().nativeLibraryDir
                if native_dir and os.path.isdir(native_dir):
                    android_candidates.append(native_dir)
        except Exception as e:
            log_msg(f"check_ffmpeg: JNI nativeLibraryDir lookup: {e}")

        for pkg in ["org.downloader.ytdownloaderpro", "org.aegea.ytdownloaderpro"]:
            android_candidates.extend([
                f"/data/data/{pkg}/lib",
                f"/data/user/0/{pkg}/lib",
            ])

        ld_paths = os.environ.get("LD_LIBRARY_PATH", "").split(os.pathsep)
        android_candidates.extend([p for p in ld_paths if p and os.path.isdir(p)])

        for dir_path in android_candidates:
            if not os.path.isdir(dir_path):
                continue
            for bin_name in ["libffmpeg.so", "libffmpegbin.so", "ffmpeg"]:
                full_bin = os.path.join(dir_path, bin_name)
                if os.path.isfile(full_bin):
                    # Asegurar permisos de ejecución
                    try:
                        os.chmod(full_bin, 0o755)
                    except Exception:
                        pass
                    # Inyectar directorio en LD_LIBRARY_PATH y PATH
                    curr_ld = os.environ.get("LD_LIBRARY_PATH", "")
                    if dir_path not in curr_ld.split(os.pathsep):
                        os.environ["LD_LIBRARY_PATH"] = f"{dir_path}{os.pathsep}{curr_ld}".rstrip(os.pathsep)
                    curr_path = os.environ.get("PATH", "")
                    if dir_path not in curr_path.split(os.pathsep):
                        os.environ["PATH"] = f"{dir_path}{os.pathsep}{curr_path}".rstrip(os.pathsep)
                    log_msg(f"FFmpeg encontrado en Android: {full_bin}")
                    return (True, full_bin)

    # 1. Comprobar en el directorio de la aplicación o subcarpeta bin
    search_dirs = [
        BASE_DIR,
        os.path.join(BASE_DIR, "bin"),
        os.path.join(BASE_DIR, "ffmpeg", "bin"),
        os.path.join(BASE_DIR, "ffmpeg"),
    ]
    
    # 2. Comprobar en variables de entorno personalizadas (FFMPG, FFMPEG, etc.)
    for env_var in ["FFMPG", "FFMPEG", "FFMPEG_PATH", "FFMPEG_DIR"]:
        val = os.environ.get(env_var)
        if val:
            if os.path.isfile(val) and os.path.basename(val).lower().startswith("ffmpeg"):
                search_dirs.insert(0, os.path.dirname(val))
            elif os.path.isdir(val):
                search_dirs.insert(0, val)

    # 3. Rutas estándar en Windows
    search_dirs.extend([
        r"C:\ffmpeg\bin",
        r"C:\ffmpeg",
        r"C:\Program Files\ffmpeg\bin",
        r"C:\Program Files (x86)\ffmpeg\bin",
        r"D:\ffmpeg\bin",
        r"D:\ffmpeg",
    ])

    for directory in search_dirs:
        if os.path.isdir(directory):
            candidate = os.path.join(directory, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK | os.R_OK):
                # Inyectar en PATH para que subprocess y yt-dlp lo encuentren sin configuración manual
                current_path = os.environ.get("PATH", "")
                if directory not in current_path.split(os.pathsep):
                    os.environ["PATH"] = directory + os.pathsep + current_path
                return (True, candidate)

    # 4. Comprobar mediante shutil.which
    path = shutil.which("ffmpeg")
    if path:
        return (True, path)

    return (False, None)


def verify_all_dependencies() -> Dict[str, dict]:
    """
    Analiza el estado de todas las dependencias requeridas y valida su compatibilidad.
    """
    results = {}
    for pkg in REQUIRED_PACKAGES:
        name = pkg["name"]
        imp_name = pkg["import_name"]
        installed_ver = get_installed_version(name, imp_name)
        
        # En modo congelado .EXE, si se puede importar directamente se considera instalado
        if installed_ver is None and is_frozen():
            try:
                __import__(imp_name)
                installed_ver = "integrada"
            except Exception:
                pass

        is_installed = installed_ver is not None
        is_compatible = True
        incompatibility_reason = ""

        # Validar incompatibilidad por versión superior a la soportada (ej. KivyMD 2.0)
        if is_installed and installed_ver != "integrada" and "max_version" in pkg:
            max_v = version_tuple(pkg["max_version"])
            inst_v = version_tuple(installed_ver)
            if inst_v >= max_v:
                is_compatible = False
                incompatibility_reason = f"v{installed_ver} incompatible (requiere < {pkg['max_version']})"

        results[name] = {
            "installed": is_installed and is_compatible,
            "raw_installed": is_installed,
            "version": installed_ver,
            "min_version": pkg.get("min_version"),
            "max_version": pkg.get("max_version"),
            "pip_spec": pkg.get("pip_spec", name),
            "critical": pkg.get("critical", False),
            "description": pkg.get("description", ""),
            "incompatibility_reason": incompatibility_reason,
        }
    return results


def check_missing_dependencies() -> List[dict]:
    """Retorna la lista de paquetes requeridos que no están instalados o necesitan ajuste de versión."""
    if is_android() or is_frozen():
        return []

    status = verify_all_dependencies()
    missing = []
    for pkg in REQUIRED_PACKAGES:
        name = pkg["name"]
        if not status[name]["installed"]:
            item = dict(pkg)
            if status[name]["raw_installed"]:
                item["action"] = "reinstalar_compatible"
                item["reason"] = status[name]["incompatibility_reason"]
            else:
                item["action"] = "instalar"
                item["reason"] = "No instalada"
            missing.append(item)
    return missing


def check_outdated_dependencies(check_only_critical: bool = True) -> List[dict]:
    """
    Comprueba qué paquetes instalados tienen actualizaciones disponibles en PyPI
    respetando las restricciones de compatibilidad.
    """
    if is_android() or is_frozen():
        return []

    outdated = []
    for pkg in REQUIRED_PACKAGES:
        if check_only_critical and not pkg.get("critical", False):
            continue

        # No sugerir actualizar paquetes con versión máxima acotada (como kivymd)
        if "max_version" in pkg:
            continue

        name = pkg["name"]
        installed_ver = get_installed_version(name, pkg["import_name"])
        if installed_ver and installed_ver != "integrada":
            latest_ver = get_latest_pypi_version(name)
            if latest_ver and latest_ver != installed_ver:
                outdated.append({
                    "name": name,
                    "installed_version": installed_ver,
                    "latest_version": latest_ver,
                    "description": pkg.get("description", "")
                })
    return outdated


def install_package(package_spec: str, upgrade: bool = False, on_output: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
    """Instala o actualiza un paquete usando pip y registra toda la salida."""
    if is_android():
        return False, "La instalación con pip no está disponible en Android."
    if is_frozen():
        return False, "La aplicación está compilada como .EXE autónomo. Las dependencias vienen integradas."

    cmd = [sys.executable, "-m", "pip", "install"]
    if upgrade:
        cmd.append("--upgrade")
    cmd.append(package_spec)

    log_msg(f"Ejecutando instalación: {' '.join(cmd)}")

    try:
        if on_output:
            on_output(f"Ejecutando: {' '.join(cmd)}...\n")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

        output_lines = []
        if process.stdout:
            for line in process.stdout:
                output_lines.append(line)
                log_msg("  [pip] " + line.rstrip(), also_print=False)
                if on_output:
                    on_output(line)

        process.wait()
        full_output = "".join(output_lines)
        success = (process.returncode == 0)
        
        if not success:
            log_msg(f"❌ Error al instalar {package_spec} (Código de salida: {process.returncode})")
        else:
            log_msg(f"✅ {package_spec} instalado correctamente.")

        return success, full_output
    except Exception as e:
        err_msg = f"Excepción al ejecutar pip para {package_spec}: {str(e)}\n{traceback.format_exc()}"
        log_msg(err_msg)
        if on_output:
            on_output(err_msg + "\n")
        return False, err_msg


def upgrade_ytdlp(on_output: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
    """Actualiza yt-dlp a la última versión disponible en PyPI."""
    if is_frozen():
        return False, "En la versión .EXE compilada, yt-dlp ya está integrado. Recompila con compilar_exe.bat para actualizar."
    return install_package("yt-dlp", upgrade=True, on_output=on_output)


def ensure_dependencies(auto_install: bool = True, pause_on_fail: bool = True) -> bool:
    """
    Función de arranque automático con protección y diagnóstico.
    Verifica que las librerías necesarias estén instaladas en versiones compatibles.
    Si faltan librerías o hay versiones incompatibles (ej. KivyMD 2.0+), las ajusta automáticamente vía pip.
    """
    if is_android() or is_frozen():
        return True

    log_msg("=" * 65)
    log_msg(f"Inicio de verificación de dependencias: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_msg(f"Python: {sys.version.split()[0]} en {sys.executable}")
    log_msg("=" * 65)

    missing = check_missing_dependencies()
    if not missing:
        log_msg("✅ Todas las librerías necesarias están instaladas y en versiones compatibles.")
        return True

    log_msg("Se detectaron librerías que requieren instalación o ajuste de compatibilidad:")
    for item in missing:
        motivo = f" ({item['reason']})" if "reason" in item else ""
        log_msg(f"  • {item['name']}: {item['description']}{motivo}")

    if not auto_install:
        msg = "Faltan dependencias. Ejecuta: pip install -r requirements.txt"
        log_msg(msg)
        if pause_on_fail:
            pause_and_exit(1, msg)
        return False

    log_msg("\nAjustando dependencias automáticamente vía pip...")
    failed_packages = []

    for item in missing:
        pkg_spec = item.get("pip_spec", item["name"])
        log_msg(f"\n>> Instalando versión compatible: {pkg_spec}...")
        success, out = install_package(pkg_spec, upgrade=False, on_output=lambda line: sys.stdout.write("   " + line))
        if not success:
            failed_packages.append((pkg_spec, out))

    if failed_packages:
        error_summary = []
        for pkg, out in failed_packages:
            last_lines = "\n".join(out.strip().splitlines()[-6:])
            error_summary.append(f"• Paquete: {pkg}\n  Detalle de pip:\n{last_lines}")

        full_error_text = (
            f"No se pudieron instalar {len(failed_packages)} dependencias necesarias:\n\n"
            + "\n\n".join(error_summary)
            + "\n\nPosibles causas:\n"
            "- Sin conexión a internet o bloqueo por cortafuegos/proxy.\n"
            "- Permisos de usuario insuficientes para escribir en la carpeta de Python."
        )

        if pause_on_fail:
            pause_and_exit(1, full_error_text)
        return False

    log_msg("\n" + "=" * 65)
    log_msg(" Todas las dependencias han sido configuradas con éxito.")
    log_msg("=" * 65 + "\n")
    return True


if __name__ == "__main__":
    try:
        log_msg("=== Diagnóstico Manual de YouTube Downloader Pro ===")
        log_msg(f"Plataforma: {sys.platform} (Android: {is_android()}, Compilado .EXE: {is_frozen()})")
        log_msg(f"Ejecutable Python: {sys.executable}")
        
        ffmpeg_ok, ffmpeg_path = check_ffmpeg()
        log_msg(f"FFmpeg disponible: {'Sí' if ffmpeg_ok else 'No'} ({ffmpeg_path or 'No encontrado en PATH'})")
        log_msg("\nVerificando librerías...")
        status = verify_all_dependencies()
        for name, info in status.items():
            if info['installed']:
                ver_str = f"v{info['version']}"
                icon = "✅"
            else:
                ver_str = f"NO COMPATIBLE ({info['incompatibility_reason']})" if info['raw_installed'] else "NO INSTALADA"
                icon = "❌"
            log_msg(f"  {icon} {name:<12}: {ver_str:<25} ({info['description']})")

        missing = check_missing_dependencies()
        if missing:
            log_msg(f"\nSe requieren {len(missing)} ajustes de dependencias.")
            ensure_dependencies(auto_install=True, pause_on_fail=True)
        else:
            log_msg("\nComprobando actualizaciones en PyPI...")
            outdated = check_outdated_dependencies(check_only_critical=True)
            if outdated:
                for item in outdated:
                    log_msg(f"  ⚠️ Actualización disponible para {item['name']}: {item['installed_version']} -> {item['latest_version']}")
            else:
                log_msg("  ✅ Las librerías críticas están al día.")

        print("\nDiagnóstico finalizado.")
        if sys.stdin and sys.stdin.isatty():
            input("Presiona [ENTER] para salir...")

    except Exception as e:
        pause_and_exit(1, f"Error durante el diagnóstico: {str(e)}\n{traceback.format_exc()}")

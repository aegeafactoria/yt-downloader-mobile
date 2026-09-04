[app]

# (str) Title of your application
title = YT Downloader Pro

# (str) Package name
package.name = ytdownloaderpro

# (str) Package domain (needed for android packaging)
package.domain = org.downloader

# (str) Source code directory
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application version
version = 2.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,kivymd,yt-dlp,certifi,urllib3,idna,charset_normalizer,plyer,pillow,requests

# (str) Custom p4a local recipes directory
p4a.local_recipes = ./p4a_recipes


# (str) Supported orientations (one of landscape, portrait or all)
orientation = portrait

# (bool) Use fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
# android.ndk = 25b

# (str) Android SDK directory to use (if empty, it will be downloaded)
# android.sdk_path = 

# (str) Android NDK directory to use (if empty, it will be downloaded)
# android.ndk_path = 

# (list) The Android architectures to build for (arm64-v8a, armeabi-v7a, x86, x86_64)
android.archs = arm64-v8a

# (bool) Allow backup
android.allow_backup = True

# (bool) Request legacy external storage (required for writing downloads on Android 10/11)
android.requestlegacyexternalstorage = True

# (bool) Auto accept Android SDK licenses
android.accept_sdk_license = True

# (str) Bootstrap to use for android build
android.bootstrap = sdl2

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 0

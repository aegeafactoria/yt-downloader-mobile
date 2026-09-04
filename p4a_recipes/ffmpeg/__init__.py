from pythonforandroid.recipe import Recipe
from pythonforandroid.logger import shprint, info
from os.path import join, exists, dirname
import sh
import shutil


class FFMpegRecipe(Recipe):
    version = '9.0.1'
    url = 'https://raw.githubusercontent.com/aegeafactoria/yt-downloader-mobile/main/p4a_recipes/ffmpeg/ffmpeg-9.0.1.tar.xz'
    archive_root = 'ffmpeg-9.0.1'
    built_libraries = {'libffmpeg.so': '.', 'libc++_shared.so': '.'}

    def download_file(self, url, target, cwd=None):
        local_archive = join(dirname(__file__), 'ffmpeg-9.0.1.tar.xz')
        if exists(local_archive):
            info(f'FFMpegRecipe: Using local archive from {local_archive}')
            shutil.copy(local_archive, target)
            return
        super().download_file(url, target, cwd=cwd)

    def should_build(self, arch):
        return True

    def build_arch(self, arch):
        build_dir = self.get_build_dir(arch.arch)
        info(f'FFMpegRecipe: Preparing binaries in {build_dir} for {arch.arch}')
        libffmpeg = join(build_dir, 'libffmpeg.so')
        if exists(libffmpeg):
            shprint(sh.chmod, '+x', libffmpeg)

    def install_libraries(self, arch):
        build_dir = self.get_build_dir(arch.arch)
        libs_to_install = []
        for lib in ['libffmpeg.so', 'libc++_shared.so']:
            p = join(build_dir, lib)
            if exists(p):
                libs_to_install.append(p)
        if libs_to_install:
            info(f'FFMpegRecipe: Installing {libs_to_install} to {arch.arch}')
            self.install_libs(arch, *libs_to_install)


recipe = FFMpegRecipe()

import PyInstaller.__main__
import os
import shutil
from PyInstaller.utils.hooks import collect_data_files

def build():
    # clean dist and build folders
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")

    # Collect data files for flet_desktop to ensure the binary is included
    flet_datas = collect_data_files('flet_desktop')
    # Also collect for flet core just in case
    flet_datas.extend(collect_data_files('flet'))

    print(f"DEBUG: Collected datas: {flet_datas}")

    PyInstaller.__main__.run([
        "gui_app.py",
        "--name=TranscriptAnalyzer",
        "--windowed",
        "--onedir", 
        "--clean",
        "--hidden-import=flet.controls.services.file_picker",
        "--hidden-import=flet_desktop",
        "--add-data=.env:. " if os.path.exists(".env") else "", 
    ] + [f"--add-data={src}:{dest}" for src, dest in flet_datas])

    print("Build complete. detailed logs in build/ and output in dist/TranscriptAnalyzer.app")

if __name__ == "__main__":
    build()

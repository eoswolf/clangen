import os
import platform
import subprocess
import logging

from scripts.housekeeping.version import get_version_info

logger = logging.getLogger(__name__)


def setup_data_dir():
    os.makedirs(get_data_dir(), exist_ok=True)
    try:
        os.makedirs(get_save_dir(), exist_ok=True)
        os.makedirs(get_temp_dir(), exist_ok=True)
    except FileExistsError:
        print("Macos ignored exist_ok=true for save or temp dict, continuing.")
        pass
    os.makedirs(get_log_dir(), exist_ok=True)
    os.makedirs(get_cache_dir(), exist_ok=True)
    os.makedirs(get_saved_images_dir(), exist_ok=True)

    # Windows requires elevated permissions to create symlinks.
    # The OpenDataDirectory.bat can be used instead as "shortcut".
    if platform.system() != "Windows":
        if os.path.exists("game_data"):
            os.remove("game_data")
        if not get_version_info().is_source_build:
            os.symlink(get_data_dir(), "game_data", target_is_directory=True)


def get_data_dir():
    if get_version_info().is_source_build:
        return "."

    from platformdirs import user_data_dir


    return user_data_dir('ClanGen', 'ClanGen')


def get_log_dir():
    return get_data_dir() + "/logs"


def get_save_dir():
    return get_data_dir() + "/saves"


def get_cache_dir():
    return get_data_dir() + "/cache"


def get_temp_dir():
    return get_data_dir() + "/.temp"


def get_saved_images_dir():
    return get_data_dir() + "/saved_images"


def open_data_dir():
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "-R", get_data_dir()])
    elif platform.system() == "Windows":
        os.startfile(get_data_dir())  # pylint: disable=no-member
    elif platform.system() == "Linux":
        try:
            subprocess.Popen(["xdg-open", get_data_dir()])
        except OSError:
            logger.exception("Failed to call to xdg-open.")


def open_url(url: str):
    if platform.system() == "Darwin":
        subprocess.Popen(["open", "-u", url])
    elif platform.system() == "Windows":
        os.system(f'start "" {url}')
    elif platform.system() == "Linux":
        subprocess.Popen(["xdg-open", url])

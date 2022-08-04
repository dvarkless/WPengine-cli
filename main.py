import argparse
import json
import os
import pathlib
import subprocess


def get_arguments():
    parser = argparse.ArgumentParser(prog='Wengine-cli')

    parser.add_argument('--random', action=argparse.BooleanOptionalAction,
                        help='Setup random wallpaper from WallpaperEngine directory', default=False)
    parser.add_argument('--undo', action=argparse.BooleanOptionalAction,
                        help='Return previous wallpaper. Useful then you got a black screen', default=False)
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('--steamdir', type=pathlib.Path,
                        help='Specify your Steam directory with this argument')
    parser.add_argument('--verbose', action=argparse.BooleanOptionalAction,
                        help='Debug utility', default=False)
    args = parser.parse_args()

    return args


def check_file(file_path: os.PathLike, home_prefix: bool = False):
    if home_prefix:
        file_path = os.path.expanduser(file_path)
    if os.path.exists(file_path):
        return
    else:
        raise FileNotFoundError(f'File "{file_path}" is not found')


def create_conf_template():
    file_path = os.path.expanduser('.config//Wengine-cli/config.json')
    with open(file_path, 'w') as file:
        struct = {
            'steam_dir': '/path/to/SteamLibrary',
            'last_id': '000000',
            'prev_ids': ['000', '001', '002', '003'],
            'WallpaperEngineSteamID': '431960',
            'WallpaperProjectName': 'Project.json',
            'WallpaperWorkShopIdOld': '12345',
            'WallpaperKDE'
            'WallpaperSourceOld': 'path/to/wallpaper',
            'VolumeOld': 0,
            'MuteAudioOld': False,
            'FpsOld': 30,
            'DisplayModeOld': 1,
        }
        json.dump(struct, file)


class ConfigHandler:
    def __init__(self, config_path: os.PathLike) -> None:
        self.config = config_path

    def get_data(self, key=None):
        with open(self.config, 'r') as conf:
            data = json.load(conf)
        if key is None:
            return data
        else:
            return data[key]

    def add_pos(self, id, data):
        all_data = self.get_data()
        all_data[id] = data
        with open(self.config, 'w') as conf:
            json.dump(all_data, conf)

    def _send_cmd(self, id, val):
        cmd = []
        cmd.append("dbus-send")
        cmd.append("--session")
        cmd.append("--dest=org.kde.plasmashell")
        cmd.append("--type=method_call")
        cmd.append("/PlasmaShell")
        cmd.append("org.kde.PlasmaShell.evaluateScript")
        cmd.append("'string:")
        letter = "\"for (d of desktops()) { d.wallpaperPlugin = \"com.github.casout.wallpaperEngineKde\"; d.currentConfigGroup = Array(\"Wallpaper\", \"com.github.casout.wallpaperEngineKde\", \"General\");"
        letter += f'd.writeConfig("{id}", "{val}");'
        letter += ' }"'
        cmd.append(letter)
        subprocess.run(cmd)


class Changer:
    def __init__(self) -> None:
        self._path_with_home = None
        self._steampath = None
        self._full_path = None

    @property
    def path_with_home(self):
        if os.path.exists(self._full_path):
            return self._path_with_home
        else:
            raise FileNotFoundError(
                f'File {self._path_with_home} is not found')

    @path_with_home.setter
    def path_with_home(self, rel_path: os.PathLike):
        self._path_with_home = os.path.expanduser(rel_path)

    @property
    def full_path(self):
        if os.path.exists(self._full_path):
            return self._full_path
        else:
            raise FileNotFoundError(f'File {self._full_path} is not found')

    @full_path.setter
    def full_path(self, rel_path: os.PathLike):
        if isinstance(self._steampath, os.PathLike):
            self._full_path = os.path.join(self._steampath, rel_path)


class SettingsChanger(Changer):
    def __init__(self) -> None:
        pass


class WallpaperChanger(Changer):
    def __init__(self, steampath, config_path) -> None:
        super().__init__()
        self.handler = ConfigHandler(config_path)
        self._steampath = steampath

        wpe_id = self.handler.get_data('WallpaperEngineSteamID')
        self.project_name = self.handler.get_data('WallpaperProjectName')
        self.full_path = os.path.join('/steamapps/workshop/content', wpe_id)

    def get_data(self, wp_path: os.PathLike, files: list):
        if self.project_name in files:
            with open(os.path.join(wp_path, self.project_name), 'r') as file:
                data = json.load(file)
                self.handler.add_pos(os.path.split(root)[-1], data)

    def get_all_data(self):
        for root, _, files in os.walk(self.full_path):
            self.get_data(root, files)

    def setup(self, name):
        # 1)name is name or id
        # 1.1) wallpaper type
        # 2) send command to setup wallpaper
        # 3) setup wallpaper parameters


def main():
    pass

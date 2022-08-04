import argparse
import json
import os
import re
import subprocess
from pathlib import Path


def get_arguments():
    parser = argparse.ArgumentParser(prog='Wengine-cli')

    parser.add_argument('--random', action=argparse.BooleanOptionalAction,
                        help='Setup random wallpaper from WallpaperEngine directory', default=False)
    parser.add_argument('--undo', action=argparse.BooleanOptionalAction,
                        help='Return previous wallpaper. Useful then you got a black screen', default=False)
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('--steamdir', type=Path,
                        help='Specify your Steam directory with this argument')
    parser.add_argument('--verbose', action=argparse.BooleanOptionalAction,
                        help='Debug utility', default=False)
    args = parser.parse_args()

    return args


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
    def __init__(self, config_path: Path) -> None:
        if not Path(config_path).exists():
            raise FileNotFoundError(f'file not found: {config_path}')
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
        if 'title' in data and 'type' in data:
            all_data[id + '_prop'] = (data['title'], data['type'])

        with open(self.config, 'w') as conf:
            json.dump(all_data, conf)

    def send_cmd(self, id, val):
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
    def __init__(self, steampath) -> None:
        self._path_with_home = None
        self._steampath = Path(steampath)
        self._full_path = None

    @property
    def path_with_home(self):
        if Path(self._path_with_home).exists():
            return self._path_with_home
        else:
            raise FileNotFoundError(
                f'File {self._path_with_home} is not found')

    @path_with_home.setter
    def path_with_home(self, rel_path: Path):
        self._path_with_home = Path().home() / Path(rel_path)

    @property
    def full_path(self):
        if Path(self._full_path).exists():
            return self._full_path
        else:
            raise FileNotFoundError(f'File {self._full_path} is not found')

    @full_path.setter
    def full_path(self, rel_path: Path):
        if isinstance(self._steampath, Path):
            self._full_path = os.path.join(self._steampath, rel_path)
        else:
            raise ValueError('_steampath not exists')


class SettingsChanger(Changer):
    def __init__(self, steampath, config_path) -> None:
        super().__init__(steampath)
        self.handler = ConfigHandler(config_path)

        wpe_id = self.handler.get_data('WallpaperEngineSteamID')
        self.project_name = self.handler.get_data('WallpaperProjectName')
        self.full_path = Path('steamapps/workshop/content') / wpe_id

    def setup():
        pass


class WallpaperChanger(Changer):
    def __init__(self, steampath, config_path) -> None:
        super().__init__()
        self.handler = ConfigHandler(config_path)
        self._steampath = Path(steampath)

        wpe_id = self.handler.get_data('WallpaperEngineSteamID')
        self.project_name = self.handler.get_data('WallpaperProjectName')
        self.full_path = Path('steamapps/workshop/content') / wpe_id

    def get_data(self, wp_path: Path, files: list):
        if self.project_name in files:
            with open(Path(wp_path) / self.project_name), 'r') as file:
                data=json.load(file)
                self.handler.add_pos(root.suffix, data)

    def get_all_data(self):
        for root, _, files in os.walk(self.full_path):
            self.get_data(Path(root), files)

    def setup(self, name):
        name_type=None
        name_id=None
        wp_data=self.handler.get_data()
        for id, vals in wp_data.items():
            name_id=id
            if name == id:
                name_type='id'
                break
            if name in vals:
                name_type='name'
                break
        else:
            raise KeyError(f'Bad name or id: "{name}"')

        wp_type=wp_data[name_id]['type']
        self.handler.send_cmd('WallpaperWorkShopId', name_id)

        tail=wp_data[name_id]['file'] + '+' + wp_type
        wp_path=self.full_path / name_id / tail
        # add file:// if as_uri raises exception
        self.handler.send_cmd('WallpaperSource', wp_path.as_uri())

class Plugin:
    def __init__(self) -> None:
        home_dir=Path().home()
        if not home_dir.exists():
            raise FileNotFoundError(
                'Please setup your "$HOME" environment variable')
        self.config_path=Path().home() / Path('/.config/WPE-cli/config.json')
        self.handler=ConfigHandler(config_path)
        self.steamdir=self.handler.get_data('steam_dir')


        self.wp_changer=WallpaperChanger(self.steamdir, self.config_path)
        self.settings_changer = SettingsChanger(self.steamdir, self.config_path)

        parser=argparse.ArgumentParser(
                    description = 'CLI addon for Wallpaper Engine KDE tool',
                    usage = '''wengine <command> [<args>]

        Commands:
           wallpaper  Setup wallpaper
           settings   Change settings
           update     Update list of installed wallpapers
           config     Change specific configs
           pull       Pull data about current wallpaper and SteamLibrary from
                      Wallpaper Engine
           undo       Undo last change, useful then you get a black screen
        ''')
        parser.add_argument('command', help = 'Subcommand to run')

        # parser = argparse.ArgumentParser(prog='Wengine-cli')
        # parser.add_argument('--random', action=argparse.BooleanOptionalAction,
        #                     help='Setup random wallpaper from WallpaperEngine directory', default=False)
        # parser.add_argument('--undo', action=argparse.BooleanOptionalAction,
        #                     help='Return previous wallpaper. Useful then you got a black screen', default=False)
        # parser.add_argument('--version', action='version', version='%(prog)s 0.1')
        # parser.add_argument('--steamdir', type=Path,
        #                     help='Specify your Steam directory with this argument')
        # parser.add_argument('--verbose', action=argparse.BooleanOptionalAction,
        #                     help='Debug utility', default=False)

        args=parser.parse_args()
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)

        getattr(self, args.command)()

    def config(self):
        pass

    def pull(self):
        settings_path=Path(
            "~/.config/plasma-org.kde.plasma.desktop-appletsrc").expanduser()
        patterns = {
            "steam_dir": re.compile(r"SteamLibraryPath.+"),
            "WallpaperWorkShopIdOld": re.compile(r"WallpaperWorkShopId.+"),
            "WallpaperSource": re.compile(r"WallpaperSource.+"),
                }
        
        pattern_path=re.compile(r"file://.+")
        pattern_digits=re.compile(r"\d+")
        pattern_types = {
            "steam_dir": pattern_path,
            "WallpaperWorkShopIdOld": pattern_digits,
            "WallpaperSourceOld": pattern_path,
                }

        with open(settings_path, 'r') as file:
            for line in file:
                for config, pattern in patterns.items():
                    if pattern.match(line):
                        match = pattern_types[config].search(line)
                        data = match.group(0)
                        self.handler.add_pos(config, data)

    def wallpaper(self):
        self.wp_changer.setup()

    def undo(self):
        pass

    def update(self):
        pass

    def settings(self):
        self.settings_changer.setup()


if __name__ == "__main__":
    Plugin()

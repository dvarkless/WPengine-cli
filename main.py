import argparse
import json
import os
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from random import choices

import dbus


class ConfigHandler:
    __template = {
        'steam_dir': '/path/to/SteamLibrary',
        'last_id': '000000',
        'prev_ids': ['000', '001', '002', '003'],
        'WallpaperEngineSteamID': '431960',
        'WallpaperProjectName': 'project.json',
        'WallpaperWorkShopIdOld': '12345',
        'WallpaperSourceOld': 'path/to/wallpaper',
    }

    def __init__(self, config_path: Path) -> None:
        self.config = Path(config_path)
        if not self.config.exists():
            print(f'Could not find a configuration file at "{config_path}"')
            result = input("Create a new config? y/n \n")
            if result == 'y':
                self.write_template()
            else:
                exit(1)

    def get_data(self, key=None):
        with open(self.config, 'r') as conf:
            data = json.load(conf)
        if key is None:
            return data
        else:
            return data[key]

    def get_ids(self):
        data = self.get_data()
        to_remove = []
        for name in data.keys():
            try:
                int(name)
            except:
                to_remove.append(name)
        for name in to_remove:
            del data[name]
        return data

    def update_last_ids(self, id, /):
        prev_ids = self.get_data('prev_ids')
        prev_ids.pop(0)
        prev_ids.append(id)
        self.add_pos('prev_ids', prev_ids)
        self.add_pos('last_id', id)

    def add_pos(self, id, data):
        all_data = self.get_data()
        all_data[id] = data

        with open(self.config, 'w') as conf:
            json.dump(all_data, conf)

    def remove_pos(self, name, /):
        all_data = self.get_data()
        try:
            del all_data[name]
        except KeyError:
            raise KeyError(
                f"This key ({name}) does not exist in config file. Explicit call??")
        with open(self.config, 'w') as conf:
            json.dump(all_data, conf)

    def send_cmd(self, id, val):
        script = """
        for (d of desktops()) {
            d.wallpaperPlugin = "com.github.casout.wallpaperEngineKde";
            d.currentConfigGroup = Array("Wallpaper", "com.github.casout.wallpaperEngineKde", "General");
        """
        script += f'd.writeConfig("{id}", "{val}");'
        script += '\n}'
        bus = dbus.SessionBus()
        plasma = dbus.Interface(bus.get_object(
            'org.kde.plasmashell', '/PlasmaShell'), dbus_interface='org.kde.PlasmaShell')
        plasma.evaluateScript(script)

    def write_template(self):
        self.config.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config, 'w') as file:
            json.dump(ConfigHandler.__template, file)


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
            raise ValueError(
                f'_steampath is not an instance of Path ({self._steampath})')


class SettingsChanger(Changer):
    def __init__(self, steampath, config_path) -> None:
        super().__init__(steampath)
        self.handler = ConfigHandler(config_path)

        wpe_id = self.handler.get_data('WallpaperEngineSteamID')
        self.project_name = self.handler.get_data('WallpaperProjectName')
        self.full_path = Path('steamapps/workshop/content') / wpe_id

    def setup(self):
        pass


class WallpaperChanger(Changer):
    def __init__(self, steampath, config_path) -> None:
        super().__init__(steampath)
        self.handler = ConfigHandler(config_path)
        self._steampath = Path(steampath)

        wpe_id = self.handler.get_data('WallpaperEngineSteamID')
        self.project_name = self.handler.get_data('WallpaperProjectName')
        self.full_path = Path('steamapps/workshop/content') / wpe_id

    def get_data(self, wp_path: Path, files: list):
        if self.project_name in files:
            with open(Path(wp_path) / self.project_name, 'r') as file:
                data = json.load(file)
                self.handler.add_pos(Path(wp_path).name, data)

    def get_all_data(self):
        for root, _, files in os.walk(self.full_path):
            self.get_data(Path(root), files)

    def get_last_id_name(self):
        data = self.handler.get_data()
        id = data['last_id']
        try:
            name = data[id]['title']
        except:
            raise FileNotFoundError(f'Could not find wallpaper by id:{id}')
        return id, name

    def setup(self, name, silent_delete=False):
        if type(name) in (tuple, list, set):
            name = name[0]
        name_id = None
        wp_data = self.handler.get_data()
        for id, vals in wp_data.items():
            name_id = id
            if name == id:
                break
            else:
                if isinstance(vals, dict):
                    if SequenceMatcher(a=name, b=vals['title']).ratio() > 0.8:
                        break
        else:
            raise KeyError(f'Bad name or id: "{name}"')

        wp_type = wp_data[name_id]['type']
        self.handler.send_cmd('WallpaperWorkShopId', name_id)

        tail = wp_data[name_id]['file'] + '+' + wp_type
        wp_path = self.full_path / Path(name_id) / Path(tail)
        if not Path(self.full_path / Path(name_id)).exists():
            if silent_delete:
                self.handler.remove_pos(id)
                return True
            else:
                print(f'error path: "{wp_path}"')
                raise KeyError(
                    f'This id not exists: "{id}" with name "{name}"')
        # add file:// if as_uri raises exception
        self.handler.send_cmd('WallpaperSource', 'file://'+str(wp_path))
        self.handler.update_last_ids(id)

    def setup_random(self, **filters):
        wp_ids = self.handler.get_ids()
        for name, val in filters.items():
            for id, data in wp_ids:
                if val is list:
                    if data[name] not in val:
                        del wp_ids[id]
                if val in (int, float, str):
                    if data[name] != val:
                        del wp_ids[id]
        if len(wp_ids) == 0:
            raise ValueError(
                f"Could not find wallpapers with this filters: {filters}")

        last_ids = self.handler.get_data('prev_ids')
        weights = []
        for id in wp_ids:
            if id in last_ids:
                weights.append(0.1)
            else:
                weights.append(1)
        if self.setup(choices(list(wp_ids.keys()), weights=weights)):
            print(
                f'setup_random failed because got non-existent id, recursive calling itself again')
            self.setup_random(**filters)


class Plugin:
    def __init__(self) -> None:
        home_dir = Path().home()
        if not home_dir.exists():
            raise FileNotFoundError(
                'Please setup your "$HOME" environment variable')
        self.config_path = Path('~/.config/WPE-cli/config.json').expanduser()
        self.handler = ConfigHandler(self.config_path)
        self.steamdir = self.handler.get_data('steam_dir')

        self.wp_changer = WallpaperChanger(self.steamdir, self.config_path)
        self.settings_changer = SettingsChanger(
            self.steamdir, self.config_path)

        parser = argparse.ArgumentParser(
            description='CLI addon for Wallpaper Engine KDE tool',
            usage='''wengine <command> [<args>]

        Commands:
           wallpaper - Operations with wallpaper
           settings  - Change settings in Wallpaper Engine
           update    - Update list of installed wallpapers
           config    - Change specified configs 
           pull      - Pull data about current wallpaper and SteamLibrary from
                       Wallpaper Engine
           undo      - Undo last change, useful then you get a black screen
        ''')
        self.parser_0 = parser
        parser.add_argument('command', help='Subcommand to run')

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

        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            self.help()
        getattr(self, args.command)()

    def config(self):
        parser = argparse.ArgumentParser(
            description='Operations with wallpaper',
            usage='''wengine config <command> <flags>

        Commands:
            setup  - setup config
            get    - get config

        ''')

        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[2:3])
        if args.command == 'setup':
            pass
        elif args.command == 'get':
            pass
        else:
            self.help(parser)

    def pull(self):
        settings_path = Path(
            "~/.config/plasma-org.kde.plasma.desktop-appletsrc").expanduser()
        patterns = {
            "steam_dir": re.compile(r"SteamLibraryPath.+"),
            "WallpaperWorkShopIdOld": re.compile(r"WallpaperWorkShopId.+"),
            "WallpaperSourceOld": re.compile(r"WallpaperSource.+"),
        }

        pattern_path = re.compile(r"file://(.+)")
        pattern_digits = re.compile(r"\d+")
        pattern_types = {
            "steam_dir": (pattern_path, 1),
            "WallpaperWorkShopIdOld": (pattern_digits, 0),
            "WallpaperSourceOld": (pattern_path, 0),
        }

        with open(settings_path, 'r') as file:
            for line in file:
                for config, pattern in patterns.items():
                    if pattern.match(line):
                        pattern_type, pos = pattern_types[config]
                        match = pattern_type.search(line)
                        if match is not None:
                            data = match.group(pos)
                            self.handler.add_pos(config, data)

    def wallpaper(self):
        parser = argparse.ArgumentParser(
            description='Operations with wallpaper',
            usage='''wengine wallpaper <command> <flags>

        Commands:
            setup  - setup wallpaper by id or name
            random - setup random wallpaper. You can specify filters with
                     arguments --type, --contentrating, --tags.
                     (for example choose random wallpaper from nature scenes:
                         ... random --type scenes --tags Nature)
            name   - get current wallpaper name and id
                     in format: <id> "name".
            accent - get wallpaper's accent color in RGB uint8 format:
                     R G B
            get    - get info about the wallpaper from its config

        ''')

        parser.add_argument('command', help='Subcommand to run')

        parser.add_argument(
            '--type', help='random: Type of wallpapers to choose from. Syntax: "--type scene,video,web"')
        parser.add_argument(
            '--contentrating', help='random: Filter out NSFW wallpapers and vice versa. Syntax: "--contentrating Everyone,Mature" (Note! starts with capital letter)', )
        parser.add_argument(
            '--tags', help='random: Filter by tags specified in wallpaper description. Syntax: "--tags Nature,Anime,Game"')

        args = parser.parse_args(sys.argv[2:3])
        if args.command == 'setup':
            parser.add_argument(
                'name_or_id', help='Title of the wallpaper or its id')
            args = parser.parse_args(sys.argv[2:])
            self.wp_changer.setup(args.name_or_id)
        elif args.command == 'random':
            filters = {}
            if hasattr(args, 'type'):
                if args.type:
                    filters['type'] = args.type.split(',')
            if hasattr(args, 'contentrating'):
                if args.contentrating:
                    filters['contentrating'] = args.contentrating.split(',')
            if hasattr(args, 'tags'):
                if args.tags:
                    filters['tags'] = args.tags.split(',')

            self.wp_changer.setup_random(**filters)

        elif args.command == 'name':
            id, name = self.wp_changer.get_last_id_name()
            print(f'<{id}> "{name}"')

        elif args.command == 'accent':
            id, _ = self.wp_changer.get_last_id_name()
            wp_data = self.handler.get_data(id)
            rgb_str = wp_data['general']['properties']['schemecolor']['value']
            rgb_vals = [int(float(val)*255) for val in rgb_str.split()]
            print("{} {} {}".format(*rgb_vals))

        elif args.command == 'get':
            id, _ = self.wp_changer.get_last_id_name()
            wp_data = self.handler.get_data(id)

            def recursion_dict_printer(my_dict, level=0):
                for name, val in my_dict.items():
                    if isinstance(val, dict):
                        recursion_dict_printer(my_dict[name], level+1)
                    else:
                        print(f'{"  "*level} {name}="{val}"')
            recursion_dict_printer(wp_data)
        else:
            self.help(parser)

    def undo(self):
        id = self.handler.get_data('WallpaperWorkShopIdOld')
        self.wp_changer.setup(id)

    def update(self):
        self.wp_changer.get_all_data()

    def settings(self):
        parser = argparse.ArgumentParser(
            description='Change settings for Wallpaper Engine',
            usage='''wengine settings <command> <flags>

        Commands:
            setup - setup specific setting for Wallpaper Engine
            get   - get specific setting
        ''')

        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[2:3])
        if args.command == 'setup':
            pass
        elif args.command == 'get':
            pass
        else:
            self.help(parser)

    def help(self, parser=None, /):
        if parser is None:
            parser = self.parser_0
        print('Unrecognized command')
        parser.print_help()
        exit(1)


if __name__ == "__main__":
    Plugin()

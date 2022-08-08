import argparse
import sys
from pathlib import Path

from changers import SettingsChanger, WallpaperChanger
from config_handler import ConfigHandler


class Plugin:
    def __init__(self) -> None:
        home_dir = Path().home()
        if not home_dir.exists():
            raise FileNotFoundError(
                'Please setup your "$HOME" environment variable')
        self.config_path = Path('~/.config/WPE-cli/config.json').expanduser()
        self.handler = ConfigHandler(self.config_path)
        self.steamdir = self.handler.get_data('SteamLibraryPath')

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
        settings_list = self.settings_changer.read()
        for setting_tuple in settings_list:
            self.handler.add_pos(*setting_tuple)

    def wallpaper(self):
        parser = argparse.ArgumentParser(
            description='Operations with wallpaper')
        """
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
        """
        parser.add_argument('command', help='Subcommand to run')

        parser.add_argument(
            '--type', help='random: Type of wallpapers to choose from. Syntax: "--type scene,video,web"', choices=['scene', 'video', 'web'])
        parser.add_argument(
            '--contentrating', help='random: Filter out NSFW wallpapers and vice versa. Syntax: "--contentrating Everyone,Mature" (Note! starts with capital letter)', choices=['Everyone', 'Questionable', 'Mature'])
        parser.add_argument(
            '--tags', help='random: Filter by tags specified in wallpaper description. Syntax: "--tags Nature,Anime,Game"')
        parser.add_argument(
            '--strict', help='random: disable fuzzy finder then searching by title', action=argparse.BooleanOptionalAction, default='False')

        parser.add_argument(
            '--nsfw', help='random: add wallpapers with rating "Mature" into the mix', action=argparse.BooleanOptionalAction, default='False')
        args = parser.parse_args(sys.argv[2:3])
        if args.command == 'setup':
            parser.add_argument(
                'name_or_id', help='Title of the wallpaper or its id')
            args = parser.parse_args(sys.argv[2:])
            self.wp_changer.setup(args.name_or_id)
        elif args.command == 'random':
            filters = {}
            args = parser.parse_args(sys.argv[2:])
            if hasattr(args, 'type'):
                if args.type:
                    filters['type'] = args.type.split(',')
            if hasattr(args, 'contentrating'):
                if args.contentrating:
                    filters['contentrating'] = args.contentrating.split(',')
            if hasattr(args, 'tags'):
                if args.tags:
                    filters['tags'] = args.tags.split(',')
            if args.nsfw:
                if 'contentrating' not in filters.keys():
                    filters['contentrating'] = ['Everyone', 'Unspecified', 'Questionable']
            self.wp_changer.setup_random(filters=filters, fuzzy=not args.strict)

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
        undoable_settings = self.settings_changer.settings_list
        for setting in undoable_settings:
            if setting in ("SteamLibraryPath"):
                continue
            val = self.handler.get_data(setting)
            self.settings_changer.setup(setting, val)

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
        parser.add_argument(
            'setting_name', help='Name of the setting to change or print')
        args = parser.parse_args(sys.argv[2:4])
        if args.command == 'setup':
            parser.add_argument('setting_val', help='Subcommand to run')
            args = parser.parse_args(sys.argv[2:5])

            setting = args.setting_name
            val = args.setting_val
            self.settings_changer.setup(setting, val)
        elif args.command == 'get':
            setting = args.setting_name
            print(self.settings_changer.read(setting))
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

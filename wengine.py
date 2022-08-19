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
        
        # defining argument parser:
        parser = argparse.ArgumentParser(
            description='CLI for Wallpaper Engine KDE tool')
        subparsers = parser.add_subparsers(dest='command')
        wallpaper_parser = subparsers.add_parser('wallpaper', help='Operations with the wallpaper')
        wallpaper_parser.set_defaults(func=self.wallpaper)

        wallpaper_subparsers = wallpaper_parser.add_subparsers(dest='wallpaper_command')
        setup_wallpaper_parser = wallpaper_subparsers.add_parser('setup')
        setup_wallpaper_parser.add_argument(
            '--strict', help='disable fuzzy finder then searching by title', action=argparse.BooleanOptionalAction, default=False)
        setup_wallpaper_parser.add_argument('name_or_id', help='Name or ID') 
        random_wallpaper_parser = wallpaper_subparsers.add_parser('random')
        random_wallpaper_parser.add_argument(
            '--type', help='Type of wallpapers to choose from. Syntax: "--type scene,video,web"', choices=['scene', 'video', 'web'])
        random_wallpaper_parser.add_argument(
            '--contentrating', help='Filter out NSFW wallpapers and vice versa. Syntax: "--contentrating Everyone,Questionable,Mature" (Note! starts with capital letter)', choices=['Everyone', 'Questionable', 'Mature'])
        random_wallpaper_parser.add_argument(
            '--tags', help='Filter by tags specified in wallpaper description. Syntax: "--tags Nature,Anime,Game"')
        random_wallpaper_parser.add_argument(
            '--nsfw', help='Add wallpapers with rating "Mature" into the mix', action=argparse.BooleanOptionalAction, default=False)

        wallpaper_subparsers.add_parser('name', help='get name of the current wallpaper')
        wallpaper_subparsers.add_parser('accent', help='get accent color from the current wallpaper in uint8 RGB format')
        wallpaper_subparsers.add_parser('get', help='print info about current wallpaper')
        wallpaper_subparsers.add_parser('like', help='show this wallpaper twice more often then calling "random" method (max is x2)')
        wallpaper_subparsers.add_parser('dislike', help='show this wallpaper half as often often then calling "random" method (min is x0.5)')
            
        settings_parser = subparsers.add_parser('settings', help="manipulate and view Wallpaper Engine's config file")
        settings_parser.set_defaults(func=self.settings)
        settings_subparsers = settings_parser.add_subparsers(dest='settings_command')

        setup_settings_parser = settings_subparsers.add_parser('setup')
        name_setup_settings_parser = setup_settings_parser.add_subparsers(dest='subcommand').add_parser('name')
        name_setup_settings_parser.add_argument('value')

        get_settings_parser = settings_subparsers.add_parser('get')
        get_settings_parser.add_argument('name', help='setting name')

        update_parser = subparsers.add_parser('update', help='get the list of available wallpapers for this CLI')
        update_parser.set_defaults(func=self.update)

        pull_parser = subparsers.add_parser('pull', help='get all configurations from Wallpaper Engine KDE widget')
        pull_parser.set_defaults(func=self.pull)

        undo_parser = subparsers.add_parser('undo', help='revert current wallpaper and configurations to last working state')
        undo_parser.set_defaults(func=self.undo)

        parser.add_argument('--version', action='version', version='%(prog)s 0.5')
        parser.add_argument('--verbose', action=argparse.BooleanOptionalAction,
                            help='debug utility', default=False) 

        args = parser.parse_args()
        dict_args = vars(args).copy()
        dict_args.pop('func')
        dict_args.pop('command')
        args.func(**dict_args)

    def config(self, **kwargs):
        if kwargs['command'] == 'setup':
            pass
        elif kwargs['command'] == 'get':
            pass

    def pull(self, **kwargs):
        settings_list = self.settings_changer.read()
        for setting_tuple in settings_list:
            self.handler.add_pos(*setting_tuple)

    def wallpaper(self, **kwargs):
        if kwargs['wallpaper_command'] == 'setup':
            self.wp_changer.setup(kwargs['name_or_id'], fuzzy=not kwargs['strict'])
        elif kwargs['wallpaper_command'] == 'random':
            filters = {}
            if kwargs['type']:
                filters['type'] = kwargs['type'].split()
            if kwargs['contentrating']:
                filters['contentrating'] = kwargs['contentrating'].split()
            elif kwargs['nsfw']:
                filters['contentrating'] = ['Everyone', 'Unspecified', 'Questionable', 'Mature']
            if kwargs['tags']:
                filters['tags'] = kwargs['tags'].split()

            self.wp_changer.setup_random(filters=filters)

        elif kwargs['wallpaper_command'] == 'name':
            id, name = self.wp_changer.get_last_id_name()
            print(f'<{id}> "{name}"')

        elif kwargs['wallpaper_command'] == 'accent':
            id, _ = self.wp_changer.get_last_id_name()
            wp_data = self.handler.get_data(id)
            rgb_str = wp_data['general']['properties']['schemecolor']['value']
            rgb_vals = [int(float(val)*255) for val in rgb_str.split()]
            print("{} {} {}".format(*rgb_vals))

        elif kwargs['wallpaper_command'] == 'get':
            id, _ = self.wp_changer.get_last_id_name()
            wp_data = self.handler.get_data(id)

            def recursion_dict_printer(my_dict, level=0):
                for name, val in my_dict.items():
                    if isinstance(val, dict):
                        recursion_dict_printer(my_dict[name], level+1)
                    else:
                        print(f'{"  "*level} {name}="{val}"')
            recursion_dict_printer(wp_data)

        elif kwargs['wallpaper_command'] == 'like':
            wp_id, _ = self.wp_changer.get_last_id_name()
            self.handler.add_subpos(wp_id, 'freq', 2.0)
            print(f'I like this wallpaper! ({self.wp_changer.get_last_id_name()[1]})')

        elif kwargs['wallpaper_command'] == 'dislike':
            wp_id, _ = self.wp_changer.get_last_id_name()
            self.handler.add_subpos(wp_id, 'freq', 0.5)
            print(f'Show less of ({self.wp_changer.get_last_id_name()[1]}) please')

    def undo(self, **kwargs):
        undoable_settings = self.settings_changer.settings_list
        for name in undoable_settings:
            if name == "SteamLibraryPath":
                continue
            val = self.handler.get_data(name)
            self.settings_changer.setup(name, val)

    def update(self, **kwargs):
        self.wp_changer.get_all_data()

    def settings(self, **kwargs):
        if kwargs['settings_command'] == 'setup':
            self.settings_changer.setup(kwargs['subcommand'], kwargs['val'])
        elif kwargs['settings_command'] == 'get':
            print(self.settings_changer.read(kwargs['subcommand']))


if __name__ == "__main__":
    Plugin()

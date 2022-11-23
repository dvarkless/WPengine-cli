import argparse
import logging
import sys
from logging import handlers as log_handlers
from pathlib import Path

from changers import SettingsChanger, WallpaperChanger
from config_handler import ConfigHandler
from constants import LOG_PATH
from exception_handler import handle_exception

sys.excepthook = handle_exception

formatter = logging.Formatter(
    '%(asctime)s - [%(levelname)s] - [%(module)s] - "%(message)s"')
logging_handler = log_handlers.TimedRotatingFileHandler(
    LOG_PATH, when='D', interval=2, backupCount=3)
logging_handler.setFormatter(formatter)


class Plugin:
    def __init__(self, logging_handler=None) -> None:
        # defining logger:
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        if logging_handler is None:
            formatter = logging.Formatter(
                '%(asctime)s - [%(levelname)s] - [%(module)s] - "%(message)s"')
            logging_handler = log_handlers.TimedRotatingFileHandler(
                LOG_PATH, when='D', interval=7, backupCount=3)
            logging_handler.setFormatter(formatter)
        self.logger.addHandler(logging_handler)
        # defining argument parser:
        self.logger.info('============PROGRAM STARTED============')
        parser = argparse.ArgumentParser(
            description='CLI for Wallpaper Engine KDE tool')
        subparsers = parser.add_subparsers(dest='command')
        wallpaper_parser = subparsers.add_parser(
            'wallpaper', help='Operations with the wallpaper')
        wallpaper_parser.set_defaults(func=self.wallpaper)

        wallpaper_subparsers = wallpaper_parser.add_subparsers(
            dest='wallpaper_command')
        setup_wallpaper_parser = wallpaper_subparsers.add_parser('setup')
        setup_wallpaper_parser.add_argument(
            '--strict', help='disable fuzzy finder then searching by title', action=argparse.BooleanOptionalAction, default=False)
        setup_wallpaper_parser.add_argument('name_or_id', help='Name or ID')
        setup_wallpaper_parser.add_argument('--apply-accent-color', help='Apply accent color from wallpaper config in your KDE plasma',
                                            action=argparse.BooleanOptionalAction, default=False)
        random_wallpaper_parser = wallpaper_subparsers.add_parser('random')
        random_wallpaper_parser.add_argument(
            '--type', help='Type of wallpapers to choose from. Syntax: "--type scene,video,web"', choices=['scene', 'video', 'web'])
        random_wallpaper_parser.add_argument(
            '--contentrating', help='Filter out NSFW wallpapers and vice versa. Syntax: "--contentrating Everyone,Questionable,Mature" (Note! starts with capital letter)', choices=['Everyone', 'Questionable', 'Mature'])
        random_wallpaper_parser.add_argument(
            '--tags', help='Filter by tags specified in wallpaper description. Syntax: "--tags Nature,Anime,Game"')
        random_wallpaper_parser.add_argument(
            '--nsfw', help='Add wallpapers with rating "Mature" into the mix', action=argparse.BooleanOptionalAction, default=False)
        random_wallpaper_parser.add_argument('--apply-accent-color', help='Apply accent color from wallpaper config in your KDE plasma',
                                             action=argparse.BooleanOptionalAction, default=False)
        wallpaper_subparsers.add_parser(
            'name', help='get name of the current wallpaper')
        wallpaper_subparsers.add_parser(
            'id', help='get id of the current wallpaper')
        accent_parser = wallpaper_subparsers.add_parser(
            'accent', help='get accent color from the current wallpaper in hexadecimal RGB format')
        accent_parser.add_argument('--apply-accent-color', help='Apply accent color from wallpaper config in your KDE plasma',
                                   action=argparse.BooleanOptionalAction, default=False)
        wallpaper_subparsers.add_parser(
            'get', help='print info about current wallpaper')
        wallpaper_subparsers.add_parser(
            'like', help='show this wallpaper twice more often then calling "random" method (max is x2)')
        wallpaper_subparsers.add_parser(
            'dislike', help='show this wallpaper half as often often then calling "random" method (min is x0.5)')

        settings_parser = subparsers.add_parser(
            'settings', help="manipulate and view Wallpaper Engine's config file")
        settings_parser.set_defaults(func=self.settings)
        settings_subparsers = settings_parser.add_subparsers(
            dest='settings_command')

        setup_settings_parser = settings_subparsers.add_parser('setup')
        setup_settings_parser.add_argument('name')
        setup_settings_parser.add_argument('value')

        get_settings_parser = settings_subparsers.add_parser('get')
        get_settings_parser.add_argument('name', help='setting name')

        update_parser = subparsers.add_parser(
            'update-list', help='receive the list of available wallpapers from workshop folder for this CLI')
        update_parser.set_defaults(func=self.update_list)

        pull_parser = subparsers.add_parser(
            'pull', help='get all configurations from Wallpaper Engine KDE widget')
        pull_parser.set_defaults(func=self.pull)

        undo_parser = subparsers.add_parser(
            'undo', help='revert current wallpaper and configurations to last working state')
        undo_parser.set_defaults(func=self.undo)

        parser.add_argument('--version', action='version',
                            version='%(prog)s 0.5')
        parser.add_argument('--verbose', action=argparse.BooleanOptionalAction,
                            help='debug utility', default=False)
        self.logger.info('defining argparse complete')

        args = parser.parse_args()

        if args.verbose:
            self.print_log = True
            self.logger.debug('printing log into console')
        else:
            sys.tracebacklimit = 0
            self.print_log = False
            self.logger.debug(
                'not printing log into console, NO ERROR TRACEBACKS')

        # setup properties
        home_dir = Path().home()
        if not home_dir.exists():
            raise FileNotFoundError(
                'Please setup your "$HOME" environment variable')
        self.handler = ConfigHandler(logging_handler=logging_handler)
        self.steamdir = self.handler.get_data('SteamLibraryPath')

        self.settings_changer = SettingsChanger(
            self.steamdir, logging_handler=logging_handler)
        self.wp_changer = WallpaperChanger(
            self.steamdir, logging_handler=logging_handler)

        # run method from argparse
        dict_args = vars(args).copy()
        self.logger.debug(f'called with arguments: {dict_args}')
        dict_args.pop('func')
        dict_args.pop('command')
        args.func(**dict_args)

        self.logger.info('program finished with sys.exit code 0')

    def pull(self, **kwargs):
        self.logger.info(f'called method [pull] with arguments: ({kwargs})')
        settings_list = self.settings_changer.read()
        for setting_tuple in settings_list:
            self.logger.debug(f'adding setting {setting_tuple} to config')
            self.handler.add_pos(*setting_tuple)

    def wallpaper(self, **kwargs):
        self.logger.info(
            f'called method [wallpaper] with arguments: ({kwargs})')
        if kwargs['wallpaper_command'] == 'setup':
            self.logger.debug(
                f'wallpaper setup "{kwargs["name_or_id"]}", strict={kwargs["strict"]}')
            self.wp_changer.setup(
                kwargs['name_or_id'], fuzzy=not kwargs['strict'])

        elif kwargs['wallpaper_command'] == 'random':
            filters = {}
            if kwargs['type']:
                filters['type'] = kwargs['type'].split()
            if kwargs['contentrating']:
                filters['contentrating'] = kwargs['contentrating'].split()
            elif kwargs['nsfw']:
                filters['contentrating'] = ['Everyone',
                                            'Unspecified', 'Questionable', 'Mature']
            else:
                # hide this stuff if user not specified otherwise
                filters['contentrating'] = ['Everyone',
                                            'Unspecified', 'Questionable']
            if kwargs['tags']:
                filters['tags'] = kwargs['tags'].split()

            self.logger.debug(
                f'wallpaper random with filters: "{filters}"')
            self.wp_changer.setup_random(filters=filters)

        elif kwargs['wallpaper_command'] == 'name':
            self.logger.debug(f'wallpaper name')
            id, name = self.wp_changer.get_last_id_name()
            output = f'<{id}> "{name}"'
            self.logger.info(f'program output = "{output}"')
            print(output)

        elif kwargs['wallpaper_command'] == 'id':
            self.logger.debug(f'wallpaper id')
            id, name = self.wp_changer.get_last_id_name()
            self.logger.info(f'program output = "{id}"')
            print(id)

        elif kwargs['wallpaper_command'] == 'accent':
            self.logger.debug('wallpaper accent')
            id, _ = self.wp_changer.get_last_id_name()
            wp_data = self.handler.get_data(id)
            try:
                rgb_str = wp_data['general']['properties']['schemecolor']['value']
            except TypeError:
                self.logger.error(
                    'this wallpaper doesn\'t have a scheme color')
                print('ERROR: this wallpaper doesn\'t have a scheme color')
                sys.exit(1)
            rgb_vals = [int(float(val)*255) for val in rgb_str.split()]
            output = '#%02x%02x%02x' % tuple(rgb_vals)
            self.logger.info(f'program output = "{output}"')
            print(output)

        elif kwargs['wallpaper_command'] == 'get':
            self.logger.debug('wallpaper get')
            id, _ = self.wp_changer.get_last_id_name()
            wp_data = self.handler.get_data(id)

            def recursion_dict_printer(my_dict, level=0):
                for name, val in my_dict.items():
                    if isinstance(val, dict):
                        recursion_dict_printer(my_dict[name], level+1)
                    else:
                        output = f'{"  "*level} {name}="{val}"'
                        self.logger.info(output)
                        print(output)
            recursion_dict_printer(wp_data)

        elif kwargs['wallpaper_command'] == 'like':
            self.logger.debug('wallpaper like')
            wp_id, _ = self.wp_changer.get_last_id_name()
            self.handler.add_subpos(wp_id, 'freq', 2.0)
            output = f'I like this wallpaper! ({self.wp_changer.get_last_id_name()[1]})'
            self.logger.info(output)
            print(output)

        elif kwargs['wallpaper_command'] == 'dislike':
            self.logger.debug('wallpaper dislike')
            wp_id, _ = self.wp_changer.get_last_id_name()
            self.handler.add_subpos(wp_id, 'freq', 0.5)
            output = f'Show less of ({self.wp_changer.get_last_id_name()[1]}) please'
            self.logger.info(output)
            print(output)

        if kwargs.get('apply_accent_color', False):
            id, _ = self.wp_changer.get_last_id_name()
            wp_data = self.handler.get_data(id)
            try:
                rgb_str = wp_data['general']['properties']['schemecolor']['value']
            except TypeError:
                self.logger.error(
                    'this wallpaper doesn\'t have a scheme color')
                print('ERROR: this wallpaper doesn\'t have a scheme color')
                sys.exit(1)
            rgb_vals = tuple([int(float(val)*255) for val in rgb_str.split()])
            if rgb_vals == (0, 0, 0):
                try:
                    output = self.handler.get_data('default_color')
                except KeyError:
                    self.logger.info('Cannot access "default color" property')
                    sys.exit(1)
            else:
                output = '#%02x%02x%02x' % rgb_vals
            self.handler.execute_script(
                'plasma-apply-colorscheme', '--accent-color', output)

    def undo(self, **kwargs):
        self.logger.info(f'called method [undo] with arguments: ({kwargs})')
        undoable_settings = self.settings_changer.settings_list
        for name in undoable_settings:
            if name == "SteamLibraryPath":
                continue
            val = self.handler.get_data(name)
            self.settings_changer.setup(name, val)

    def update_list(self, **kwargs):
        self.logger.info(
            f'called method [update_list] with arguments: ({kwargs})')
        self.wp_changer.get_all_data()

    def settings(self, **kwargs):
        self.logger.info(
            f'called method [settings] with arguments: ({kwargs})')
        if kwargs['settings_command'] == 'setup':
            self.settings_changer.setup(kwargs['name'], kwargs['value'])
        elif kwargs['settings_command'] == 'get':
            output = self.settings_changer.read(kwargs['name'])
            self.logger.info(output)
            print(output)


if __name__ == "__main__":
    Plugin(logging_handler)

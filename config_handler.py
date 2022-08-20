import json
import logging
from logging import handlers as log_handlers
from pathlib import Path

import dbus

from constants import CONFIG_PATH, LOG_PATH


class ConfigHandler:
    __template = {
        'SteamLibraryPath': '/path/to/SteamLibrary',
        'last_id': '000000',
        'prev_ids': ['000', '001', '002', '003'],
        'WallpaperEngineSteamID': '431960',
        'WallpaperProjectName': 'project.json',
        'WallpaperWorkShopId': '12345',
        'WallpaperSource': 'path/to/wallpaper',
    }

    def __init__(self, logging_handler=None) -> None:
        if logging_handler is None:
            formatter = logging.Formatter(
                '%(asctime)s - [%(levelname)s] - [%(module)s] - "%(message)s"')
            file_handler = log_handlers.TimedRotatingFileHandler(
                LOG_PATH, when='D', interval=7, backupCount=3)
            file_handler.setFormatter(formatter)
            logging_handler = file_handler
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging_handler)

        if not CONFIG_PATH.exists():
            print(f'Could not find a configuration file at "{CONFIG_PATH}"')
            result = input("Create a new config? y/n \n")
            if result == 'y':
                self.write_template()
            else:
                self.logger.info('program finished with exit code 1')
                exit(1)

    def get_data(self, key=None):
        self.logger.debug(f'called method [get_data] with arguments (key={key})')
        with open(CONFIG_PATH, 'r') as conf:
            data = json.load(conf)
            self.logger.debug('json load')
        if key is None:
            self.logger.debug(f'returning value (all data with len={len(data)}')
            return data
        else:
            self.logger.debug(f'returning value (data[key] with {len(data[key])} positions)')
            return data[key]

    def get_ids(self):
        self.logger.debug('called method [get_ids]')
        data = self.get_data()
        to_remove = []
        for name in data.keys():
            try:
                int(name)
            except ValueError:
                to_remove.append(name)
        for name in to_remove:
            del data[name]
        if not data:
            error_msg = f"Cannot find wallpapers in config file, did you call 'wengine update'?"
            self.logger.error(
                f'Hangled exception: "{error_msg}", program finished')
            raise ValueError(error_msg)
        self.logger.debug(f'returning value (data with len={len(data)})')
        return data

    def update_last_ids(self, id, /):
        self.logger.debug(f'called method [update_last_ids] with arguments (id={id})')
        prev_ids = self.get_data('prev_ids')
        prev_ids.pop(0)
        prev_ids.append(id)
        self.add_pos('prev_ids', prev_ids)
        self.add_pos('last_id', id)

    def add_pos(self, id, data):
        self.logger.debug(f'called method [add_pos] with arguments (id={id}, data=data with len={len(data)})')
        all_data = self.get_data()
        self.logger.debug(f'in position ({id}) add value ({data})')
        all_data[id] = data

        with open(CONFIG_PATH, 'w') as conf:
            json.dump(all_data, conf)
            self.logger.debug('json dump')

    def add_subpos(self, id, subpos, data):
        self.logger.debug(f'called method [add_subpos] with arguments (id={id}, subpos={subpos}, data={data})')
        all_data = self.get_data()
        self.logger.debug(f'in position ({id}), subposition ({subpos}) add value ({data})')
        all_data[id][subpos] = data

        with open(CONFIG_PATH, 'w') as conf:
            json.dump(all_data, conf)
            self.logger.debug('json dump')

    def remove_pos(self, name, /):
        self.logger.debug(f'called method [remove_pos] with arguments (name={name})')
        all_data = self.get_data()
        try:
            self.logger.info(f'remove ({all_data[name]})')
            del all_data[name]
        except KeyError:
            error_msg = f"This key ({name}) does not exist in config file. Direct call??"
            self.logger.error(
                f'Hangled exception: "{error_msg}", program finished')
            raise KeyError(error_msg)
        with open(CONFIG_PATH, 'w') as conf:
            json.dump(all_data, conf)
            self.logger.debug('json dump')

    def send_cmd(self, id, val):
        self.logger.debug(f'called method [send_cmd] with arguments (id={id}, val={val})')
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
        self.logger.debug(f'called method [write_template]')
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, 'w') as file:
            json.dump(ConfigHandler.__template, file)
            self.logger.debug('json dump')

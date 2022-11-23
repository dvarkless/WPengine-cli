import json
import logging
import os
import re
from difflib import SequenceMatcher
from logging import handlers as log_handlers
from pathlib import Path
from random import choices

from config_handler import ConfigHandler
from constants import LOG_PATH


class SettingsChanger():
    __header_regex = \
        r".+\[Wallpaper\]\[com\.github\.casout\.wallpaperEngineKde\]\[General\]"
    __kde_config_path = Path(
        "~/.config/plasma-org.kde.plasma.desktop-appletsrc").expanduser()

    def __init__(self, steampath, logging_handler=None) -> None:
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

        self._steampath = Path(steampath)
        self.handler = ConfigHandler(
            logging_handler=logging_handler)

        wpe_id = self.handler.get_data('WallpaperEngineSteamID')
        self.project_name = self.handler.get_data('WallpaperProjectName')
        self.full_path = self._steampath / \
            Path('steamapps/workshop/content') / wpe_id

        self.name_to_pattern = {
            'DisplayMode': re.compile(r"DisplayMode=(\d+)"),
            'Fps': re.compile(r"Fps=(\d+)"),
            'MuteAudio': re.compile(r"MuteAudio=(\w+)"),
            'SortMode': re.compile(r"SortMode=(\d)"),
            'SteamLibraryPath': re.compile(r"SteamLibraryPath.+=file://(.+)"),
            'Volume': re.compile(r"Volume=(\d+)"),
            'WallpaperSource': re.compile(r"WallpaperSource.+.+=(file://.+)"),
            'WallpaperWorkShopId': re.compile(r"WallpaperWorkShopId=(\d+)"),
        }
        self.name_type_check = {
            'DisplayMode': lambda x: int(x) >= 0 and int(x) < 20,
            'Fps': lambda x: int(x) > 0 and int(x) <= 60,
            'MuteAudio': lambda x: x in ("false", "true"),
            'SortMode': lambda x: x in "123",
            'SteamLibraryPath': lambda x: isinstance(x, str),
            'Volume': lambda x: int(x) >= 0 and int(x) <= 100,
            'WallpaperSource': lambda x: isinstance(x, str),
            # Basically check if int(x) is possible
            'WallpaperWorkShopId': lambda x: isinstance(int(x), int),
        }
        self.start_line = self.get_start_line()

    @property
    def settings_list(self):
        self.logger.debug('get settings list')
        return list(self.name_to_pattern.keys())

    @settings_list.setter
    def settings_list(self, _):
        pass

    def setup(self, name, val):
        self.logger.debug(
            f'called method [setup] with arguments (name={name}, val={val})')
        if name in self.name_to_pattern.keys():
            if not self.name_type_check[name](val):
                error_msg = f'Invalid value ({val}) for setting "{name}"'
                self.logger.error(
                    f'Hangled exception: "{error_msg}", program finished')
                raise ValueError(error_msg)

            self.handler.send_cmd(name, val)
        else:
            self.handler.add_pos(name, val)

    def read(self, setting=None):
        self.logger.debug(
            f'called method [read] with arguments (setting={setting})')
        if setting is not None:
            if setting not in self.name_to_pattern.keys():
                return self.handler.get_data(setting)

        return_list = []
        chapter_end_pattern = re.compile(r"\n\n")
        with open(SettingsChanger.__kde_config_path, 'r') as file:
            for i, line in enumerate(file):
                if i < getattr(self, 'start_line', -1):
                    continue

                if setting is not None:
                    pattern_iter = [(setting, self.name_to_pattern[setting])]
                else:
                    pattern_iter = self.name_to_pattern.items()

                for name, pattern in pattern_iter:
                    match = pattern.search(line)
                    if match:
                        return_list.append((name, match.group(1)))

                if chapter_end_pattern.match(line):
                    break  # Used to not possibly overwrite found settings
        self.logger.debug(f'returning value ({return_list})')
        return return_list

    def get_start_line(self):
        self.logger.debug(f'called method [get_start_line]')
        pattern = re.compile(SettingsChanger.__header_regex)
        with open(SettingsChanger.__kde_config_path, 'r') as file:
            for i, line in enumerate(file):
                if pattern.match(line):
                    self.logger.debug(f'returning value ({i})')
                    return i
            else:
                error_msg = "WallpaperEngine settings are not found in plasma config"
                self.logger.error(
                    f'Hangled exception: "{error_msg}", program finished')
                raise ValueError(error_msg)


class WallpaperChanger():
    def __init__(self, steampath, logging_handler=None) -> None:
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

        self.handler = ConfigHandler(
            logging_handler=logging_handler)
        self.settings_changer = SettingsChanger(
            steampath, logging_handler=None)
        self._steampath = Path(steampath)

        wpe_id = self.handler.get_data('WallpaperEngineSteamID')
        self.project_name = self.handler.get_data('WallpaperProjectName')
        self.full_path = self._steampath / \
            Path('steamapps/workshop/content') / wpe_id

    def get_data(self, wp_path: Path, files: list):
        self.logger.debug(
            f'called method [get_data] with arguments (wp_path={wp_path}, files={files})')
        if self.project_name in files:
            with open(Path(wp_path) / self.project_name, 'r') as file:
                data = json.load(file)
                self.handler.add_pos(Path(wp_path).name, data)

    def get_all_data(self):
        self.logger.debug(f'called method [get_all_data]')
        for root, _, files in os.walk(self.full_path):
            self.get_data(Path(root), files)

    def get_last_id_name(self):
        self.logger.debug('called method [get_last_id_name]')
        id = self.settings_changer.read('WallpaperWorkShopId')
        data = self.handler.get_data()
        try:
            name = data[id]['title']
        except KeyError:
            error_msg = f'Could not find a wallpaper by id:{id}'
            self.logger.error(
                f'Hangled exception: "{error_msg}", program finished')
            raise FileNotFoundError(error_msg)
        self.logger.debug(f'returning value ({(id, name)})')
        return id, name

    def setup(self, name, *, silent_delete=False, fuzzy=True):
        self.logger.debug(
            f'called method [setup] with arguments (name={name}, silent_delete={silent_delete}, fuzzy={fuzzy})')
        if type(name) in (tuple, list, set):
            name = name[0]
        name_id = None
        wp_data = self.handler.get_ids()
        compare_results = []
        for id, vals in wp_data.items():
            name_id = id
            if name == id:
                break
            if name.isdigit():
                continue
            s = SequenceMatcher(a=name.casefold(), b=vals['title'].casefold())
            ratio = s.quick_ratio()
            len_match = s.find_longest_match().size
            if ratio > 0.5 if fuzzy else ratio > 0.95:
                compare_results.append((id, ratio*len_match))
        else:
            if not compare_results:
                raise KeyError(f'Bad name or id: "{name}"')
            else:
                compare_results.sort(key=lambda x: x[1], reverse=True)
                name_id = compare_results[0][0]

        wp_type = wp_data[name_id]['type'].lower()
        self.handler.send_cmd('WallpaperWorkShopId', name_id)

        tail = wp_data[name_id]['file'] + '+' + wp_type
        wp_path = self.full_path / Path(name_id) / Path(tail)
        if not Path(self.full_path / Path(name_id)).exists():
            if silent_delete:
                self.handler.remove_pos(name_id)
                return True
            else:
                print(f'error path: "{wp_path}"')
                raise KeyError(
                    f'This id not exists: "{name_id}" with name "{name}"')
        # wp_path.as_uri() breaks encoding
        self.handler.send_cmd('WallpaperSource', 'file://'+str(wp_path))
        self.handler.update_last_ids(name_id)

    def _parse_into_str(self, data, name):
        out = data.get(name, 'Unspecified')
        if isinstance(out, list):
            return out[0]
        if isinstance(out, tuple):
            return out[0]
        else:
            return str(out)

    def setup_random(self, *, filters={}, fuzzy=True):
        self.logger.debug(
            f'called method [setup_random] with arguments (filters={filters}, fuzzy={fuzzy})')
        wp_ids = self.handler.get_ids()
        all_data = self.handler.get_data()
        new_ids = {}
        for id, data in wp_ids.items():
            # Check if value in data also contains in filters
            if all([self._parse_into_str(data, name) in val for name, val in filters.items()]):
                new_ids[id] = data
        if not filters:
            new_ids = wp_ids
        if not new_ids:
            error_msg = f"Could not find wallpapers with this filters: {filters}"
            self.logger.error(
                f'Hangled exception: "{error_msg}", program finished')
            raise ValueError(error_msg)

        last_ids = self.handler.get_data('prev_ids')
        weights = []
        for id in new_ids:
            try:
                freq = float(all_data[id]['freq'])
            except KeyError:
                freq = 1.0
            if id in last_ids:
                weights.append(0.1*freq)
            else:
                weights.append(freq)

        if self.setup(choices(list(new_ids.keys()), weights=weights), silent_delete=True, fuzzy=fuzzy):
            self.logger.info(
                f'setup_random failed because got non-existent id, recursive calling itself again')
            self.setup_random(filters=filters, fuzzy=fuzzy)

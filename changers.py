import json
import os
import re
from difflib import SequenceMatcher
from pathlib import Path
from random import choices

from config_handler import ConfigHandler


class SettingsChanger():
    __header_regex = \
        r".+\[Wallpaper\]\[com\.github\.casout\.wallpaperEngineKde\]\[General\]"
    __kde_config_path = Path(
        "~/.config/plasma-org.kde.plasma.desktop-appletsrc").expanduser()
    def __init__(self, steampath, config_path) -> None:
        self._steampath = Path(steampath)
        self.handler = ConfigHandler(config_path)

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
        return list(self.name_to_pattern.keys())

    @settings_list.setter
    def settings_list(self, _):
        pass

    def setup(self, name, val):
        if not (name in self.name_to_pattern.keys()):
            raise KeyError(f'Passed name - "{name}" is an unknown setting')
        if not self.name_type_check[name](val):
            raise ValueError(f'Invalid value ({val}) for setting "{name}"')

        self.handler.send_cmd(name, val)

    def read(self, setting=None):
        if setting is not None:
            if setting not in self.name_to_pattern.keys():
                raise KeyError(f"Bad setting name - '{setting}'")

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
                    break # Used to not possibly overwrite found settings

        return return_list

    def get_start_line(self):
        pattern = re.compile(SettingsChanger.__header_regex)
        with open(SettingsChanger.__kde_config_path, 'r') as file:
            for i, line in enumerate(file):
                if pattern.match(line):
                    return i
            else:
                raise ValueError(
                    "WallpaperEngine settings are not found in plasma config")


class WallpaperChanger():
    def __init__(self, steampath, config_path) -> None:
        self.handler = ConfigHandler(config_path)
        self._steampath = Path(steampath)

        wpe_id = self.handler.get_data('WallpaperEngineSteamID')
        self.project_name = self.handler.get_data('WallpaperProjectName')
        self.full_path = self._steampath / \
            Path('steamapps/workshop/content') / wpe_id

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
                    SequenceMatcher(
                        a=name.casefold(), b=vals['title'].casefold()).real_quick_ratio()
                    break
        else:
            raise KeyError(f'Bad name or id: "{name}"')

        wp_type = wp_data[name_id]['type'].lower()
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
        # wp_path.as_uri() breaks encoding
        self.handler.send_cmd('WallpaperSource', 'file://'+str(wp_path))
        self.handler.update_last_ids(id)

    def setup_random(self, **filters):
        # TODO: instead of returning first file with >80% coincedence
        # get a list with % coincedence and return file with biggest % > 50%
        wp_ids = self.handler.get_ids()
        new_ids = {}
        for name, val in filters.items():
            for id, data in wp_ids.items():
                if isinstance(val, list):
                    if data.get(name, ['Unspecified'])[0] in val:
                        new_ids[id] = data
                if val in (int, float, str):
                    if data.get(name, ['Unspecified'])[0] == val:
                        new_ids[id] = data
        if len(filters) == 0:
            new_ids = wp_ids
        if len(new_ids) == 0:
            raise ValueError(
                f"Could not find wallpapers with this filters: {filters}")

        last_ids = self.handler.get_data('prev_ids')
        weights = []
        for id in new_ids:
            if id in last_ids:
                weights.append(0.1)
            else:
                weights.append(1)
        if self.setup(choices(list(new_ids.keys()), weights=weights)):
            print(
                f'setup_random failed because got non-existent id, recursive calling itself again')
            self.setup_random(**filters)

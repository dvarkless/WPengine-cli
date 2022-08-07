import json
import os
from difflib import SequenceMatcher
from pathlib import Path
from random import choices

from config_handler import ConfigHandler


class SettingsChanger():
    def __init__(self, steampath, config_path) -> None:
        self._steampath = Path(steampath)
        self.handler = ConfigHandler(config_path)

        wpe_id = self.handler.get_data('WallpaperEngineSteamID')
        self.project_name = self.handler.get_data('WallpaperProjectName')
        self.full_path = self._steampath / \
            Path('steamapps/workshop/content') / wpe_id

    def setup(self):
        raise NotImplementedError


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
                    if SequenceMatcher(a=name, b=vals['title']).ratio() > 0.8:
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
        # add file:// if as_uri raises exception
        self.handler.send_cmd('WallpaperSource', 'file://'+str(wp_path))
        self.handler.update_last_ids(id)

    def setup_random(self, **filters):
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

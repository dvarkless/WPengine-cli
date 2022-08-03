import os
import sys
import pathlib
import argparse
import json

def get_arguments():
    parser = argparse.ArgumentParser(prog='Wengine-cli')

    parser.add_argument( '--random', action=argparse.BooleanOptionalAction, help='Setup random wallpaper from WallpaperEngine directory', default=False)
    parser.add_argument( '--undo', action=argparse.BooleanOptionalAction, help='Return previous wallpaper. Useful then you got a black screen', default=False)
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('--steamdir',type=pathlib.Path, help='Specify your Steam directory with this argument') 
    parser.add_argument( '--verbose', action=argparse.BooleanOptionalAction, help='Debug utility', default=False)
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
                'STEAM_DIR': '/path/to/SteamLibrary',
                'last_id': '000000',
                'prev_ids': ['000', '001','002', '003']
                }
        json.dump(struct, file)

def return_type(root_dir: os.PathLike, wallpaper_id: os.PathLike):
    full_path = os.path.join(root_dir, wallpaper_id)
    
class ConfigHandler:
    def __init__(self, config_path: os.PathLike) -> None:
        self.config = config_path

    def _get_kdata(self, key):
        with open(self.config, 'r') as conf:
            data = json.load(conf)

        return data[key]

    def get_data(self, key):
        self._get_kdata(key)

class SettingsChanger:
    def __init__(self, steampath) -> None:
        self._steampath = steampath
        
    
    @property
    def path_with_home(self):
        return self._path_with_home
    
    @path_with_home.setter
    def path_with_home(self, rel_path: os.PathLike):
        self._path_with_home = os.path.expanduser(rel_path)

    @property
    def full_path(self):
        return self._full_path

    @full_path.setter
    def full_path(self, rel_path: os.PathLike):
        self._full_path = os.path.join(self._steampath, rel_path)

        
    
def main():
    pass

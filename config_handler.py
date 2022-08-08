import json
from pathlib import Path

import dbus


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
            except ValueError:
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

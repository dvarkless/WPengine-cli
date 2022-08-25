# WPengine-cli
Custom command line interface for Wallpaper Engine for KDE widget

![setup_random_preview](https://user-images.githubusercontent.com/78558029/186255486-803f991a-5ce6-42c2-b977-09c684eb1d7d.gif)

## About The Project
This program allows you to setup wallpapers from Wallpaper Engine using Command Line Interface.  
There is also additional features like changing the accent color of your desktop to match the wallpaper.  

### Prerequisites
- [Steam](https://store.steampowered.com/about/) with [Wallpaper Engine](https://store.steampowered.com/app/431960/Wallpaper_Engine/) installed
- [Wallpaper Engine Plugin for KDE Plasma](https://github.com/catsout/wallpaper-engine-kde-plugin)
- Python3 

### Installation & Post-install
   ```
    git clone https://github.com/dvarkless/WPengine-cli.git
  ```  
Now move into the repository and pull Wallpaper Engine's settings  
  ```
    cd WPengine-cli
    python wengine.py pull
  ```  
Update the list of installed wallpapers on your system (Call this each time then you install new wallpapers):
  ```
    python wengine.py update-list 
  ```
#### Optional:
if you want to create a binary file and install it in your system, install `pyinstaller` module and run `install.sh`
   ```
      pip install pyinstaller
      ./install.sh
   ```
This allows you to call this script without python, for example:
   ```
      wengine update-list
   ```

## Usage
### Setup a wallpaper

Setup a wallpaper by its id or name using `wallaper setup` argument:
  ```
    python wengine.py wallpaper setup wallpaper_id
  ```
It's not necessary to specify an exact name of the wallpaper to set it up, the script will find the closest match:
  ```
    python wengine.py wallpaper setup "snow"
    python wengine.py wallpaper name
    # >>><2190054449> "Snow [4K]"
  ```
### Setup a random wallpaper

Let's setup a random wallpaper:
  ```
    python wengine.py wallpaper random
  ```
You can also use filters to get a wallpaper of a specific type, theme or age rating.
- `--type` wallpaper type chosen from: `(Video,Scene,Web)`
- `--tags` main tag of the wallpaper, for example:`(Landscape,Cars,Anime)` and so on.
- `--contentrating` specify age rating of the wallpapers, chosen from: `(Everyone,Questionable,Mature)`.  
NOTE: rating `Mature` is filtered out by default  
Usage example:
  ```
    python wengine.py wallpaper random --tags Anime,Game --type Video,Web --contentrating Everyone
  ```
  
### Apply accent color of the wallpaper to your system
You can see the effect of this feature in the lower left-hand corner of this gif:
![accent_color_preview](https://user-images.githubusercontent.com/78558029/186417741-19398c86-f184-400a-a862-3dcc3f79acba.gif)  
Before applying an accent color, I recommend you to define a default accent color, because many wallpapers on the steam workshop have a #000000 schemecolor, which is not in sync wallpapers and looks bad.
  ```
    python wengine.py settings setup default_color "#213658"
  ```
choose any color you want, instead of `#213658`. Color defined in [HEX](https://www.color-hex.com) format.  

Apply a colorscheme of the current wallpaper:
  ```
    python wengine.py wallpaper accent --apply-accent-color
  ```
Setup a random wallpaper and change an accent color accordingly:
  ```
    python wengine.py wallpaper random --apply-accent-color
  ```
This works with `setup` too:
  ```
    python wengine.py wallpaper setup "best_wallpaper_ever" --apply-accent-color
  ```
  
### Other
Get all the available commands:
  ```
    python wengine.py --help
    python wengine.py wallpaper --help
  ```
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

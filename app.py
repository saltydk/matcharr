from classes.timer import *
from classes.arr import *
from utils import *

runtime = Timer()

config_timer = Timer()
print("Loading Configuration")
config = json.load(open("config.json"))
sonarr_config = [*config["sonarr"]]
radarr_config = [*config["radarr"]]

sonarrs_config = {}
for x in sonarr_config:
    sonarrs_config[x] = config["sonarr"][x]

radarrs_config = {}
for x in radarr_config:
    radarrs_config[x] = config["radarr"][x]

print(f"Loading Configuration took {config_timer.stop()} seconds.")

media_timer = Timer()
print("Loading Data From Plex, Sonarr & Radarr")

media = {"sonarr": {}, "radarr": {}}
for x in [*sonarrs_config]:
    media["sonarr"][x] = Arr(sonarrs_config[x]["url"],
                             sonarrs_config[x]["apikey"],
                             "series").data

for x in [*radarrs_config]:
    media["radarr"][x] = Arr(radarrs_config[x]["url"],
                             radarrs_config[x]["apikey"],
                             "movie").data

sonarr = {}
radarr = {}
plexlibrary = {}

load_data(media, sonarr, radarr, plexlibrary, config, sonarrs_config, radarrs_config)

print(f"Loading Data From Plex, Sonarr & Radarr took {media_timer.stop()} seconds.")

faulty_timer = Timer()
print("Checking for faulty data in Radarr & Sonarr")

check_faulty(radarrs_config, radarr)
check_faulty(sonarrs_config, sonarr)

print(f"Checking for faulty data in Radarr & Sonarr took {faulty_timer.stop()} seconds.")

plex_duplicate_timer = Timer()
print("Checking for Duplicate Media")

duplicate = check_duplicate(plexlibrary, config)

print(f"Checking for Duplicate Media took {plex_duplicate_timer.stop()} seconds.")

if duplicate == 1:
    reload_timer = Timer()
    print(f"Reloading Data due to duplicate item(s) in Plex")

    sonarr = {}
    radarr = {}
    plexlibrary = {}

    load_data(media, sonarr, radarr, plexlibrary, config, sonarrs_config, radarrs_config)

    print(f"Reloading Data took {reload_timer.stop()} seconds.")

print("Checking for Mismatched Media")
plex_mismatch_timer = Timer()

compare_media(radarrs_config, radarr, plexlibrary, "themoviedb", config)
compare_media(sonarrs_config, sonarr, plexlibrary, "thetvdb", config)

print(f"Checking for Mismatched Media took {plex_mismatch_timer.stop()} seconds.")
print(f"Running the program took {runtime.stop()} seconds.")

exit(0)
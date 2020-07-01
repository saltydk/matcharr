from classes.timer import *
from classes.arr import *
from utils import *

runtime = Timer()

config_timer = Timer()
print("Loading Configuration")
config = json.load(open("config.json"))
sonarr_config = [*config["sonarr"]]
radarr_config = [*config["radarr"]]
delay = config["delay"]
plex_sections = {}
sonarrs_config = {}
for x in sonarr_config:
    sonarrs_config[x] = config["sonarr"][x]
    plex_sections[config["sonarr"][x]["library_id"]] = "shows"

radarrs_config = {}
for x in radarr_config:
    radarrs_config[x] = config["radarr"][x]
    plex_sections[config["radarr"][x]["library_id"]] = "movie"

print(f"Loading Configuration took {config_timer.stop()} seconds.")

# Load data from Arr instances.
arr_timer = Timer()
print("Loading data from Arr instances")

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

load_arr_data(media, sonarr, radarr)

print(f"Loading data from Arr instances took {arr_timer.stop()} seconds.")

# Load data from Plex.
plex_timer = Timer()
print("Loading data from Plex")

load_plex_data(plexlibrary, config, plex_sections, delay)

print(f"Loading data from Plex took {plex_timer.stop()} seconds.")

# Check for duplicate entries in Arr instances.
faulty_timer = Timer()
print("Checking for faulty data in Radarr & Sonarr")

check_faulty(radarrs_config, radarr)
check_faulty(sonarrs_config, sonarr)

print(f"Checking for faulty data in Radarr & Sonarr took {faulty_timer.stop()} seconds.")

# Check for duplicate entries in Plex.
plex_duplicate_timer = Timer()
print("Checking for Duplicate Media")

duplicate = check_duplicate(plexlibrary, config, delay)

print(f"Checking for Duplicate Media took {plex_duplicate_timer.stop()} seconds.")

# Reload Plex data if duplicate items were found in Plex.
if duplicate == 1:
    reload_timer = Timer()
    print(f"Reloading data due to duplicate item(s) in Plex")

    plexlibrary = {}

    load_plex_data(plexlibrary, config, plex_sections, delay)

    print(f"Reloading data took {reload_timer.stop()} seconds.")

# Check for mismatches entries and correct them.
print("Checking for Mismatched Media")
plex_mismatch_timer = Timer()

compare_media(radarrs_config, radarr, plexlibrary, "themoviedb", config, delay)
compare_media(sonarrs_config, sonarr, plexlibrary, "thetvdb", config, delay)

print(f"Checking for Mismatched Media took {plex_mismatch_timer.stop()} seconds.")
print(f"Running the program took {runtime.stop()} seconds.")

exit(0)

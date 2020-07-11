from classes.timer import *
from classes.arr import *
from utils import *

runtime = Timer()

config_timer = Timer()
print(f"{timeoutput()} - Loading Configuration")
config = json.load(open("config.json"))
sonarr_config = [*config["sonarr"]]
radarr_config = [*config["radarr"]]
delay = config["delay"]
emby_enabled = config["emby_enabled"]
plex_enabled = config["plex_enabled"]
plex_sections = {}
emby_sections = {}

sonarrs_config = {}
for x in sonarr_config:
    sonarrs_config[x] = config["sonarr"][x]

    if plex_enabled and config["sonarr"][x]["plex_library_id"] != "None":
        plex_sections[config["sonarr"][x]["plex_library_id"]] = "shows"

    if emby_enabled and config["sonarr"][x]["emby_library_id"] != "None":
        emby_sections[config["sonarr"][x]["emby_library_id"]] = "shows"

radarrs_config = {}
for x in radarr_config:
    radarrs_config[x] = config["radarr"][x]

    if plex_enabled and config["radarr"][x]["plex_library_id"] != "None":
        plex_sections[config["radarr"][x]["plex_library_id"]] = "movie"

    if emby_enabled and config["radarr"][x]["emby_library_id"] != "None":
        emby_sections[config["radarr"][x]["emby_library_id"]] = "movie"


print(f"{timeoutput()} - Loading Configuration took {config_timer.stop()} seconds.")

# Load data from Arr instances.
arr_timer = Timer()
print(f"{timeoutput()} - Loading data from Arr instances")

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
embylibrary = {}

load_arr_data(media, sonarr, radarr)

print(f"{timeoutput()} - Loading data from Arr instances took {arr_timer.stop()} seconds.")

if plex_enabled:
    # Load data from Plex.
    plex_timer = Timer()
    print(f"{timeoutput()} - Loading data from Plex")

    load_plex_data(plexlibrary, config, plex_sections, delay)

    print(f"{timeoutput()} - Loading data from Plex took {plex_timer.stop()} seconds.")

if emby_enabled:
    # Load data from Emby.
    emby_timer = Timer()
    print(f"{timeoutput()} - Loading data from Emby")

    load_emby_data(config, emby_sections, embylibrary)

    print(f"{timeoutput()} - Loading data from Emby took {emby_timer.stop()} seconds.")


# Check for duplicate entries in Arr instances.
faulty_timer = Timer()
print(f"{timeoutput()} - Checking for faulty data in Radarr & Sonarr")

check_faulty(radarrs_config, radarr)
check_faulty(sonarrs_config, sonarr)

print(f"{timeoutput()} - Checking for faulty data in Radarr & Sonarr took {faulty_timer.stop()} seconds.")

# Check for duplicate entries in Plex.
if plex_enabled:
    plex_duplicate_timer = Timer()
    print(f"{timeoutput()} - Checking for Duplicate Media")

    duplicate = check_duplicate(plexlibrary, config, delay)

    print(f"{timeoutput()} - Checking for Duplicate Media took {plex_duplicate_timer.stop()} seconds.")

    # Reload Plex data if duplicate items were found in Plex.
    if duplicate == 1:
        reload_timer = Timer()
        print(f"{timeoutput()} - Reloading data due to duplicate item(s) in Plex")

        plexlibrary = {}

        load_plex_data(plexlibrary, config, plex_sections, delay)

        print(f"{timeoutput()} - Reloading data took {reload_timer.stop()} seconds.")

# Check for mismatched entries and correct them.
if plex_enabled:
    print(f"{timeoutput()} - Checking for Mismatched Media in Plex")
    plex_mismatch_timer = Timer()

    plex_compare_media(radarrs_config, radarr, plexlibrary, "themoviedb", config, delay)
    plex_compare_media(sonarrs_config, sonarr, plexlibrary, "thetvdb", config, delay)

    print(f"{timeoutput()} - Checking for Mismatched Media in Plex took {plex_mismatch_timer.stop()} seconds.")

if emby_enabled:
    print(f"{timeoutput()} - Checking for Mismatched Media in Emby")
    emby_mismatch_timer = Timer()

    emby_compare_media(radarrs_config, radarr, embylibrary, "Tmdb", config, delay)
    emby_compare_media(sonarrs_config, sonarr, embylibrary, "Tvdb", config, delay)

    print(f"{timeoutput()} - Checking for Mismatched Media in Emby took {emby_mismatch_timer.stop()} seconds.")

print(f"{timeoutput()} - Running the program took {runtime.stop()} seconds.")

exit(0)

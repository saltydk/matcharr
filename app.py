from plexapi.server import PlexServer
from classes.timer import *
from classes.arr import *
from utils import *

runtime = Timer()

config = json.load(open("config.json"))
sonarr_config = config["sonarr"].keys()
radarr_config = config["radarr"].keys()
delay = config["delay"]
emby_enabled = config["emby_enabled"]
plex_enabled = config["plex_enabled"]
plex_sections = {}
emby_sections = {}

if plex_enabled:
    server = PlexServer(config["plex_url"], config["plex_token"])
    server_sections = server.library.sections()
    plex_library_paths = {}
    for section in server_sections:
        plex_library_paths[section.key] = {}
        x = 0
        for location in section.locations:
            plex_library_paths[section.key][x] = location


sonarrs_config = {}
for x in sonarr_config:
    sonarrs_config[x] = config["sonarr"][x]

    if emby_enabled and config["sonarr"][x]["emby_library_id"] != "None":
        emby_sections[config["sonarr"][x]["emby_library_id"]] = "shows"

radarrs_config = {}
for x in radarr_config:
    radarrs_config[x] = config["radarr"][x]

    if emby_enabled and config["radarr"][x]["emby_library_id"] != "None":
        emby_sections[config["radarr"][x]["emby_library_id"]] = "movie"

# Load data from Arr instances.
media = {"sonarr": {}, "radarr": {}}
paths = {"sonarr": {}, "radarr": {}}

for x in giefbar(sonarrs_config.keys(), f'{timeoutput()} - Loading data from Sonarr instances'):
    media["sonarr"][x] = Arr(sonarrs_config[x]["url"],
                             sonarrs_config[x]["apikey"],
                             "series").data
    paths["sonarr"][x] = Arr(sonarrs_config[x]["url"],
                             sonarrs_config[x]["apikey"],
                             "series").paths

for x in giefbar(radarrs_config.keys(), f'{timeoutput()} - Loading data from Radarr instances'):
    media["radarr"][x] = Arr(radarrs_config[x]["url"],
                             radarrs_config[x]["apikey"],
                             "movie").data
    paths["radarr"][x] = Arr(radarrs_config[x]["url"],
                             radarrs_config[x]["apikey"],
                             "movie").paths

sonarr = {}
radarr = {}
plexlibrary = {}
embylibrary = {}

parse_arr_data(media, sonarr, radarr)

arrpaths = get_arrpaths(paths)



if plex_enabled:
    # Load data from Plex.
    arr_plex_match = {}
    arr_plex_match = arr_find_plex_id(arrpaths, arr_plex_match, plex_library_paths, plex_sections)
    load_plex_data(server, plex_sections, plexlibrary, config)

if emby_enabled:
    # Load data from Emby.
    load_emby_data(config, emby_sections, embylibrary)

# Check for duplicate entries in Arr instances.
check_faulty(radarrs_config, radarr, "Radarr")
check_faulty(sonarrs_config, sonarr, "Sonarr")

# Check for duplicate entries in Plex.
if plex_enabled:
    duplicate = check_duplicate(server, plex_sections, config, delay)

    # Reload Plex data if duplicate items were found in Plex.
    if duplicate > 0:
        print(f"{timeoutput()} - Reloading data due to {duplicate} duplicate item(s) in Plex")

        plexlibrary = {}
        server.reload()

        load_plex_data(server, plex_sections, plexlibrary, config)

# Check for mismatched entries and correct them.
if plex_enabled:
    fixed_matches = 0
    fixed_matches += plex_compare_media(arr_plex_match, sonarr, radarr, plexlibrary, config, delay)
    print(f"{timeoutput()} - Number of fixed matches in Plex: {fixed_matches}")

if emby_enabled:
    emby_compare_media(radarrs_config, radarr, embylibrary, "Tmdb", config)
    emby_compare_media(sonarrs_config, sonarr, embylibrary, "Tvdb", config)

print(f"{timeoutput()} - Running the program took {runtime.stop()} seconds.")

exit(0)

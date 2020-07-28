from plexapi.server import PlexServer
from classes.timer import *
from classes.arr import *
from utils.emby import *
from utils.plex import *
from utils.arr import *


# TODO add logging
#  add validation for Arr/Plex/Emby config entries
#  add check for empty libraries in Plex/Emby
#  add support for anime (tentative)
#  add support for multiple Plex/Emby instances (tentative)
#  add support for forcing an agent for library types
#  add dry-run option
#  add support for specifying path mapping for media server

runtime = Timer()

config = json.load(open("config.json"))
sonarr_config = config["sonarr"].keys()
radarr_config = config["radarr"].keys()
delay = config["delay"]
emby_enabled = config["emby_enabled"]
plex_enabled = config["plex_enabled"]
plex_sections, emby_sections, sonarrs_config, radarrs_config = dict(), dict(), dict(), dict()

for x in sonarr_config:
    sonarrs_config[x] = config["sonarr"][x]

for x in radarr_config:
    radarrs_config[x] = config["radarr"][x]

if not bool(radarrs_config.keys()) and not bool(sonarrs_config.keys()):
    print(f'{timeoutput()} - No Arrs configured - Exiting.')
    exit(0)

# Load data from Arr instances.
media = {"sonarr": {}, "radarr": {}}
paths = {"sonarr": {}, "radarr": {}}

if bool(sonarrs_config.keys()):
    for x in giefbar(sonarrs_config.keys(), f'{timeoutput()} - Loading data from Sonarr instances'):
        media["sonarr"][x] = Arr(sonarrs_config[x]["url"],
                                 sonarrs_config[x]["apikey"],
                                 "series").data
        paths["sonarr"][x] = Arr(sonarrs_config[x]["url"],
                                 sonarrs_config[x]["apikey"],
                                 "series").paths

if bool(radarrs_config.keys()):
    for x in giefbar(radarrs_config.keys(), f'{timeoutput()} - Loading data from Radarr instances'):
        media["radarr"][x] = Arr(radarrs_config[x]["url"],
                                 radarrs_config[x]["apikey"],
                                 "movie").data
        paths["radarr"][x] = Arr(radarrs_config[x]["url"],
                                 radarrs_config[x]["apikey"],
                                 "movie").paths

sonarr, radarr, plexlibrary, embylibrary = dict(), dict(), dict(), dict()

parse_arr_data(media, sonarr, radarr)
arrpaths = get_arrpaths(paths)

# Check for duplicate entries in Arr instances.
check_faulty(radarrs_config, sonarrs_config, radarr, sonarr)

if plex_enabled:
    # Load data from Plex.
    server = PlexServer(config["plex_url"], config["plex_token"])
    server_sections = server.library.sections()

    plex_library_paths, arr_plex_match = dict(), dict()

    for section in server_sections:
        plex_library_paths[section.key] = dict()
        x = 0
        for location in section.locations:
            plex_library_paths[section.key][x] = location

    arr_plex_match = dict()
    arr_find_plex_id(arrpaths, arr_plex_match, plex_library_paths, plex_sections, config)

    load_plex_data(server, plex_sections, plexlibrary)

    # Check for duplicate entries in Plex.
    duplicate = check_duplicate(server, plex_sections, config, delay)

    # Reload Plex data if duplicate items were found in Plex.
    if duplicate > 0:
        print(f"{timeoutput()} - Reloading data due to {duplicate} duplicate item(s) in Plex")

        plexlibrary = dict()
        server.reload()

        load_plex_data(server, plex_sections, plexlibrary)

    # Check for mismatched entries and correct them.
    plex_fixed_matches = 0
    plex_fixed_matches += plex_compare_media(arr_plex_match, sonarr, radarr, plexlibrary, config, delay)
    print(f"{timeoutput()} - Number of fixed matches in Plex: {plex_fixed_matches}")

if emby_enabled:
    # Load data from Emby.
    emby_library_paths = EmbyDB.libraries(config)
    emby_sections = EmbyDB.sections(config)
    load_emby_data(config, emby_sections, embylibrary)

    arr_emby_match = dict()
    arr_find_emby_id(arrpaths, arr_emby_match, emby_library_paths, config)

    # Check for mismatched entries and correct them.
    emby_fixed_matches = 0
    emby_fixed_matches += emby_compare_media(arr_emby_match, sonarr, radarr, embylibrary, config)
    print(f"{timeoutput()} - Number of fixed matches in Emby: {emby_fixed_matches}")

print(f"{timeoutput()} - Running the program took {runtime.stop()} seconds.")

exit(0)

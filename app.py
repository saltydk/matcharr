"""
Matcharr compares data from Sonarr/Radarr instances to
libraries in Plex/Emby and fixes any mismatches created by the agents used.
"""

import json
import time
import sys
import pkg_resources

from plexapi.server import PlexServer
from classes.arr import Arr
from classes.embydb import EmbyDB
from utils.emby import load_emby_data, arr_find_emby_id, emby_compare_media
from utils.plex import load_plex_data, check_duplicate, arr_find_plex_id, plex_compare_media
from utils.arr import parse_arr_data, get_arrpaths, check_faulty
from utils.base import timeoutput, giefbar
from utils.logging import get_logger

# TODO add logging
#  add validation for Arr/Plex/Emby config entries
#  add check for empty libraries in Plex/Emby
#  add support for anime (tentative)
#  add support for multiple Plex/Emby instances (tentative)
#  add support for forcing an agent for library types
#  add dry-run option
#  add support for specifying path mapping for media server

runtime = time.time()

# Logging
logger = get_logger(__name__)
logger.info("Running Matcharr.")
logger.debug("Using PlexAPI version %s", pkg_resources.get_distribution("plexapi").version)
logger.debug("Using requests version %s", pkg_resources.get_distribution("requests").version)
logger.debug("Using pandas version %s", pkg_resources.get_distribution("pandas").version)
logger.debug("Using tqdm version %s", pkg_resources.get_distribution("tqdm").version)

# Load configuration
config = json.load(open("config.json"))
sonarr_config = config["sonarr"].keys()
logger.debug("Sonarr config: %s", sonarr_config)
radarr_config = config["radarr"].keys()
logger.debug("Radarr config: %s", radarr_config)
delay = config["delay"]
logger.debug("Plex delay: %s", delay)
emby_enabled = config["emby_enabled"]
logger.debug("Emby enabled: %s", emby_enabled)
plex_enabled = config["plex_enabled"]
logger.debug("Plex enabled: %s", plex_enabled)
plex_sections, emby_sections, sonarrs_config, radarrs_config = dict(), dict(), dict(), dict()

for sonarr in sonarr_config:
    sonarrs_config[sonarr] = config["sonarr"][sonarr]

for radarr in radarr_config:
    radarrs_config[radarr] = config["radarr"][radarr]

if not bool(radarrs_config.keys()) and not bool(sonarrs_config.keys()):
    print(f'{timeoutput()} - No Arrs configured - Exiting.')
    sys.exit(0)

# Load data from Arr instances.
media = {"sonarr": {}, "radarr": {}}
paths = {"sonarr": {}, "radarr": {}}

if bool(sonarrs_config.keys()):
    for sonarr in giefbar(sonarrs_config.keys(),
                          f'{timeoutput()} - Loading data from Sonarr instances'):
        media["sonarr"][sonarr] = Arr(sonarrs_config[sonarr]["url"],
                                      sonarrs_config[sonarr]["apikey"],
                                      "series").data
        paths["sonarr"][sonarr] = Arr(sonarrs_config[sonarr]["url"],
                                      sonarrs_config[sonarr]["apikey"],
                                      "series").paths

if bool(radarrs_config.keys()):
    for radarr in giefbar(radarrs_config.keys(),
                          f'{timeoutput()} - Loading data from Radarr instances'):
        media["radarr"][radarr] = Arr(radarrs_config[radarr]["url"],
                                      radarrs_config[radarr]["apikey"],
                                      "movie").data
        paths["radarr"][radarr] = Arr(radarrs_config[radarr]["url"],
                                      radarrs_config[radarr]["apikey"],
                                      "movie").paths

sonarr_items, radarr_items, plexlibrary, embylibrary = dict(), dict(), dict(), dict()

parse_arr_data(media, sonarr_items, radarr_items)
arrpaths = get_arrpaths(paths)

# Check for duplicate entries in Arr instances.
check_faulty(radarrs_config, sonarrs_config, radarr_items, sonarr_items)

if plex_enabled:
    # Load data from Plex.
    server = PlexServer(config["plex_url"], config["plex_token"])
    server_sections = server.library.sections()

    plex_library_paths, arr_plex_match = dict(), dict()

    for section in server_sections:
        plex_library_paths[section.key] = dict()
        SECTION_COUNT = 0
        for location in section.locations:
            plex_library_paths[section.key][SECTION_COUNT] = location
            SECTION_COUNT += 1

    arr_plex_match = dict()
    arr_find_plex_id(arrpaths, arr_plex_match, plex_library_paths, plex_sections, config)

    # Check for duplicate entries in Plex.
    DUPLICATE = check_duplicate(server, plex_sections, config, delay)

    # Reload Plex data if duplicate items were found in Plex.
    if DUPLICATE > 0:
        print(f"{timeoutput()} - Reloading data due to {DUPLICATE} duplicate item(s) in Plex")

        plexlibrary = dict()
        server.reload()

    load_plex_data(server, plex_sections, plexlibrary)

    # Check for mismatched entries and correct them.
    PLEX_FIXED_MATCHES = 0
    PLEX_FIXED_MATCHES += plex_compare_media(arr_plex_match,
                                             sonarr_items,
                                             radarr_items,
                                             plexlibrary,
                                             config,
                                             delay)
    print(f"{timeoutput()} - Number of fixed matches in Plex: {PLEX_FIXED_MATCHES}")

if emby_enabled:
    # Load data from Emby.
    emby_library_paths = EmbyDB.libraries(config)
    emby_sections = EmbyDB.sections(config)
    load_emby_data(config, emby_sections, embylibrary)

    arr_emby_match = dict()
    arr_find_emby_id(arrpaths, arr_emby_match, emby_library_paths, config)

    # Check for mismatched entries and correct them.
    EMBY_FIXED_MATCHES = 0
    EMBY_FIXED_MATCHES += emby_compare_media(arr_emby_match,
                                             sonarr_items,
                                             radarr_items,
                                             embylibrary,
                                             config)
    print(f"{timeoutput()} - Number of fixed matches in Emby: {EMBY_FIXED_MATCHES}")

print(f"{timeoutput()} - Running the program took {round(time.time() - runtime, 2)} seconds.")

sys.exit(0)

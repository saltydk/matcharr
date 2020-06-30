import pandas as pd
import requests
from classes.arrmedia import ArrMedia
from classes.plex import Plex
from classes.plexdb import PlexDB


def load_data(media, sonarr, radarr, plexlibrary, config, sonarrs_config, radarrs_config):
    for Arrs, mediaDB in media.items():
        for showDB, shows in mediaDB.items():
            if Arrs == "sonarr":
                sonarr[showDB] = [ArrMedia(seriesShow["title"],
                                           seriesShow["path"],
                                           seriesShow["tvdbId"],
                                           seriesShow["titleSlug"]) for seriesShow in shows]
                plexlibrary[showDB] = [Plex(row[0],
                                            row[1],
                                            row[2],
                                            row[3],
                                            row[4]) for row in PlexDB().shows(config["plex_db"],
                                                                              sonarrs_config[showDB]["library_id"])]
            if Arrs == "radarr":
                radarr[showDB] = [ArrMedia(movies["title"],
                                           movies["path"],
                                           movies["tmdbId"],
                                           movies["titleSlug"]) for movies in shows]
                plexlibrary[showDB] = [Plex(row[0],
                                            row[1],
                                            row[2],
                                            row[3],
                                            row[4]) for row in PlexDB().movie(config["plex_db"],
                                                                              radarrs_config[showDB]["library_id"])]


def check_faulty(config, arr):
    for database in [*config]:
        print(f"Checking {database}")
        database_panda = pd.DataFrame.from_records([item.to_dict() for item in arr[database]])
        database_paths = database_panda["path"]
        database_duplicate = database_panda[database_paths.isin(database_paths[database_paths.duplicated()])]
        for path in database_duplicate.values.tolist():
            print(f"Duplicate path in item: {path}")


def check_duplicate(library, config):
    duplicate = 0

    for arrDB in [*library]:
        plex_panda = pd.DataFrame.from_records([plex.to_dict() for plex in library[arrDB]])
        plex_ids = plex_panda["id"]
        plex_duplicates = plex_panda[plex_ids.isin(plex_ids[plex_ids.duplicated()])]

        if len(plex_duplicates.index) > 0:
            duplicate += 1

        for metadataid in plex_duplicates.values.tolist():
            print(f"Splitting item with ID:{metadataid[2]}")
            url_params = {
                'X-Plex-Token': config["plex_token"]
            }
            url_str = '%s/library/metadata/%d/split' % (config["plex_url"], int(metadataid[2]))
            requests.options(url_str, params=url_params, timeout=30)
            requests.put(url_str, params=url_params, timeout=30)

    return duplicate


def compare_media(arrconfig, arr, library, agent, config):
    for database in [*arrconfig]:
        for items in arr[database]:
            for plex_items in library[database]:
                if items.path == plex_items.fullpath:
                    if items.id == plex_items.id:
                        break
                    else:
                        print(f"{database} title: {items.title} did not match Plex title: {plex_items.title}")
                        print(f"{database} id: {items.id} -- Plex id: {plex_items.id}")
                        plex_match(config["plex_url"],
                                   config["plex_token"],
                                   agent,
                                   plex_items.metadataid,
                                   items.id,
                                   items.title)
                        plex_refresh(config["plex_url"],
                                     config["plex_token"],
                                     plex_items.metadataid)


def plex_match(url, token, agent, metadataid, agentid, title):
    url_params = {
        'X-Plex-Token': token,
        'guid': 'com.plexapp.agents.{}://{}?lang=en'.format(agent, agentid),
        'name': title,
    }
    url_str = '%s/library/metadata/%d/match' % (url, int(metadataid))
    requests.options(url_str, params=url_params, timeout=30)
    requests.put(url_str, params=url_params, timeout=30)


def plex_refresh(url, token, metadataid):
    url_params = {
        'X-Plex-Token': token
    }
    url_str = '%s/library/metadata/%d/refresh' % (url, int(metadataid))
    requests.options(url_str, params=url_params, timeout=30)
    requests.put(url_str, params=url_params, timeout=30)

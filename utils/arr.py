import pandas as pd

from classes.arrmedia import ArrMedia
from utils.base import timeoutput, giefbar


def parse_arr_data(media, sonarr, radarr):
    for Arrs, mediaDB in media.items():
        for showDB, shows in mediaDB.items():
            if Arrs == "sonarr":
                sonarr[showDB] = [ArrMedia(seriesShow["title"],
                                           seriesShow["path"],
                                           seriesShow["tvdbId"],
                                           seriesShow.get("imdbId", "none"),
                                           seriesShow["titleSlug"]) for seriesShow in shows]

            if Arrs == "radarr":
                radarr[showDB] = [ArrMedia(movies["title"],
                                           movies["path"],
                                           movies["tmdbId"],
                                           movies.get("imdbId", "none"),
                                           movies["titleSlug"]) for movies in shows]


def get_arrpaths(paths):
    arrpaths = {}
    for arrtype in paths.keys():
        arrpaths[arrtype] = dict()
        for arr, data in paths[arrtype].items():
            x = 0
            arrpaths[arrtype][arr] = dict()
            for path in data:
                arrpaths[arrtype][arr][x] = path.get('path')
                x += 1
    return arrpaths


def check_faulty(radarrs_config, sonarrs_config, radarr, sonarr):
    if bool(radarrs_config.keys()):
        for radarr_db in giefbar(radarrs_config.keys(), f'{timeoutput()} - Checking for faulty data in Radarr'):

            database_panda = pd.DataFrame.from_records([item.to_dict() for item in radarr[radarr_db]])
            database_paths = database_panda["path"]
            database_duplicate = database_panda[database_paths.isin(database_paths[database_paths.duplicated()])]

            for path in database_duplicate.values.tolist():
                print(f"{timeoutput()} - Checking for faulty data in Radarr - Duplicate path in item: {path}")

    if bool(sonarrs_config.keys()):
        for sonarr_db in giefbar(sonarrs_config.keys(), f'{timeoutput()} - Checking for faulty data in Sonarr'):

            database_panda = pd.DataFrame.from_records([item.to_dict() for item in sonarr[sonarr_db]])
            database_paths = database_panda["path"]
            database_duplicate = database_panda[database_paths.isin(database_paths[database_paths.duplicated()])]

            for path in database_duplicate.values.tolist():
                print(f"{timeoutput()} - Checking for faulty data in Sonarr - Duplicate path in item: {path}")

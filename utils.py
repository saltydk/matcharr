import pandas as pd
import requests
import requests.exceptions
import time
import os
from plexapi.library import MovieSection
from plexapi.library import ShowSection
from tqdm import tqdm
from datetime import datetime
from classes.arrmedia import ArrMedia
from classes.plex import Plex
from classes.emby import Emby
from classes.embydb import EmbyDB


def timeoutput():
    now = datetime.now()
    return now.strftime('%d %b %Y %H:%M:%S')


def giefbar(iterator, desc):
    return tqdm(iterator, desc=desc + ":",
                bar_format="{desc:80} {percentage:3.0f}%|{bar}| {n_fmt:^5}/{total_fmt:^5} [{elapsed_s:5.0f} s]")


# Audaciously stolen from https://github.com/l3uddz/plex_autoscan/
def map_path(config, path):
    for mapped_path, mappings in config['path_mappings'].items():
        for mapping in mappings:
            if path.startswith(mapping):
                return path.replace(mapping, mapped_path)
    return path


def parse_arr_data(media, sonarr, radarr):
    for Arrs, mediaDB in media.items():
        for showDB, shows in mediaDB.items():
            if Arrs == "sonarr":
                sonarr[showDB] = [ArrMedia(seriesShow["title"],
                                           seriesShow["path"],
                                           seriesShow["tvdbId"],
                                           seriesShow["titleSlug"]) for seriesShow in shows]

            if Arrs == "radarr":
                radarr[showDB] = [ArrMedia(movies["title"],
                                           movies["path"],
                                           movies["tmdbId"],
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


def arr_find_plex_id(arrpaths, arr_plex_match, plex_library_paths, plex_sections):
    for arrtype in arrpaths.keys():
        arr_plex_match[arrtype] = dict()
        if arrtype == "sonarr":
            string = "shows"
        if arrtype == "radarr":
            string = "movie"
        for arr in arrpaths[arrtype].keys():
            arr_plex_match[arrtype][arr] = dict()
            for arr_path in arrpaths[arrtype][arr].values():
                for library in plex_library_paths.keys():
                    for plex_path in plex_library_paths[library].values():
                        if arr_path == os.path.join(plex_path, ''):
                            arr_plex_match[arrtype][arr][arr_path] = {"plex_library_id": library}
                            plex_sections[library] = string
    return arr_plex_match


def load_plex_data(server, plex_sections, plexlibrary, config):
    for sectionid, mediatype in giefbar(plex_sections.items(), f'{timeoutput()} - Loading data from Plex'):
        section = server.library.sectionByID(str(sectionid))
        media = section.all()

        if mediatype == "shows":
            plexlibrary[sectionid] = [Plex(map_path(config, str(row.locations[0])),
                                           row.guid,
                                           row.ratingKey,
                                           row.title) for row in
                                      media]

        if mediatype == "movie":
            plexlibrary[sectionid] = [Plex(map_path(config, str(row.locations[0])),
                                           row.guid,
                                           row.ratingKey,
                                           row.title) for row in
                                      media]


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


def check_duplicate(server, plex_sections, config, delay):
    duplicate = 0

    for sectionid, mediatype in giefbar(plex_sections.items(), f'{timeoutput()} - Checking for duplicate in Plex'):
        section = server.library.sectionByID(str(sectionid))
        if isinstance(section, MovieSection):
            for x in section.search(libtype="movie", duplicate=True):
                duplicate += 1
                plex_split(x.ratingKey, config, delay)
                time.sleep(delay)

        if isinstance(section, ShowSection):
            for x in section.search(libtype="show", duplicate=True):
                if len(x.locations) > 1:
                    duplicate += 1
                    plex_split(x.ratingKey, config, delay)
                    time.sleep(delay)

    return duplicate


def plex_compare_media(arr_plex_match, sonarr, radarr, library, config, delay):
    counter = 0
    for arrtype in arr_plex_match.keys():
        if arrtype == "sonarr":
            agent = "thetvdb"
            arr = sonarr
        if arrtype == "radarr":
            agent = "themoviedb"
            arr = radarr
        for arrinstance in arr_plex_match[arrtype].keys():
            if len(arrinstance) == 0:
                continue
            for folder in arr_plex_match[arrtype][arrinstance].values():
                for items in giefbar(arr[arrinstance], f'{timeoutput()} - Checking Plex against {arrinstance}'):
                    for plex_items in library[folder.get("plex_library_id")]:
                        if items.path == plex_items.fullpath:
                            if items.id == plex_items.id:
                                break
                            else:
                                tqdm.write(
                                    f"{timeoutput()} - {arrinstance} title: {items.title} did not match Plex title: {plex_items.title}")
                                tqdm.write(
                                    f"{timeoutput()} - {arrinstance} {agent} id: {items.id} -- Plex {agent} id: {plex_items.id}")
                                tqdm.write(f"{timeoutput()} - Plex metadata ID: {plex_items.metadataid}")

                                try:
                                    plex_match(config["plex_url"],
                                               config["plex_token"],
                                               agent,
                                               plex_items.metadataid,
                                               items.id,
                                               items.title,
                                               delay)

                                    plex_refresh(config["plex_url"],
                                                 config["plex_token"],
                                                 plex_items.metadataid,
                                                 delay)

                                    time.sleep(delay)
                                except TypeError:
                                    tqdm.write(f"{timeoutput()} - Plex metadata ID appears to be missing.")
                                counter += 1
    return counter


def plex_match(url, token, agent, metadataid, agentid, title, delay):
    retries = 5
    while retries > 0:
        try:
            url_params = {
                'X-Plex-Token': token,
                'guid': 'com.plexapp.agents.{}://{}?lang=en'.format(agent, agentid),
                'name': title,
            }
            url_str = '%s/library/metadata/%d/match' % (url, int(metadataid))
            requests.options(url_str, params=url_params, timeout=30)
            resp = requests.put(url_str, params=url_params, timeout=30)

            if resp.status_code == 200:
                tqdm.write(f"{timeoutput()} - Successfully matched {int(metadataid)} to {title} ({agentid})")
            else:
                tqdm.write(
                    f"{timeoutput()} - Failed to match {int(metadataid)} to {title} ({agentid}) - Plex returned error: {resp.text}")
            break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectTimeout):
            tqdm.write(
                f"{timeoutput()} - Exception matching {int(metadataid)} to {title} ({agentid}) - {retries} left.")
            retries -= 1
            time.sleep(delay)
    if retries == 0:
        raise Exception(
            f"{timeoutput()} - Exception matching {int(metadataid)} to {title} ({agentid}) - Ran out of retries.")


def plex_refresh(url, token, metadataid, delay):
    retries = 5
    while retries > 0:
        try:
            url_params = {
                'X-Plex-Token': token
            }
            url_str = '%s/library/metadata/%d/refresh' % (url, int(metadataid))
            requests.options(url_str, params=url_params, timeout=30)
            resp = requests.put(url_str, params=url_params, timeout=30)

            if resp.status_code == 200:
                tqdm.write(f"{timeoutput()} - Successfully refreshed {int(metadataid)}")
            else:
                tqdm.write(f"{timeoutput()} - Failed refreshing {int(metadataid)} - Plex returned error: {resp.text}")
            break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectTimeout):
            tqdm.write(f"{timeoutput()} - Exception refreshing {int(metadataid)} - {retries} left.")
            retries -= 1
            time.sleep(delay)
    if retries == 0:
        raise Exception(f"{timeoutput()} - Exception refreshing {int(metadataid)} - Ran out of retries.")


def plex_split(metadataid, config, delay):
    retries = 5
    while retries > 0:
        try:
            tqdm.write(f"{timeoutput()} - Checking for duplicate in Plex: Splitting item with ID:{metadataid}")
            url_params = {
                'X-Plex-Token': config["plex_token"]
            }
            url_str = '%s/library/metadata/%d/split' % (config["plex_url"], metadataid)
            requests.options(url_str, params=url_params, timeout=30)
            resp = requests.put(url_str, params=url_params, timeout=30)

            if resp.status_code == 200:
                tqdm.write(f"{timeoutput()} - Checking for duplicate in Plex: Successfully split {metadataid}.")
            else:
                tqdm.write(
                    f"{timeoutput()} - Checking for duplicate in Plex: Failed to split {metadataid} - Plex returned error: {resp.text}")
            break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectTimeout):
            tqdm.write(
                f"{timeoutput()} - Checking for duplicate in Plex: Exception splitting {metadataid} - {retries} left.")
            retries -= 1
            time.sleep(delay)
    if retries == 0:
        raise Exception(
            f"{timeoutput()} - Checking for duplicate in Plex: Exception splitting {metadataid} - Ran out of retries.")


def load_emby_data(config, emby_sections, embylibrary):
    for section in giefbar(emby_sections, f'{timeoutput()} - Loading data from Emby'):
        embylibrary[section] = [Emby(row['Path'],
                                     row['ProviderIds'],
                                     row['Id'],
                                     row['Name']) for row in
                                EmbyDB().data(config, section)]


def emby_compare_media(arrconfig, arr, library, agent, config):
    for arrinstance in arrconfig.keys():
        if arrconfig[arrinstance]["emby_library_id"] == "None":
            continue
        for items in giefbar(arr[arrinstance], f'{timeoutput()} - Checking {arrinstance}'):
            for emby_items in library[arrconfig[arrinstance].get("emby_library_id")]:
                if items.path == emby_items.path:
                    if emby_items.id.get(agent):
                        if str(items.id) == emby_items.id.get(agent):
                            break
                        else:
                            tqdm.write(
                                f"{timeoutput()} - {arrinstance} title: {items.title} did not match Emby title: {emby_items.title}")
                            tqdm.write(
                                f"{timeoutput()} - {arrinstance} {agent} id: {items.id} -- Emby {agent} id: {emby_items.id.get(agent)}")
                            tqdm.write(f"{timeoutput()} - Emby metadata ID: {emby_items.metadataid}")

                            try:
                                emby_match(config["emby_url"],
                                           config["emby_token"],
                                           emby_items.metadataid,
                                           items.title,
                                           agent,
                                           items.id)

                                emby_refresh(config["emby_url"],
                                             config["emby_token"],
                                             emby_items.metadataid)

                            except TypeError:
                                tqdm.write(f"{timeoutput()} - Emby metadata ID appears to be missing.")
                    else:
                        tqdm.write(f"{timeoutput()} - {arrinstance} title: {items.title} has no match in Emby")
                        tqdm.write(f"{timeoutput()} - Emby metadata ID: {emby_items.metadataid}")

                        try:
                            emby_match(config["emby_url"],
                                       config["emby_token"],
                                       emby_items.metadataid,
                                       items.title,
                                       agent,
                                       items.id)

                            emby_refresh(config["emby_url"],
                                         config["emby_token"],
                                         emby_items.metadataid)

                        except TypeError:
                            tqdm.write(f"{timeoutput()} - Emby metadata ID appears to be missing.")


def emby_match(url, token, metadataid, title, agent, agentid):
    retries = 5
    while retries > 0:
        try:
            params = (
                ('api_key', token),
            )
            url_str = '%s/emby/emby/Items/%d' % (url, int(metadataid))
            headers = {
                'accept': '*/*',
                'Content-Type': 'application/json',
            }
            if agent == "Tmdb":
                data = f'{{"Id": metadataid,"Name": title,"Genres": [],"Tags": [],"TagItems": [],"LockData": false,"LockedFields": [],"ProviderIds": {{"{agent}":"{agentid}","Imdb": "","Tvdb": "","Zap2It": ""}}}}'
            if agent == "Tvdb":
                data = f'{{"Id": metadataid,"Name": title,"Genres": [],"Tags": [],"TagItems": [],"LockData": false,"LockedFields": [],"ProviderIds": {{"{agent}":"{agentid}","Imdb": "","Tmdb": "","Zap2It": ""}}}}'

            resp = requests.post(url_str, headers=headers, params=params, data=data, timeout=300)

            if resp.status_code == 200 or resp.status_code == 204:
                tqdm.write(f"{timeoutput()} - Successfully matched {int(metadataid)} to {title} ({agentid})")
            else:
                tqdm.write(
                    f"{timeoutput()} - Failed to match {int(metadataid)} to {title} ({agentid}) - Emby returned error: {resp.text}")
            break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectTimeout):
            tqdm.write(
                f"{timeoutput()} - Exception matching {int(metadataid)} to {title} ({agentid}) - {retries} left.")
            retries -= 1
    if retries == 0:
        raise Exception(
            f"{timeoutput()} - Exception matching {int(metadataid)} to {title} ({agentid}) - Ran out of retries.")


def emby_refresh(url, token, metadataid):
    retries = 5
    while retries > 0:
        try:
            params = (
                ('Recursive', 'true'),
                ('MetadataRefreshMode', 'FullRefresh'),
                ('ImageRefreshMode', 'FullRefresh'),
                ('ReplaceAllMetadata', 'true'),
                ('ReplaceAllImages', 'true'),
                ('api_key', token),
            )
            url_str = '%s/emby/Items/%d/Refresh' % (url, int(metadataid))
            headers = {
                'accept': '*/*',
                'Content-Type': 'application/json',
            }
            resp = requests.post(url_str, headers=headers, params=params, timeout=300)

            if resp.status_code == 200 or resp.status_code == 204:
                tqdm.write(f"{timeoutput()} - Successfully refreshed {int(metadataid)}")
            else:
                tqdm.write(
                    f"{timeoutput()} - Failed to refresh {int(metadataid)} - Emby returned error: {resp.text}")
            break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectTimeout):
            tqdm.write(
                f"{timeoutput()} - Exception refreshing {int(metadataid)} - {retries} left.")
            retries -= 1
    if retries == 0:
        raise Exception(
            f"{timeoutput()} - Exception refreshing {int(metadataid)} - Ran out of retries.")

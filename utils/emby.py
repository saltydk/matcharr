"""
Functions that handle Emby functionality.
"""
import posixpath
import requests
import requests.exceptions

from classes.emby import Emby
from classes.embydb import EmbyDB
from utils.base import timeoutput, giefbar, map_path, tqdm


def load_emby_data(config, emby_sections, embylibrary):
    """Loads data from Emby."""
    for section in giefbar(emby_sections, f'{timeoutput()} - Loading data from Emby'):
        embylibrary[section] = list()
        for row in giefbar(EmbyDB().data(config, section),
                           f'{timeoutput()} - '
                           f'Loading Emby section {emby_sections[section]} (ID {section})'):
            embylibrary[section].append(Emby(row['Path'],
                                             map_path(config, row['Path']),
                                             row['ProviderIds'],
                                             row['Id'],
                                             row['Name']))


def arr_find_emby_id(arrpaths, arr_emby_match, emby_library_paths, config):
    """Maps Emby libraries to Arr root paths."""
    for arrtype in arrpaths.keys():
        arr_emby_match[arrtype] = dict()
        for arr in arrpaths[arrtype].keys():
            arr_emby_match[arrtype][arr] = dict()
            for arr_path in arrpaths[arrtype][arr].values():
                for library in emby_library_paths.values():
                    if arr_path == map_path(config, posixpath.join(library.get('Path'), '')):
                        arr_emby_match[arrtype][arr][arr_path] = {"emby_library_id": library.get('Id')}


def emby_compare_media(arr_emby_match, sonarr, radarr, library, config):
    """Compares Arr data with Emby data."""
    counter = 0
    for arrtype in arr_emby_match.keys():
        if arrtype == "sonarr":
            agent = "Tvdb"
            arr = sonarr
        elif arrtype == "radarr":
            agent = "Tmdb"
            arr = radarr
        for arrinstance in arr_emby_match[arrtype].keys():
            if len(arrinstance) == 0:
                continue
            for folder in arr_emby_match[arrtype][arrinstance].values():
                for items in giefbar(arr[arrinstance],
                                     f'{timeoutput()} - Checking Emby against {arrinstance}'):
                    for emby_items in library[folder.get("emby_library_id")]:
                        if items.mappedpath == emby_items.mappedpath:
                            if emby_items.id.get(agent):
                                if str(items.id) == emby_items.id.get(agent):
                                    break
                                else:
                                    tqdm.write(
                                        f"{timeoutput()} - "
                                        f"{arrinstance} title: {items.title} "
                                        f"did not match Emby title: {emby_items.title}")
                                    tqdm.write(
                                        f"{timeoutput()} - "
                                        f"{arrinstance} {agent} id: {items.id} -- "
                                        f"Emby {agent} id: {emby_items.id.get(agent)}")
                                    tqdm.write(
                                        f"{timeoutput()} - "
                                        f"Emby metadata ID: {emby_items.metadataid}")

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
                                        tqdm.write(
                                            f"{timeoutput()} - "
                                            f"Emby metadata ID appears to be missing.")
                                    counter += 1
                            else:
                                tqdm.write(f"{timeoutput()} - "
                                           f"{arrinstance} title: {items.title} "
                                           f"has no match in Emby")
                                tqdm.write(f"{timeoutput()} - "
                                           f"Emby metadata ID: {emby_items.metadataid}")

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
                                    tqdm.write(f"{timeoutput()} - "
                                               f"Emby metadata ID appears to be missing.")
                                counter += 1
                            break
    return counter


def emby_match(url, token, metadataid, title, agent, agentid):
    """Handles matching through editing metadata items."""
    retries = 5
    while retries > 0:
        try:
            params = (
                ('api_key', token),
            )
            url_str = '%s/emby/Items/%d' % (url, int(metadataid))
            headers = {
                'accept': '*/*',
                'Content-Type': 'application/json',
            }
            if agent == "Tmdb":
                data = f'{{"Id": metadataid,"Name": title,"Genres": [],"Tags": [],"TagItems": [],"LockData": false,"LockedFields": [],"ProviderIds": {{"{agent}":"{agentid}","Imdb": "","Tvdb": "","Zap2It": ""}}}}'
            if agent == "Tvdb":
                data = f'{{"Id": metadataid,"Name": title,"Genres": [],"Tags": [],"TagItems": [],"LockData": false,"LockedFields": [],"ProviderIds": {{"{agent}":"{agentid}","Imdb": "","Tmdb": "","Zap2It": ""}}}}'

            resp = requests.post(url_str, headers=headers, params=params, data=data, timeout=30)

            if resp.status_code == 200 or resp.status_code == 204:
                tqdm.write(f"{timeoutput()} - "
                           f"Successfully matched {int(metadataid)} to {title} ({agentid})")
            else:
                tqdm.write(
                    f"{timeoutput()} - "
                    f"Failed to match {int(metadataid)} to {title} ({agentid}) - Emby returned error: {resp.text}")
            break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectTimeout):
            tqdm.write(
                f"{timeoutput()} - "
                f"Exception matching {int(metadataid)} to {title} ({agentid}) - {retries} left.")
            retries -= 1
    if retries == 0:
        raise Exception(
            f"{timeoutput()} - "
            f"Exception matching {int(metadataid)} to {title} ({agentid}) - Ran out of retries.")


def emby_refresh(url, token, metadataid):
    """Handles refreshing metadata items."""
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
            resp = requests.post(url_str, headers=headers, params=params, timeout=30)

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

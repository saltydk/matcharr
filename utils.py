import pandas as pd
import requests
import requests.exceptions
import time
from time import gmtime, strftime
from classes.arrmedia import ArrMedia
from classes.plex import Plex
from classes.plexdb import PlexDB


def timeoutput():
    return strftime('%d %b %Y %H:%M:%S', gmtime())


def load_arr_data(media, sonarr, radarr):
    for Arrs, mediaDB in media.items():
        for showDB, shows in mediaDB.items():
            print(f"{timeoutput()} - Loading data from {showDB}")

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


def load_plex_data(plexlibrary, config, plex_sections, delay):
    for section, mediatype in plex_sections.items():
        print(f"{timeoutput()} - Loading Plex Library Section: {section}")

        if mediatype == "shows":
            plexlibrary[section] = [Plex(row[0],
                                         row[1],
                                         row[2],
                                         row[3],
                                         row[4]) for row in
                                    PlexDB().shows(config["plex_db"], section)]

        if mediatype == "movie":
            plexlibrary[section] = [Plex(row[0],
                                         row[1],
                                         row[2],
                                         row[3],
                                         row[4]) for row in
                                    PlexDB().movie(config["plex_db"], section)]

        time.sleep(delay)


def check_faulty(config, arr):
    for database in [*config]:
        print(f"{timeoutput()} - Checking {database}")

        database_panda = pd.DataFrame.from_records([item.to_dict() for item in arr[database]])
        database_paths = database_panda["path"]
        database_duplicate = database_panda[database_paths.isin(database_paths[database_paths.duplicated()])]

        for path in database_duplicate.values.tolist():
            print(f"{timeoutput()} - Duplicate path in item: {path}")


def check_duplicate(library, config, delay):
    duplicate = 0

    for arrDB in [*library]:
        plex_panda = pd.DataFrame.from_records([plex.to_dict() for plex in library[arrDB]])
        plex_dfobject = pd.DataFrame(plex_panda, columns=['title', 'id', 'metadataid'])
        plex_duplicates = plex_dfobject[plex_dfobject.duplicated(['id'])]

        if len(plex_duplicates.index) > 0:
            duplicate = 1

        for metadataid in plex_duplicates.values.tolist():
            plex_split(metadataid, config, delay)

            time.sleep(delay)

    return duplicate


def compare_media(arrconfig, arr, library, agent, config, delay):
    for arrinstance in [*arrconfig]:
        for items in arr[arrinstance]:
            for plex_items in library[arrconfig[arrinstance].get("library_id")]:
                if items.path == plex_items.fullpath:
                    if items.id == plex_items.id:
                        break
                    else:
                        print(f"{timeoutput()} - {arrinstance} title: {items.title} did not match Plex title: {plex_items.title}")
                        print(f"{timeoutput()} - {arrinstance} {agent} id: {items.id} -- Plex {agent} id: {plex_items.id}")
                        print(f"{timeoutput()} - Plex metadata ID: {plex_items.metadataid}")

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
                            print(f"{timeoutput()} - Plex metadata ID appears to be missing.")


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
                print(f"{timeoutput()} - Successfully matched {int(metadataid)} to {title} ({agentid})")
            else:
                print(f"{timeoutput()} - Failed to match {int(metadataid)} to {title} ({agentid}) - Plex returned error: {resp.text}")
            break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectTimeout):
            print(f"{timeoutput()} - Exception matching {int(metadataid)} to {title} ({agentid}) - {retries} left.")
            retries -= 1
            time.sleep(delay)
    if retries == 0:
        raise Exception(f"{timeoutput()} - Exception matching {int(metadataid)} to {title} ({agentid}) - Ran out of retries.")


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
                print(f"{timeoutput()} - Successfully refreshed {int(metadataid)}")
            else:
                print(f"{timeoutput()} - Failed refreshing {int(metadataid)} - Plex returned error: {resp.text}")
            break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectTimeout):
            print(f"{timeoutput()} - Exception refreshing {int(metadataid)} - {retries} left.")
            retries -= 1
            time.sleep(delay)
    if retries == 0:
        raise Exception(f"{timeoutput()} - Exception refreshing {int(metadataid)} - Ran out of retries.")


def plex_split(metadataid, config, delay):
    retries = 5
    while retries > 0:
        try:
            print(f"Splitting item with ID:{metadataid[2]}")
            url_params = {
                'X-Plex-Token': config["plex_token"]
            }
            url_str = '%s/library/metadata/%d/split' % (config["plex_url"], int(metadataid[2]))
            requests.options(url_str, params=url_params, timeout=30)
            resp = requests.put(url_str, params=url_params, timeout=30)

            if resp.status_code == 200:
                print(f"{timeoutput()} - Successfully split {int(metadataid[2])}.")
            else:
                print(f"{timeoutput()} - Failed to split {int(metadataid[2])} - Plex returned error: {resp.text}")
            break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectTimeout):
            print(f"{timeoutput()} - Exception splitting {int(metadataid[2])} - {retries} left.")
            retries -= 1
            time.sleep(delay)
    if retries == 0:
        raise Exception(f"{timeoutput()} - Exception splitting {int(metadataid[2])} - Ran out of retries.")

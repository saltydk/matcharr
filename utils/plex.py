import posixpath
import time
import requests
import requests.exceptions


from plexapi.video import Show
from plexapi.video import Movie
from classes.plex import Plex
from utils.base import timeoutput, giefbar, map_path, tqdm


def load_plex_data(server, plex_sections, plexlibrary):
    for sectionid in giefbar(plex_sections.values(), f'{timeoutput()} - Loading data from Plex'):
        section = server.library.sectionByID(sectionid)
        Show._include = ""
        Movie._include = ""
        media = section.all()
        plexlibrary[sectionid] = list()
        for row in giefbar(media, f'{timeoutput()} - Loading Plex section {section.title} (ID {sectionid})'):
            plexlibrary[sectionid].append(Plex(row.locations[0], row.guid, row.ratingKey, row.title))


def check_duplicate(server, plex_sections, config, delay):
    duplicate = 0

    for sectionid, mediatype in giefbar(plex_sections.items(), f'{timeoutput()} - Checking for duplicates in Plex'):
        section = server.library.sectionByID(str(sectionid))
        Show._include = ""
        Movie._include = ""
        for item in section.all():
            if len(item.locations) > 1:
                duplicate += 1
                plex_split(item.ratingKey, config, delay)
                time.sleep(delay)

    return duplicate


def arr_find_plex_id(arrpaths, arr_plex_match, plex_library_paths, plex_sections, config):
    for arrtype in arrpaths.keys():
        arr_plex_match[arrtype] = dict()
        for arr in arrpaths[arrtype].keys():
            arr_plex_match[arrtype][arr] = dict()
            for arr_path in arrpaths[arrtype][arr].values():
                for library in plex_library_paths.keys():
                    for plex_path in plex_library_paths[library].values():
                        if arr_path == map_path(config, posixpath.join(plex_path, '')):
                            arr_plex_match[arrtype][arr][arr_path] = {"plex_library_id": library}
                            plex_sections[library] = library


def plex_compare_media(arr_plex_match, sonarr, radarr, library, config, delay):
    counter = 0
    for arrtype in arr_plex_match.keys():
        if arrtype == "sonarr":
            agent = "thetvdb"
            arr = sonarr
        elif arrtype == "radarr":
            agent = "themoviedb"
            arr = radarr
        for arrinstance in arr_plex_match[arrtype].keys():
            if len(arrinstance) == 0:
                continue
            for folder in arr_plex_match[arrtype][arrinstance].values():
                for items in giefbar(arr[arrinstance], f'{timeoutput()} - Checking Plex against {arrinstance}'):
                    for plex_items in library[folder.get("plex_library_id")]:
                        if items.path == map_path(config, plex_items.fullpath):
                            if plex_items.agent == "imdb":
                                if items.imdb == plex_items.id:
                                    break
                                else:
                                    tqdm.write(
                                        f"{timeoutput()} - Plex metadata item {plex_items.metadataid} with imdb ID:{plex_items.id} did not match {arrinstance} imdb ID:{items.imdb}")

                                    try:
                                        plex_match(config["plex_url"],
                                                   config["plex_token"],
                                                   agent,
                                                   plex_items.metadataid,
                                                   items.imdb,
                                                   items.title,
                                                   delay)

                                        time.sleep(delay)
                                    except TypeError:
                                        tqdm.write(f"{timeoutput()} - Plex metadata ID appears to be missing.")
                                    counter += 1

                            else:
                                if items.id == plex_items.id:
                                    break
                                else:
                                    tqdm.write(f"{timeoutput()} - Plex metadata item {plex_items.metadataid} with {agent} ID:{plex_items.id} did not match {arrinstance} {agent} ID:{items.id}")

                                    try:
                                        plex_match(config["plex_url"],
                                                   config["plex_token"],
                                                   agent,
                                                   plex_items.metadataid,
                                                   items.id,
                                                   items.title,
                                                   delay)

                                        time.sleep(delay)
                                    except TypeError:
                                        tqdm.write(f"{timeoutput()} - Plex metadata ID appears to be missing.")
                                    counter += 1
                                break
    return counter


# TODO add ability to use different language codes
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


def plex_split(metadataid, config, delay):
    retries = 5
    while retries > 0:
        try:
            tqdm.write(f"{timeoutput()} - Checking for duplicate in Plex: Splitting item with ID:{metadataid}")
            url_params = {
                'X-Plex-Token': config["plex_token"]
            }
            url_str = '%s/library/metadata/%d/split' % (config["plex_url"], metadataid)
            resp = requests.put(url_str, params=url_params, timeout=30)

            if resp.status_code == 200:
                tqdm.write(f"{timeoutput()} - Checking for duplicate in Plex: Successfully split {metadataid}.")
            else:
                tqdm.write(f"{timeoutput()} - Checking for duplicate in Plex: Failed to split {metadataid} - Plex returned error: {resp.text}")
            break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectTimeout):
            tqdm.write(
                f"{timeoutput()} - Checking for duplicate in Plex: Exception splitting {metadataid} - {retries} left.")
            retries -= 1
            time.sleep(delay)
    if retries == 0:
        raise Exception(
            f"{timeoutput()} - Checking for duplicate in Plex: Exception splitting {metadataid} - Ran out of retries.")

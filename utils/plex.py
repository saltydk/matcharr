import posixpath
import time
import requests
import requests.exceptions


from plexapi.video import Show
from plexapi.video import Movie
from classes.plex import Plex
from utils.base import timeoutput, giefbar, tqdm, map_path


def load_plex_data(server, plex_sections, plexlibrary, config):
    Show._include = ""
    Movie._include = ""
    for sectionid in plex_sections.values():
        section = server.library.sectionByID(sectionid)
        media = section.all()
        plexlibrary[sectionid] = [Plex(row.locations[0],
                                       map_path(config, row.locations[0]),
                                       row.guid,
                                       row.ratingKey,
                                       row.title,
                                       row.guids)
                                  for row in giefbar(media, f'{timeoutput()} - Loading Plex section {section.title} (ID {sectionid})')]


def check_duplicate(server, plex_sections, config, delay):
    duplicate = 0

    Show._include = ""
    Movie._include = ""
    for sectionid, mediatype in giefbar(plex_sections.items(), f'{timeoutput()} - Checking for duplicates in Plex'):
        section = server.library.sectionByID(int(sectionid))
        for item in section.all():
            if len(item.locations) > 1:
                dirname = posixpath.dirname(item.locations[0])
                for location in item.locations:
                    if posixpath.dirname(location) != dirname:
                        duplicate += 1
                        plex_split(item.ratingKey, config, delay)
                        time.sleep(delay)

    return duplicate


def arr_find_plex_id(arrpaths, arr_plex_match, plex_library_paths, plex_sections, config):
    for arrtype in arrpaths.keys():
        arr_plex_match[arrtype] = {}
        for arr in arrpaths[arrtype].keys():
            arr_plex_match[arrtype][arr] = {}
            for arr_path in arrpaths[arrtype][arr].values():
                for library in plex_library_paths.keys():
                    for plex_path in plex_library_paths[library].values():
                        if arr_path.rstrip("/") == map_path(config, posixpath.join(plex_path, '')).rstrip("/"):
                            arr_plex_match[arrtype][arr][arr_path] = {"plex_library_id": library}
                            plex_sections[library] = library


def plex_compare_media(arr_plex_match, sonarr, radarr, library, config, delay):
    counter = 0
    for arrtype in arr_plex_match.keys():
        if arrtype == "radarr":
            agent = "themoviedb"
            arr = radarr
        elif arrtype == "sonarr":
            agent = "thetvdb"
            arr = sonarr
        for arrinstance in arr_plex_match[arrtype].keys():
            if len(arrinstance) == 0:
                continue
            for folder in arr_plex_match[arrtype][arrinstance].values():
                for items in giefbar(arr[arrinstance], f'{timeoutput()} - Checking Plex against {arrinstance}'):
                    for plex_items in library[folder.get("plex_library_id")]:
                        if items.mappedpath in [posixpath.dirname(plex_items.mappedpath), plex_items.mappedpath]:
                            if plex_items.agent == "imdb":
                                if items.imdb == plex_items.id:
                                    break
                                tqdm.write(
                                    f"{timeoutput()} - Plex metadata item {plex_items.metadataid} with imdb ID:{plex_items.id} did not match {arrinstance} imdb ID:{items.imdb}")
                                tqdm.write(
                                    f"{timeoutput()} - Path: {items.mappedpath}")

                                try:
                                    plex_match(config["plex_url"],
                                               config["plex_token"],
                                               "imdb",
                                               plex_items.metadataid,
                                               items.imdb,
                                               items.title,
                                               delay)

                                    time.sleep(delay)
                                except TypeError:
                                    tqdm.write(f"{timeoutput()} - Plex metadata ID appears to be missing.")
                                counter += 1

                            elif plex_items.agent == "plex":
                                match_found = 0
                                if arrtype == "radarr":
                                    for tmdbid in plex_items.tmdb:
                                        if items.id == tmdbid:
                                            match_found = 1
                                            break
                                    if not match_found:
                                        tqdm.write(
                                            f"{timeoutput()} - Plex metadata item {plex_items.metadataid} with tmdb ID:{plex_items.tmdb} did not match {arrinstance} tmdb ID:{items.id}")
                                        tqdm.write(
                                            f"{timeoutput()} - Path: {items.mappedpath}")
                                        try:
                                            plex_match(config["plex_url"],
                                                       config["plex_token"],
                                                       "plextmdb",
                                                       plex_items.metadataid,
                                                       items.id,
                                                       items.title,
                                                       delay)

                                            time.sleep(delay)
                                        except TypeError:
                                            tqdm.write(f"{timeoutput()} - Plex metadata ID appears to be missing.")
                                        counter += 1
                                elif arrtype == "sonarr":
                                    for tvdbid in plex_items.tvdb:
                                        if items.id == tvdbid:
                                            match_found = 1
                                            break
                                    if not match_found:
                                        tqdm.write(
                                            f"{timeoutput()} - Plex metadata item {plex_items.metadataid} with tvdb ID:{plex_items.tvdb} did not match {arrinstance} tvdb ID:{items.id}")
                                        tqdm.write(
                                            f"{timeoutput()} - Path: {items.mappedpath}")
                                        try:
                                            plex_match(config["plex_url"],
                                                       config["plex_token"],
                                                       "plextvdb",
                                                       plex_items.metadataid,
                                                       items.id,
                                                       items.title,
                                                       delay)

                                            time.sleep(delay)
                                        except TypeError:
                                            tqdm.write(f"{timeoutput()} - Plex metadata ID appears to be missing.")
                                        counter += 1

                            else:
                                if items.id == plex_items.id:
                                    break
                                tqdm.write(f"{timeoutput()} - Plex metadata item {plex_items.metadataid} with {agent} ID:{plex_items.id} did not match {arrinstance} {agent} ID:{items.id}")
                                tqdm.write(f"{timeoutput()} - Path: {items.mappedpath}")
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
            if agent == "plextmdb":
                url_params = {'X-Plex-Token': token,
                              'guid': f'tmdb://{agentid}?lang=en',
                              'name': title}
            elif agent == "plextvdb":
                url_params = {'X-Plex-Token': token,
                              'guid': f'tvdb://{agentid}?lang=en',
                              'name': title}
            else:
                url_params = {'X-Plex-Token': token,
                              'guid': f'com.plexapp.agents.{agent}://{agentid}?lang=en',
                              'name': title}

            url_str = f'{url}/library/metadata/{int(metadataid):d}/match'
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

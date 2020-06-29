import pandas as pd
from classes.timer import *
from classes.plex import *
from classes.plexdb import *
from classes.arr import *
from classes.arrmedia import *
runtime = Timer()

config_timer = Timer()
print("Loading Configuration")
config = json.load(open("config.json"))
sonarr_config = [*config["sonarr"]]
radarr_config = [*config["radarr"]]

sonarrs_config = {}
for x in sonarr_config:
    sonarrs_config[x] = config["sonarr"][x]

radarrs_config = {}
for x in radarr_config:
    radarrs_config[x] = config["radarr"][x]

print(f"Loading Configuration took {config_timer.stop()} seconds.")

media_timer = Timer()
print("Loading Data From Plex, Sonarr & Radarr")

media = {}
media["sonarr"] = {}
media["radarr"] = {}
for x in [*sonarrs_config]:
    media["sonarr"][x] = Arr(sonarrs_config[x]["url"], sonarrs_config[x]["apikey"], "series").data

for x in [*radarrs_config]:
    media["radarr"][x] = Arr(radarrs_config[x]["url"], radarrs_config[x]["apikey"], "movie").data

sonarr = {}
radarr = {}
plexlibrary = {}

for Arrs, mediaDB in media.items():
    for showDB, shows in mediaDB.items():
        if Arrs == "sonarr":
            sonarr[showDB] = [ArrMedia(seriesShow["title"], seriesShow["path"], seriesShow["tvdbId"], seriesShow["titleSlug"]) for seriesShow in shows]
            plexlibrary[showDB] = [Plex(row[0], row[1], row[2], row[3], row[4]) for row in PlexDB().shows(config["plex_db"], sonarrs_config[showDB]["library_id"])]
        if Arrs == "radarr":
            radarr[showDB] = [ArrMedia(movies["title"], movies["path"], movies["tmdbId"], movies["titleSlug"]) for movies in shows]
            plexlibrary[showDB] = [Plex(row[0], row[1], row[2], row[3], row[4]) for row in PlexDB().movie(config["plex_db"], radarrs_config[showDB]["library_id"])]

print(f"Loading Data From Plex, Sonarr & Radarr took {media_timer.stop()} seconds.")

faulty_timer = Timer()
print("Checking for faulty data in Radarr & Sonarr")
for radarrDB in [*radarrs_config]:
    radarr_showPanda = pd.DataFrame()
    radarr_paths = pd.DataFrame()
    radarr_duplicate = pd.DataFrame()
    print(f"Checking {radarrDB}")
    radarr_showPanda = pd.DataFrame.from_records([item.to_dict() for item in radarr[radarrDB]])
    radarr_paths = radarr_showPanda["path"]
    radarr_slugs = radarr_showPanda["slug"]
    radarr_duplicate = radarr_showPanda[radarr_paths.isin(radarr_paths[radarr_paths.duplicated()])]
    for path, slug in zip(radarr_duplicate.values.tolist(), radarr_slugs.values.tolist()):
        print(f"Duplicate path in item: {radarrs_config[radarrDB]['url']}/movie/{slug}")

for sonarrDB in [*sonarrs_config]:
    sonarr_showPanda = pd.DataFrame()
    sonarr_paths = pd.DataFrame()
    sonarr_duplicate = pd.DataFrame()
    print(f"Checking {sonarrDB}")
    sonarr_showPanda = pd.DataFrame.from_records([item.to_dict() for item in sonarr[sonarrDB]])
    sonarr_paths = sonarr_showPanda["path"]
    sonarr_slugs = sonarr_showPanda["slug"]
    sonarr_duplicate = sonarr_showPanda[sonarr_paths.isin(sonarr_paths[sonarr_paths.duplicated()])]
    for path, slug in zip(sonarr_duplicate.values.tolist(), sonarr_slugs.values.tolist()):
        print(f"Duplicate path in item: {sonarrs_config[sonarrDB]['url']}/series/{slug}")

print(f"Checking for faulty data in Radarr & Sonarr took {faulty_timer.stop()} seconds.")

plex_duplicate_timer = Timer()
print("Checking for Duplicate Media")

for arrDB in [*plexlibrary]:
    plex_showPanda = pd.DataFrame.from_records([plex.to_dict() for plex in plexlibrary[arrDB]])
    plex_ids = plex_showPanda["id"]
    plex_duplicates = plex_showPanda[plex_ids.isin(plex_ids[plex_ids.duplicated()])]

    for u in plex_duplicates.values.tolist():
        print(f"Splitting item with ID:{u[2]}")
        url_params = {
            'X-Plex-Token': config["plex_token"]
        }
        url_str = '%s/library/metadata/%d/split' % (config["plex_url"], int(u[2]))
        requests.options(url_str, params=url_params, timeout=30)
        resp = requests.put(url_str, params=url_params, timeout=30)

print(f"Checking for Duplicate Media took {plex_duplicate_timer.stop()} seconds.")
print("Checking for Mismatched Media")
plex_mismatch_timer = Timer()

for radarrDB in [*radarrs_config]:
    for movie in radarr[radarrDB]:
        for plexMovie in plexlibrary[radarrDB]:
            if movie.path == plexMovie.fullpath:
                if movie.id == plexMovie.id:
                    break
                else:
                    print(f"Radarr title: {movie.title} did not match Plex title: {plexMovie.title}")
                    print(f"Radarr id: {movie.id} -- Plex id: {plexMovie.id}")
                    url_params = {
                        'X-Plex-Token': config["plex_token"],
                        'guid': 'com.plexapp.agents.themoviedb://{}?lang=en'.format(movie.id),
                        'name': movie.title,
                    }
                    url_str = '%s/library/metadata/%d/match' % (config["plex_url"], int(plexMovie.metadataid))
                    requests.options(url_str, params=url_params, timeout=30)
                    resp = requests.put(url_str, params=url_params, timeout=30)
                    url_params = {
                        'X-Plex-Token': config["plex_token"]
                    }
                    url_str = '%s/library/metadata/%d/refresh' % (config["plex_url"], int(plexMovie.metadataid))
                    requests.options(url_str, params=url_params, timeout=30)
                    resp = requests.put(url_str, params=url_params, timeout=30)

for sonarrDB in [*sonarrs_config]:
    for series in sonarr[sonarrDB]:
        for plexSeries in plexlibrary[sonarrDB]:
            if series.path == plexSeries.fullpath:
                if series.id == plexSeries.id:
                    break
                else:
                    print(f"Sonarr title: {series.title} did not match Plex title: {plexSeries.title}")
                    print(f"Sonarr id: {series.id} -- Plex id: {plexSeries.id}")
                    url_params = {
                        'X-Plex-Token': config["plex_token"],
                        'guid': 'com.plexapp.agents.thetvdb://{}?lang=en'.format(series.id),
                        'name': series.title,
                    }
                    url_str = '%s/library/metadata/%d/match' % (config["plex_url"], int(plexSeries.metadataid))
                    requests.options(url_str, params=url_params, timeout=30)
                    resp = requests.put(url_str, params=url_params, timeout=30)
                    url_params = {
                        'X-Plex-Token': config["plex_token"]
                    }
                    url_str = '%s/library/metadata/%d/refresh' % (config["plex_url"], int(plexSeries.metadataid))
                    requests.options(url_str, params=url_params, timeout=30)
                    resp = requests.put(url_str, params=url_params, timeout=30)

print(f"Checking for Mismatched Media took {plex_mismatch_timer.stop()} seconds.")
print(f"Running the program took {runtime.stop()} seconds.")

Current assumptions / limitations:

Agents for movies are tmdb (Plex Movie can also use tmdb) and not imdb.

Agents for shows are tvdb which means no HAMA or tmdb.

Identical root paths in sonarr,radarr and Plex.

Use something like [Plex Autoscan](https://github.com/l3uddz/plex_autoscan) to identify the IDs of your libraries. Below is a snippet from the Plex Autoscan readme:
### Plex Section IDs

Running the following command, will return a list of Plex Library Names and their corresponding Section IDs (sorted by alphabetically Library Name):

```shell
python scan.py sections
```

This will be in the format of:

```
SECTION ID #: LIBRARY NAME
```

Sample output:

```
 2018-06-23 08:28:27,070 -     INFO -      PLEX [140425529542400]: Using Plex Scanner
  1: Movies
  2: TV
```

Then you will have to enter your sonarr and radarr instances into the config (rename the sample to config.json):

```
{
  "plex_db": "/opt/plex/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db",
  "plex_token": "",
  "plex_url": "https://plex.domain.tld",
  "radarr": {
    "radarr2": {
      "library_id": "1",
      "url": "https://radarr.domain.tld",
      "apikey": ""
    },
    "radarr4k": {
      "library_id": "11",
      "url": "https://radarr4k.domain.tld",
      "apikey": ""
    }
  },
  "sonarr": {
    "sonarr": {
      "library_id": "2",
      "url": "https://sonarr.domain.tld",
      "apikey": ""
    },
    "sonarr4k": {
      "library_id": "12",
      "url": "https://sonarr4k.domain.tld",
      "apikey": ""
    }
  }
}
```

You can add as many sonarr or radarr instances as you would like but there is no formatting check built into my script so make sure it is valid json. 
You can grab your Plex token from Plex Autoscan or look [here](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/).

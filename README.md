Current assumptions / limitations:
* Agents for movies are tmdb (Plex Movie can also use tmdb) and not imdb.
* Agents for shows are tvdb which means no HAMA or tmdb.
* Identical root paths in sonarr,radarr and Plex.
* Assumes that you are using a similar directory structure to the ones recommended by Plex. 
This for [movies](https://support.plex.tv/articles/naming-and-organizing-your-movie-media-files/) 
and this for [TV Shows](https://support.plex.tv/articles/naming-and-organizing-your-tv-show-files/). 
If you deviate from the structure you should assume that this script will not work for your setup. 
Names of the files/folders are not important as long as they are unique since we use the data in 
the various sonarr/radarr instances to figure out which is which and not relying on Plex to guess.

There is at present time no config validation so be careful with setting it up. 
Once the core functionality has been more thoroughly tested I will work on config validation.

Use something like [Plex Autoscan](https://github.com/l3uddz/plex_autoscan) to identify the IDs of 
your libraries. Below is a snippet from the Plex Autoscan readme:
### Plex Section IDs

Running the following command, will return a list of Plex Library Names and 
their corresponding Section IDs (sorted by alphabetically Library Name):

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

Then you will have to enter your sonarr and radarr instances into the config 
(rename the sample to config.json):

```
{
  "plex_db": "/opt/plex/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db",
  "plex_token": "",
  "plex_url": "https://plex.domain.tld",
  "plex_enabled": false,
  "emby_token": "",
  "emby_url":  "https://emby.domain.tld",
  "emby_enabled": false,
  "delay": 10,
  "radarr": {
    "radarr": {
      "plex_library_id": "1",
      "emby_library_id": "None",
      "url": "https://radarr.domain.tld",
      "apikey": ""
    },
    "radarr4k": {
      "plex_library_id": "11",
      "emby_library_id": "None",
      "url": "https://radarr4k.domain.tld",
      "apikey": ""
    }
  },
  "sonarr": {
    "sonarr": {
      "plex_library_id": "2",
      "emby_library_id": "None",
      "url": "https://sonarr.domain.tld",
      "apikey": ""
    },
    "sonarr4k": {
      "plex_library_id": "12",
      "emby_library_id": "2007",
      "url": "https://sonarr4k.domain.tld",
      "apikey": ""
    }
  }
}
```

You can add as many sonarr or radarr instances (but with unique names) as you would like but 
there is no formatting check built into my script so make sure it is valid json. 
You can grab your Plex token from Plex Autoscan or look 
[here](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/).

### Emby Section IDs
Run the following command with your own url and apikey to get the library information you need:

```
curl -X GET "https://emby.domain.tld/emby/Library/SelectableMediaFolders?api_key=<insert apikey>" -H "accept: application/json"
```
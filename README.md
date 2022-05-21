### Matcharr
Matcharr compares data from Sonarr/Radarr instances to libraries in Plex/Emby and fixes any mismatches created by the agents used.

### Python
Python 3.8 is the targetted requirement for this script. May work with other versions just don't assume it will.

### Current assumptions / limitations
* Agents for movies are Plex Movie, tmdb or imdb.
* Agents for shows are Plex TV Series or tvdb.
* Assumes that you are using a similar directory structure to the ones recommended by Plex. 
This for [movies](https://support.plex.tv/articles/naming-and-organizing-your-movie-media-files/) 
and this for [TV Shows](https://support.plex.tv/articles/naming-and-organizing-your-tv-show-files/). 
If you deviate from the structure you should assume that this script will not work for your setup. 
Names of the files/folders are not important as long as they are unique since we use the folder data in 
the various sonarr/radarr instances to figure out which is which and not relying on Plex to guess.

### Emby notice
Matcharr will queue the refresh requests in Emby after editing the metadata which means that if 
you have significant amount of rematches (especially TV shows) it is recommended to not 
restart Emby until it is done refreshing. On my own system Emby uses 2 seconds per file, so a movie 
will only take 2 seconds while TV Shows will take 2 seconds for every episode in it.

### Configuration
There is at present time no config validation so be careful with setting it up. 
Once the core functionality has been more thoroughly tested I will work on config validation.

Template looks like this:

```json
{
  "plex_token": "",
  "plex_url": "https://plex.domain.tld",
  "plex_enabled": false,
  "emby_token": "",
  "emby_url": "https://emby.domain.tld",
  "emby_enabled": false,
  "delay": 10,
  "path_mappings": {
    "/mnt/unionfs/Media/": "/data/",
    "/mnt/unionfs/Media/Movies/": "/movies/",
    "/mnt/unionfs/Media/TV/": "/tv/"
  },
  "radarr": {
    "radarr": {
      "url": "https://radarr.domain.tld",
      "apikey": ""
    },
    "radarr4k": {
      "url": "https://radarr4k.domain.tld",
      "apikey": ""
    }
  },
  "sonarr": {
    "sonarr": {
      "url": "https://sonarr.domain.tld",
      "apikey": ""
    },
    "sonarr4k": {
      "url": "https://sonarr4k.domain.tld",
      "apikey": ""
    }
  }
}
```

#### Media Server Section
```json
"plex_token": "",
"plex_url": "https://plex.domain.tld",
"plex_enabled": false,
"emby_token": "",
"emby_url": "https://emby.domain.tld",
"emby_enabled": false,
"delay": 10,
```
Enable the client(s) you want to use after entering the url and api token. If using Plex you can edit the delay option to change the rate of requests to Plex when it comes to metadata changes/refreshes if it overwhelms the Plex instance, or you want to go faster.

For Plex, you can get your token from Plex Autoscan or look [here](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/).

#### Path Mapping Section
```json
"path_mappings": {
  "/mnt/unionfs/Media/": "/data/",
  "/mnt/unionfs/Media/Movies/": "/movies/",
  "/mnt/unionfs/Media/TV/": "/tv/"
},
```
You can add as many mapping entries as you'd like as long as the values on the right are unique. Script, using the above example, checks if the path starts with /data/, /tv/ or /movies/ and replaces it with the corresponding value set in the config. So enter the path that is used in your Sonarr/Radarr/Plex/Emby instances and then the corresponding path on the host that is running the script.

#### Arr Section
```json
"radarr": {
  "radarr": { <-- Unique name for instance
    "url": "https://radarr.domain.tld",
    "apikey": ""
  },
  "radarr4k": { <-- Unique name for instance
    "url": "https://radarr4k.domain.tld",
    "apikey": ""
  }
},
"sonarr": {
  "sonarr": { <-- Unique name for instance
    "url": "https://sonarr.domain.tld",
    "apikey": ""
  },
  "sonarr4k": { <-- Unique name for instance
    "url": "https://sonarr4k.domain.tld",
    "apikey": ""
  }
}
```
Enter the url and apikey for your instances. There is no set limit to how many instances you can enter here but make sure that they have unique names.

### Current assumptions / limitations
* Agents for movies are tmdb (Plex Movie can also use tmdb) and not imdb.
* Agents for shows are tvdb which means no HAMA or tmdb.
* Script has to run somewhere with access to the directory used in Sonarr/Radarr/Plex to use 
some python functionality to strip filename out of paths for movie libraries in Plex.
* Assumes that you are using a similar directory structure to the ones recommended by Plex. 
This for [movies](https://support.plex.tv/articles/naming-and-organizing-your-movie-media-files/) 
and this for [TV Shows](https://support.plex.tv/articles/naming-and-organizing-your-tv-show-files/). 
If you deviate from the structure you should assume that this script will not work for your setup. 
Names of the files/folders are not important as long as they are unique since we use the data in 
the various sonarr/radarr instances to figure out which is which and not relying on Plex to guess.

### Emby notice
Matcharr will queue the refresh requests in Emby after editing the metadata which means that if 
you have significant amount of rematches (especially TV shows) it is recommended to not 
restart Emby until it is done refreshing. On my own system Emby uses 2 seconds per file, so a movie 
will only take 2 seconds while TV Shows will take 2 seconds for every episode in it.

### Configuration
There is at present time no config validation so be careful with setting it up. 
Once the core functionality has been more thoroughly tested I will work on config validation.

You will have to enter your sonarr and radarr instances into the config 
(rename the sample to config.json):

```
{
  "plex_token": "",
  "plex_url": "https://plex.domain.tld",
  "plex_enabled": false,
  "emby_token": "",
  "emby_url": "https://emby.domain.tld",
  "emby_enabled": false,
  "delay": 10,
  "path_mappings": {
    "/mnt/unionfs/Media/": [ # Path that the script can see the files.
      "/data/"               # Any paths used in Plex/Sonarr/Radarr that does not match the above.
    ]
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

You can add as many sonarr or radarr instances (but with unique names) as you would like but 
there is no formatting check built into my script so make sure it is valid json. 
You can grab your Plex token from Plex Autoscan or look 
[here](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/).
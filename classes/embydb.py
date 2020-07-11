import requests
import requests.exceptions
import json


class EmbyDB:
    @staticmethod
    def data(config, libraryid):
        fields = 'ProviderIds%2CPath'
        url_params = {
            'X-Emby-Token': config["emby_token"]
        }
        url_str = '%s/emby/Items?ParentId=%d&Fields=%s' % (config["emby_url"], int(libraryid), fields)
        requests.options(url_str, params=url_params, timeout=30)
        resp = requests.get(url_str, params=url_params, timeout=30)
        result = json.loads(resp.content)
        return result["Items"]

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
        resp = requests.get(url_str, params=url_params, timeout=30)
        result = json.loads(resp.content)
        return result["Items"]

    @staticmethod
    def libraries(config):
        url_params = {
            'X-Emby-Token': config["emby_token"]
        }
        url_str = f'{config["emby_url"]}/emby/Library/SelectableMediaFolders'
        resp = requests.get(url_str, params=url_params, timeout=30)
        result = json.loads(resp.content)

        emby_libraries = {}
        x = 0
        for library in result:
            for subfolder in library.get('SubFolders'):
                emby_libraries[x] = subfolder
                x += 1

        return emby_libraries

    @staticmethod
    def sections(config):
        url_params = {
            'X-Emby-Token': config["emby_token"]
        }
        url_str = f'{config["emby_url"]}/emby/Library/SelectableMediaFolders'
        resp = requests.get(url_str, params=url_params, timeout=30)
        result = json.loads(resp.content)

        emby_sections = {}
        for library in result:
            for subfolder in library.get('SubFolders'):
                emby_sections[subfolder.get('Id')] = library.get('Name')

        return emby_sections

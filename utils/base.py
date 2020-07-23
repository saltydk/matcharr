from datetime import datetime
from tqdm import tqdm


def timeoutput():
    now = datetime.now()
    return now.strftime('%d %b %Y %H:%M:%S')


def giefbar(iterator, desc):
    return tqdm(iterator, desc=desc + ":",
                bar_format="{desc:80} {percentage:3.0f}%|{bar}| {n_fmt:^5}/{total_fmt:^5} [{elapsed_s:5.0f} s]")


def map_path(config, path):
    for mapped_path, mapping in config['path_mappings'].items():
        if path.startswith(mapping):
            return path.replace(mapping, mapped_path)
    return path

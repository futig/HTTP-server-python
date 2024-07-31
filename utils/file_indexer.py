import os
from pathlib import Path

from models.exceptions import WrongPathException


class FileIndexer:
    def __init__(self, root_folder, home_page_file_path, media):
        self.URLS = dict()
        self.root = root_folder
        self.media = media
        self.home_page = Path(home_page_file_path)
        self.index_files()

    def index_files(self):
        self._check_paths_existence()
        self.update_urls(self.root)
        self.update_urls(self.media, save_suffix=True)
        self.URLS[Path('\\')] = self.home_page

    def contains(self, url):
        return Path(url) in self.URLS

    def get_page_path(self, url):
        file = Path(url)
        if file in self.URLS.keys():
            return self.URLS[file]
        raise WrongPathException(file)

    def get_page_code(self, url):
        page_path = self.get_page_path(url)
        with open(page_path) as template:
            return template.read()

    def update_urls(self, root, save_suffix=False):
        levels = len(Path(root).parts)
        stack = [root]
        while len(stack) > 0:
            for file in Path(stack.pop()).iterdir():
                if file.is_dir():
                    stack.append(file)
                    continue
                url = list(file.parts[levels:])
                if not save_suffix:
                    url[-1] = file.stem
                self.URLS[os.path.join(*url)] = file

    def index_file(self, file_path, save_suffix=False):
        file = Path(file_path)
        if file.parts[0] != self.root:
            return
        url = list(file.parts[1:])
        if not save_suffix:
            url[-1] = file.stem
        self.URLS[os.path.join(*url)] = file

    def remove_file(self, file_path):
        file = Path(file_path)
        if file.parts[0] != self.root:
            return

        if os.path.exists(file_path):
            os.remove(file_path)

        url = list(file.parts[1:])
        suffix_url = os.path.join(*url)
        if suffix_url in self.URLS:
            self.URLS.remove(suffix_url)
        else:
            url[-1] = file.stem
            stem_url = os.path.join(*url)
            if stem_url in self.URLS:
                self.URLS.remove(stem_url)

    def _check_paths_existence(self):
        if not os.path.exists(self.home_page):
            raise WrongPathException(self.home_page)

        if not os.path.exists(self.root):
            raise WrongPathException(self.root)

        if not os.path.exists(self.media):
            raise WrongPathException(self.media)

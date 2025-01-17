import os
import time
from pathlib import Path

from models.exceptions import WrongPathException


class FileManager:
    def __init__(self, root_folder, home_page_file_path, media):
        self.URLS = dict()
        self.root_path = root_folder
        self.root_path_lvl = len(Path(root_folder).parts)
        self.media_path = media
        self.media_path_lvl = len(Path(media).parts)
        self.home_page = Path(home_page_file_path)
        self.index_files()
        if not os.path.exists(media_path):
            os.mkdir(media_path)

    def index_files(self):
        self._check_paths_existence()
        self.update_urls(self.root_path)
        self.update_urls(self.media_path, save_suffix=True)
        self.URLS[Path("/")] = self.home_page

    def contains(self, url):
        return Path(url) in self.URLS

    def get_page_path(self, url):
        file = Path(url)
        if file in self.URLS.keys():
            return self.URLS[file]
        raise WrongPathException(file)

    def get_page_code(self, url):
        page_path = self.get_page_path(url)
        method = "rb" if Path(url).suffix else "r"
        with open(page_path, method) as content:
            return content.read()

    def update_urls(self, root, save_suffix=False):
        levels = len(Path(root).parts)
        stack = [root]
        while len(stack) > 0:
            for file in Path(stack.pop()).iterdir():
                if file.is_dir():
                    stack.append(file)
                    continue
                url = list(file.parts[levels:])
                if not save_suffix and file.stem != "favicon":
                    url[-1] = file.stem
                self.URLS[Path(os.path.join("/", *url))] = file

    def index_media(self, file_path):
        if not self.path_starts_with(file_path, self.media_path):
            return
        file = Path(file_path)
        url = list(file.parts[self.root_path_lvl :])
        self.URLS[Path(os.path.join("/", *url))] = file

    def path_starts_with(self, first, second):
        """Checks if first path starts with second"""
        first_parts = Path(first).parts
        second_parts = Path(second).parts
        for i in range(len(second_parts)):
            if first_parts[i] != second_parts[i]:
                return False
        return True

    def _check_paths_existence(self):
        if not os.path.exists(self.home_page):
            raise WrongPathException(self.home_page)

        if not os.path.exists(self.root_path):
            raise WrongPathException(self.root_path)

        if not os.path.exists(self.media_path):
            raise WrongPathException(self.media_path)

    def get_media_links(self):
        res = []
        for url in self.URLS.keys():
            suffix = Path(url).suffix
            if suffix and suffix != ".ico":
                res.append(url)
        return res

    def save_media(self, data):
        split = data.split(b"\r\n\r\n")
        info = split[0]
        body = split[1]
        for part in info.split(b"\r\n"):
            if b'filename="' in part:
                filename = part.split(b'filename="')[1].split(b'"')[0].decode()
                break
        file_path = os.path.join(self.media_path, filename)
        if os.path.exists(file_path):
            filename = str(time.time()) + Path(filename).suffix
            file_path = os.path.join(self.media_path, filename)
        with open(file_path, "wb") as file:
            file.write(body)
        self.index_media(file_path)

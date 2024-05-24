import os.path
from os import walk, path
from pathlib import Path

from exceptions import WrongPathException


class FileIndexer:
    def __init__(self, root_folder, home_page_file_path):
        self.URLS = dict()
        self.root = root_folder
        self.home_page = Path(home_page_file_path)
        self.index_files()

    def index_files(self):
        if not os.path.exists(self.home_page):
            raise WrongPathException(self.home_page)
        files_root_level = 0
        root_path = Path(self.root)
        for part in root_path.parts:
            files_root_level += 1
            if part == root_path.stem:
                break
        for (dir_path, _, filenames) in walk(self.root):
            for filename in filenames:
                file_path = path.join(dir_path, filename)
                dir_parts = Path(dir_path).parts[files_root_level:]
                site_path = "\\" + path.join(*dir_parts, Path(filename).stem)
                self.URLS[Path(site_path)] = file_path
        self.URLS[Path('\\')] = self.home_page

    def contains(self, site_path):
        return Path(site_path) in self.URLS.keys()

    def get_page_path(self, site_path):
        file = Path(site_path)
        if file in self.URLS.keys():
            return self.URLS[file]
        raise WrongPathException(path)

    def get_page_code(self, site_path):
        page_path = self.get_page_path(site_path)
        with open(page_path) as template:
            return template.read()

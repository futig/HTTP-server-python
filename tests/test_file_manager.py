import os
import unittest
from unittest.mock import patch, mock_open
from pathlib import Path
from models.exceptions import WrongPathException
from utils.file_manager import FileManager


class TestFileManager(unittest.TestCase):

    def setUp(self):
        self.root_folder = "tests/src/root"
        self.home_page_file = "tests/src/root/home.html"
        self.media_folder = "tests/src/media"
        os.makedirs(self.root_folder, exist_ok=True)
        os.makedirs(self.media_folder, exist_ok=True)
        with open(self.home_page_file, "w") as f:
            f.write("<html></html>")

        self.file_manager = FileManager(
            self.root_folder, self.home_page_file, self.media_folder
        )

    def tearDown(self):
        if os.path.exists(self.home_page_file):
            os.remove(self.home_page_file)
        if os.path.exists(self.media_folder):
            os.rmdir(self.media_folder)
        if os.path.exists(self.root_folder):
            os.rmdir(self.root_folder)

    def test_index_files(self):
        self.assertIn(Path("/"), self.file_manager.URLS)
        self.assertEqual(self.file_manager.URLS[Path("/")], Path(self.home_page_file))

    def test_contains(self):
        url = Path("/")
        self.assertTrue(self.file_manager.contains(url))
        non_existent_url = Path("/non_existent")
        self.assertFalse(self.file_manager.contains(non_existent_url))

    def test_get_page_path_valid(self):
        url = Path("/")
        self.assertEqual(
            self.file_manager.get_page_path(url), Path(self.home_page_file)
        )

    def test_get_page_path_invalid(self):
        with self.assertRaises(WrongPathException):
            self.file_manager.get_page_path("/invalid_url")

    @patch("builtins.open", new_callable=mock_open, read_data="<html></html>")
    def test_get_page_code(self, mock_file):
        url = "/"
        content = self.file_manager.get_page_code(url)
        self.assertEqual(content, "<html></html>")
        mock_file.assert_called_once_with(Path(self.home_page_file), "r")

    def test_update_urls(self):
        file_path = os.path.join(self.root_folder, "test.txt")
        with open(file_path, "w") as f:
            f.write("test")
        self.file_manager.update_urls(self.root_folder)
        self.assertIn(Path("/test"), self.file_manager.URLS)
        os.remove(file_path)

    def test_index_media(self):
        file_path = os.path.join(self.media_folder, "image.jpg")
        with open(file_path, "wb") as f:
            f.write(b"image data")
        self.file_manager.index_media(file_path)
        self.assertIn(Path("/image.jpg"), self.file_manager.URLS)
        os.remove(file_path)

    def test_path_starts_with(self):
        self.assertTrue(
            self.file_manager.path_starts_with(self.root_folder, self.root_folder)
        )
        self.assertFalse(
            self.file_manager.path_starts_with(self.root_folder, self.media_folder)
        )

    @patch("os.path.exists", return_value=False)
    @patch("builtins.open", new_callable=mock_open)
    def test_save_media(self, mock_file, mock_exists):
        data = b'Content-Disposition: form-data; name="file"; filename="test.jpg"\r\n\r\nimage data'
        self.file_manager.save_media(data)
        self.assertIn(Path("/test.jpg"), self.file_manager.URLS)
        mock_file.assert_called_once_with(
            os.path.join(self.media_folder, "test.jpg"), "wb"
        )

    def test_get_media_links(self):
        file_path = os.path.join(self.media_folder, "image.jpg")
        with open(file_path, "wb") as f:
            f.write(b"image data")
        self.file_manager.update_urls(self.media_folder, True)
        media_links = self.file_manager.get_media_links()
        self.assertIn(Path("/image.jpg"), media_links)
        os.remove(file_path)


if __name__ == "__main__":
    unittest.main()

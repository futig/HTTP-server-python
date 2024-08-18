import unittest
from unittest.mock import MagicMock
from utils.request_parser import RequestParser


class TestRequestParser(unittest.TestCase):

    def setUp(self):
        self.file_manager = MagicMock()
        self.parser = RequestParser(self.file_manager)

    def test_parse_request(self):
        data = "GET /index.html HTTP/1.1\r\nConnection: keep-alive\r\nContent-Length: 123\r\nUser-Agent: TestAgent\r\n"
        request = self.parser.parse_request(data)

        self.assertEqual(request.method, "GET")
        self.assertEqual(request.url, "/index.html")
        self.assertEqual(request.page_name, "index.html")
        self.assertEqual(request.http_version, "HTTP/1.1")
        self.assertEqual(request.connection, "keep-alive")
        self.assertEqual(request.content_length, 123)
        self.assertEqual(request.user_agent, "TestAgent")

    def test_parse_request_body_with_image(self):
        request_info = MagicMock()
        request_info.page_name = "uploaded_image"
        body = b"--boundary\r\nContent-Disposition: form-data; name=\"file\"; filename=\"test.jpg\"\r\n\r\nimage data\r\n--boundary--"

        self.parser.parse_request_body(request_info, body)
        self.file_manager.save_media.assert_called_once_with(body)

    def test_parse_request_body_with_login(self):
        request_info = MagicMock()
        request_info.page_name = "logger_name"
        body = "name=John&surname=Doe"

        self.parser.parse_request_body(request_info, body)
        self.assertEqual(request_info.login_body, "John Doe")

    def test_parse_request_body_with_empty_body(self):
        request_info = MagicMock()
        request_info.page_name = "logger_name"
        request_info.login_body = None
        body = b""

        self.parser.parse_request_body(request_info, body)
        self.assertFalse(request_info.login_body)


if __name__ == '__main__':
    unittest.main()

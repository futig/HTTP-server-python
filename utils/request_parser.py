import re
from pathlib import Path

from models.request import Request


class RequestParser:
    def __init__(self, file_manager):
        self._file_manager = file_manager

    def parse_request(self, data: str):
        headers = data.split("\r\n")
        first_line = headers[0].split()
        request = Request(first_line[0], first_line[1], 
                          first_line[2], Path(first_line[1]).name)
        for i in range(1, len(headers)):
            if headers[i].startswith("Connection:"):
                request.connection = headers[i].split(":")[1].strip()
            elif headers[i].startswith("Content-Length:"):
                request.content_length = int(headers[i].split(":")[1].strip())
            elif headers[i].startswith("User-Agent:"):
                request.user_agent = headers[i].split(":")[1].strip()   
        return request

    def parse_request_body(self, request_info, body):
        if not body:
            return
        if request_info.page_name == "download":
            self.parse_media(body)
        elif request_info.page_name == "logger_name":
            request_info.request_body = self.parse_login(body)
        
    def parse_media(self, data):
        self._file_manager.save_media(data)

    def parse_login(self, data):
        replaced = data.replace("+", " ")
        info_dict = dict(pair.split("=") for pair in replaced.split("&") if pair)
        return f"{info_dict["name"]} {info_dict["surname"]}"
    
import re
from models.user_info import UserInfo

from models.exceptions import BadRequestException


class RequestParser:
    def __init__(self):
        self._pattern = re.compile(
            r"^(?P<method>GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH|TRACE) "
            r"(?P<url>/\S*) (?P<version>HTTP/\d\.\d)\r?\n(?:.*\r?\n)*"
            r"User-Agent: (?P<user_agent>.+)")

    def parse_request(self, request: str):
        match = self._pattern.search(request)
        if not match:
            raise BadRequestException(request)
        request_info = {
            "method": match.group('method'),
            "url": match.group('url'),
            "http-version": match.group('version'),
            "connection": "Connection: keep-alive" in request,
            "user_agent": match.group('user_agent')
        }
        return request_info, []

    def parse_request_body(self, body: str):  # name=Vasia&surname=Petrovich&submit=Send
        if not body:
            return
        replaced = body.replace('+', ' ')
        info_dict = dict(pair.split("=") for pair in replaced.split('&') if pair)
        return UserInfo(info_dict["name"], info_dict["surname"])

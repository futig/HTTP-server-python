import configparser
import os
import socket
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import models.exceptions as exc
from utils.file_manager import FileManager
from utils.logger import Logger
from utils.request_parser import RequestParser
from utils.response_generator import ResponseGenerator


class Server:
    def __init__(self, config):
        try:
            self._port = int(config["port"])
            self._ip_address = config["ip-address"]
            self._request_size = int(config["request-size"])
            self._used_threads = int(config["used-threads"])

            self._connections_limit = int(config["connections_limit"])

            self._keep_alive_timeout = int(config["keep-alive-timeout"])
            self._keep_alive_max_requests = int(config["keep-alive-max-requests"])
            self._debug = bool(config["debug"])

            self._logger = Logger(config["access-log"])
            self._file_manager = FileManager(
                os.path.join(os.getcwd(), config["root"]),
                os.path.join(os.getcwd(), config["home_page_path"]),
                os.path.join(os.getcwd(), config["media"]),
            )
            self._mutex = Lock()
            self._parser = RequestParser(self._file_manager)
            self._response_generator = ResponseGenerator(
                self._file_manager,
                int(config["keep-alive-max-requests"]),
                bool(config["caching"]),
                int(config["keep-alive-timeout"]),
            )
        except KeyError as e:
            raise exc.ConfigFieldException(e) from None
        if self._debug:
            print("Server was initialized successfully", end="\n")

    def handle_client(self, client, address):
        keep_alive = True
        requests_count = 0

        if self._debug:
            print(f"Client {address[0]}:{address[1]} connected")

        while keep_alive and requests_count < self._keep_alive_max_requests:
            try:
                client.settimeout(self._keep_alive_timeout)
                data = client.recv(self._request_size)
                if not data:
                    break
                requests_count += 1
                request = data.decode("utf-8")
                
                request_info = self._parser.parse_request(request)
                request_info.client = address[0]
                request_info.requests_count = requests_count
                keep_alive = bool(request_info.connection)

                if request_info.method == "POST":
                    if request_info.page_name == "download":
                        request_body = client.recv(request_info.content_length)
                    else:
                        request_body = request[request_info.content_length:]
                    self._parser.parse_request_body(
                        request_info, request_body
                    )

                response, code = self._response_generator.generate_response(
                    request_info
                )

                # self._logger.add_record(request_info, code)
                client.sendall(response.encode("utf-8"))
                
            except socket.timeout:
                if self._debug:
                    print("Connection timed out")
                break        

        client.close()
        if self._debug:
            print(f"Client {address[0]}:{address[1]} disconnected")

    def run(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self._ip_address, self._port))
        server_socket.listen(self._connections_limit)

        with ThreadPoolExecutor(max_workers=self._used_threads) as executor:
            while True:
                client, address = server_socket.accept()
                executor.submit(self.handle_client, client, address)


if __name__ == "__main__":
    configuration = configparser.ConfigParser()
    configuration.read("config.ini")
    server = Server(configuration["SERVER"])
    server.run()

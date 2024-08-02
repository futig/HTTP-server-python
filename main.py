import configparser
import os
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import models.exceptions as exc
from utils.file_indexer import FileIndexer
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
            self._server = socket.create_server((self._ip_address, self._port))
            self._server.listen(self._connections_limit)

            self._keep_alive_timeout = int(config["keep-alive-timeout"])
            self._keep_alive_max_requests = int(config["keep-alive-max-requests"])
            self._debug = bool(config["debug"])

            self._logger = Logger(config["access-log"])
            self._file_indexer = FileIndexer(
                os.path.join(os.getcwd(), config["root"]),
                os.path.join(os.getcwd(), config["home_page_path"]),
                os.path.join(os.getcwd(), config["media"])
            )
            self._mutex = Lock()
            self._parser = RequestParser()
            self._response_generator = ResponseGenerator(
                self._file_indexer, int(config["keep-alive-max-requests"]),
                bool(config["caching"]), int(config["keep-alive-timeout"])
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
            print("enter loop")

            data = None
            start = time.time()
            while not data and time.time() - start < self._keep_alive_timeout:
                data = client.recv(self._request_size)
            if not data:
                break

            print("start decoding")
            requests_count += 1
            request = data.decode("utf-8")
            request_info, request_body = self._parser.parse_request(request)
            request_info["client"] = address[0]
            request_info["requests-count"] = requests_count
            keep_alive = request_info["connection"]

            response, code = self._response_generator.generate_response(
                request_info
            )

            # self._logger.add_record(request_info, code)
            client.send(response.encode("utf-8"))
            print("sent e=response")


        client.close()
        if self._debug:
            print(f"Client {address[0]}:{address[1]} disconnected")

    def run(self):
        with ThreadPoolExecutor(max_workers=self._used_threads) as executor:
            while True:
                client, address = self._server.accept()
                executor.submit(self.handle_client, client, address)

    def stop_server(self):
        self._server.close()
        print("Server was closed successfully")

    def __del__(self):
        self.stop_server()


if __name__ == "__main__":
    configuration = configparser.ConfigParser()
    configuration.read("config.ini")
    server = Server(configuration["SERVER"])
    server.run()

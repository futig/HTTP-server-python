import configparser
import asyncio
from threading import Lock

import models.exceptions as exc

from utils.file_indexer import FileIndexer
from utils.logger import Logger
from utils.request_parser import parse_request, parse_request_body
from utils.response_generator import generate_response


class Server:
    def __init__(self, config):
        try:
            self._port = int(config["port"])
            self._ip_address = config["ip-address"]
            self._request_size = int(config["request-size"])

            self._connections_limit = int(config["connections_limit"])
            self._active_connections = {}
            self._caching = bool(config["caching"])
            self._keep_alive_timeout = int(config["keep-alive-timeout"])
            self._keep_alive_max_requests = int(config["keep-alive-max-requests"])
            self._debug = bool(config["debug"])

            self._logger = Logger(config["access-log"])
            self._file_indexer = FileIndexer(
                config["root"], config["home_page_path"], config["media"]
            )
            self._mutex = Lock()

        except KeyError as e:
            raise exc.ConfigFieldException(e) from None

        if self._debug:
            print("Server was initialized successfully", end="\n")

    async def handle_client(self, reader, writer):
        client = writer.get_extra_info("peername")
        client_ip = client[1]
        client_port = client[0]
        keep_alive = True
        requests_count = 0

        if self._debug:
            print(f"Client connected: {client_ip}:{client_port}")

        while keep_alive and requests_count < self._keep_alive_max_requests:

            data = await asyncio.wait_for(
                reader.read(self._request_size), timeout=self._keep_alive_timeout
            )
            if not data:
                break

            requests_count += 1
            request = data.decode("utf-8")
            request_dict, request_body = parse_request(request)
            request_dict["client"] = client

            if not self._add_client_connection(client_ip):
                break

            user_info = None
            if request_dict["method"] == "POST":
                user_info = parse_request_body(request_body)
            response, code = generate_response(
                request_dict, user_info, self._file_indexer
            )

            await self._logger.add_record(request_dict, code)
            writer.write(response.encode("utf-8"))
            await writer.drain()

        self._remove_client_connection(client_ip)
        writer.close()
        await writer.wait_closed()
        if self._debug:
            print("Connection closed")

    async def run(self):
        async_server = await asyncio.start_server(
            self.handle_client, self._ip_address, self._port
        )
        if self._debug:
            print(f"Server started on {self._ip_address}:{self._port}")
        async with async_server:
            await async_server.serve_forever()

    def _add_client_connection(self, client_ip):
        self._mutex.acquire()
        if client_ip not in self._active_connections:
            self._active_connections[client_ip] = 0
        if self._active_connections[client_ip] >= self._connections_limit:
            return False
        self._active_connections[client_ip] += 1
        self._mutex.release()
        return True

    def _remove_client_connection(self, client_ip):
        self._mutex.acquire()
        if client_ip in self._active_connections:
            self._active_connections[client_ip] -= 1
            if self._active_connections[client_ip] < 1:
                self._active_connections.pop(client_ip)
        self._mutex.release()


if __name__ == "__main__":
    configuration = configparser.ConfigParser()
    configuration.read("config.ini")
    server = Server(configuration["SERVER"])
    asyncio.run(server.run())

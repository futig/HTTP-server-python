import configparser
import os
import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import time

import models.exceptions as exc
from utils.file_manager import FileManager
from utils.request_parser import RequestParser
from utils.response_generator import ResponseGenerator
from utils.page_caching import CashList


class Server:
    def __init__(self, config):
        try:
            self._port = int(config["port"])
            self._ip_address = config["ip-address"]
            self._request_size = int(config["request-size"])

            self._connections_limit = int(config["connections-limit"])
            self._client_connections_limit = int(config["client-connections-limit"])
            self._active_connections = {}

            self._too_many_requests_span = int(config["too-many-requests-span"])
            self._too_many_requests_limit = int(config["too-many-requests-limit"])

            self._keep_alive = bool(config["keep-alive"])
            self._keep_alive_timeout = int(config["keep-alive-timeout"])
            self._keep_alive_max_requests = int(config["keep-alive-max-requests"])
            self._debug = bool(config["debug"])
            self._file_manager = FileManager(
                os.path.join(os.getcwd(), config["root"]),
                os.path.join(os.getcwd(), config["home-page-path"]),
                os.path.join(os.getcwd(), config["media"]),
            )

            cash_size = int(config["server-cash-size"])
            self._server_cash_list = CashList(cash_size) if cash_size > 0 else None

            self._mutex = Lock()
            self._parser = RequestParser(self._file_manager)
            self._response_generator = ResponseGenerator(
                self._file_manager,
                int(config["keep-alive-max-requests"]),
                bool(config["browser-caching"]),
                self._server_cash_list,
                int(config["keep-alive-timeout"]),
            )

            if not os.path.exists("logs"):
                os.mkdir("logs")
            logging.basicConfig(
                filename=config["access-log"],
                filemode="w",
                level=logging.INFO,
                format="%(levelname)s: [%(asctime)s] %(message)s",
            )

        except KeyError as e:
            raise exc.ConfigFieldException(e) from None
        if self._debug:
            print("Server was initialized successfully", end="\n")

    def handle_client(self, client, address):
        keep_alive = self._keep_alive
        requests_count = 0
        ip = address[0]
        exit = False

        self._mutex.acquire()
        if ip not in self._active_connections:
            self._active_connections[ip] = [0, []]
        self._active_connections[ip][0] += 1
        self._active_connections[ip][1].append(time.time())
        client_connections = self._active_connections[ip]
        tmr = self._too_many_requests(client_connections[1])
        self._mutex.release()

        if client_connections[0] > self._client_connections_limit:
            exit = True

        if self._debug:
            print(f"Client {address[0]}:{address[1]} connected")
        while (
            not exit and keep_alive and requests_count < self._keep_alive_max_requests
        ):
            try:
                client.settimeout(self._keep_alive_timeout)
                data = client.recv(self._request_size)
                if not data:
                    break
                requests_count += 1
                data = data.split(b"\r\n\r\n", 1)
                request = data[0].decode("utf-8")

                request_info = self._parser.parse_request(request)
                request_info.too_many_requests = tmr
                request_info.client = address[0]
                request_info.requests_count = requests_count
                keep_alive = (
                    keep_alive
                    and bool(request_info.connection)
                    and request_info.method != "POST"
                )

                if request_info.method == "POST":
                    if request_info.page_name == "uploaded_image":
                        arr = bytearray(data[1])
                        additional = b""
                        if len(arr) < request_info.content_length:
                            try:
                                additional = client.recv(self._request_size)
                                while additional:
                                    body_part = client.recv(self._request_size)
                                    if not body_part:
                                        break
                                    additional += body_part
                            except socket.timeout:
                                pass
                        request_body = data[1] + additional
                    else:
                        request_body = data[1].decode("utf-8")
                    self._parser.parse_request_body(request_info, request_body)
                response, code = self._response_generator.generate_response(
                    request_info
                )
                self._mutex.acquire()
                logging.info(
                    f"{request_info.client} - {request_info.method} "
                    f"{request_info.url} {code} "
                    f"{request_info.user_agent}"
                )
                self._mutex.release()

                client.sendall(response)
            except Exception as e:
                if e.__class__ is not socket.timeout:
                    self._mutex.acquire()
                    logging.error("Server exception", exc_info=True)
                    self._mutex.release()
                break

        client.close()
        self._mutex.acquire()
        self._active_connections[ip][0] -= 1
        client_connections = self._active_connections[ip]
        self._mutex.release()
        if self._debug:
            print(f"Client {address[0]}:{address[1]} disconnected")

    def run(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self._ip_address, self._port))
        server_socket.listen(self._connections_limit)

        with ThreadPoolExecutor(max_workers=self._connections_limit) as executor:
            while True:
                client, address = server_socket.accept()

                if self._keep_alive:
                    self._set_keepalive(client)
                executor.submit(self.handle_client, client, address)

    def _set_keepalive(self, sock, after_idle_sec=1, interval_sec=3, max_fails=5):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, after_idle_sec)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval_sec)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, max_fails)

    def _too_many_requests(self, requests):
        while (
            len(requests) > 0
            and time.time() - requests[0] > self._too_many_requests_span
        ):
            requests.pop(0)
        res = len(requests) > self._too_many_requests_limit
        return res


if __name__ == "__main__":
    configuration = configparser.ConfigParser()
    configuration.read("config.ini")
    server = Server(configuration["SERVER"])
    server.run()

import configparser
import os
import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import models.exceptions as exc
from utils.file_manager import FileManager
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

            self._keep_alive = bool(config["keep-alive"])
            self._keep_alive_max_requests = int(config["keep-alive-max-requests"])
            self._debug = bool(config["debug"])
            self._file_manager = FileManager(
                os.path.join(os.getcwd(), config["root"]),
                os.path.join(os.getcwd(), config["home_page_path"]),
                os.path.join(os.getcwd(), config["media"]),
            )
            self._mutex = Lock()
            self._parser = RequestParser(self._file_manager)
            self._response_generator = ResponseGenerator(
                self._file_manager, bool(config["caching"])
            )

            logging.basicConfig(filename=config["access-log"], filemode="w", level=logging.INFO,
                                format="%(levelname)s: [%(asctime)s] %(message)s")

        except KeyError as e:
            raise exc.ConfigFieldException(e) from None
        if self._debug:
            print("Server was initialized successfully", end="\n")

    def handle_client(self, client, address):
        keep_alive = self._keep_alive
        requests_count = 0

        if self._debug:
            print(f"Client {address[0]}:{address[1]} connected")

        while keep_alive and requests_count < self._keep_alive_max_requests:
            try:
                # client.settimeout(2)
                data = client.recv(self._request_size)
                if not data:
                    break
                requests_count += 1
                request = data.decode("utf-8")

                request_info = self._parser.parse_request(request)
                request_info.client = address[0]
                request_info.requests_count = requests_count
                keep_alive = keep_alive and bool(request_info.connection)

                if request_info.method == "POST":
                    if request_info.page_name == "uploaded_image":
                        request_body = client.recv(request_info.content_length)
                        # request_body = client.recv(self._request_size)
                        # while request_body:
                        #     body_part = client.recv(self._request_size)
                        #     if not body_part:
                        #         break
                        #     request_body += body_part
                    else:
                        request_body = request[-request_info.content_length:]
                    self._parser.parse_request_body(
                        request_info, request_body
                    )
                response, code = self._response_generator.generate_response(
                    request_info
                )
                self._mutex.acquire()
                logging.info(f"{request_info.client} - {request_info.method} "
                             f"{request_info.url} {code} "
                             f"{request_info.user_agent}")
                self._mutex.release()

                client.sendall(response)
            except Exception as e:
                # if e.__class__ is socket.timeout:
                #     if self._debug:
                #         print(f"Connection with client {address[0]} timed out")
                # else:
                self._mutex.acquire()
                logging.error("Server exception", exc_info=True)
                self._mutex.release()
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
                self.set_keepalive_linux(client)
                executor.submit(self.handle_client, client, address)

    def set_keepalive_linux(self, sock, after_idle_sec=1, interval_sec=3, max_fails=5):
        """Настройка TCP keepalive на открытом сокете для Linux."""
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, after_idle_sec)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval_sec)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, max_fails)


if __name__ == "__main__":
    configuration = configparser.ConfigParser()
    configuration.read("config.ini")
    server = Server(configuration["SERVER"])
    server.run()

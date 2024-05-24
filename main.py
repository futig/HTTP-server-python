import configparser
import socket

from exceptions import *
from logger import Logger
from request_parser import parse_request, parse_request_body
from response_generator import generate_response
from file_indexer import FileIndexer


class Server:
    def __init__(self, configuration):
        try:
            self._root = configuration['root']
            self._request_size = int(configuration['request-size'])
            self._logger = Logger(configuration['access-log'])
            self._ip_address = configuration['ip-address']
            self._port = int(configuration['port'])
            self._connections_limit = int(configuration['connections_limit'])
            self._server = socket.create_server((self._ip_address, self._port))
            self._server.listen(self._connections_limit)
            self._file_indexer = FileIndexer(self._root, configuration['home_page_file_path'])
        except KeyError as e:
            raise ConfigFieldException(e) from None
        finally:
            print("Server was initialized successfully", end='\n')

    def run(self):
        while True:
            client, address = self._server.accept()
            request = client.recv(self._request_size).decode("utf-8")
            if not request:
                client.close()
                continue
            request_dict, request_body = parse_request(request)
            request_dict['client'] = address[0]
            user_info = None
            if request_dict["method"] == "POST":
                user_info = parse_request_body(request_body)
            response, code = generate_response(request_dict, user_info, self._file_indexer)
            self._logger.add_record(request_dict, code)
            client.send(response.encode("utf-8"))
            client.close()

    def stop_server(self):
        self._server.close()
        print("Server was closed successfully")

    def __del__(self):
        self.stop_server()


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    server = Server(config["SERVER"])
    server.run()

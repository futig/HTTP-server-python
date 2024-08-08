from pathlib import Path

class ResponseGenerator:
    def __init__(self, indexer, keep_alive_max_requests,
                 caching, keep_alive_timeout):
        self._indexer = indexer
        self._caching = caching
        self._keep_alive_timeout = keep_alive_timeout
        self._keep_alive_max_requests = keep_alive_max_requests

    def generate_response(self, request_info):
        response = []
        status_header, code = self._generate_status_header(
            request_info.method, request_info.url
        )
        response.append(status_header)
        response.append(self._generate_content_type_header())
        response.append(self._generate_caching_header(request_info.url))
        response.append(self._generate_connection_header(request_info))
        response.append("\n")
        response.append(self._generate_body(code, request_info))
        return "".join(response), code

    def _generate_connection_header(self, request_info):
        max_req = self._keep_alive_max_requests - request_info.requests_count
        return "Connection: close\n" if not request_info.connection \
            else (f"Connection: keep-alive\nKeep-Alive: "
                  f"timeout={self._keep_alive_timeout}, "
                  f"max={max_req}\n")

    def _generate_caching_header(self, url):
        cache_condition = (not self._caching or url in
                           {"/logger_name", "/download"})
        cache = "no-store" if cache_condition else "public, max-age=86400"
        return "Cache-Control: " + cache + "\n"

    def _generate_content_type_header(sefl):
        # if file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
        #     return 'image/jpeg'
        # elif file_path.endswith('.png'):
        #     return 'image/png'
        # elif file_path.endswith('.gif'):
        #     return 'image/gif'
        # else:
        #     return 'application/octet-stream'
        return "Content-Type: text/html\n"


    def _generate_status_header(self, method, url):
        if method not in {"POST", "GET"}:
            return "HTTP/1.1 405 Method not allowed\n", 405
        if not self._indexer.contains(url):
            return "HTTP/1.1 404 Not found\n", 404
        return "HTTP/1.1 200 OK\n", 200

    def _generate_body(self, code, request_info):
        if code == 404:
            return "<h1>404</h1><p>Not found</p>\n"
        if code == 405:
            return "<h1>405</h1><p>Method not allowed</p>\n"
        if code == 200:
            page_code = self._indexer.get_page_code(request_info.url)
            page = Path(request_info.url).name
            if request_info.method == "POST" and page == "logger_name":
                return page_code.format(request_info.login_body)
            return page_code

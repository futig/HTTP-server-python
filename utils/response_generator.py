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
            request_info["method"], request_info["url"]
        )
        response.append(status_header)
        response.append(self._generate_content_type_header())
        # if self._caching and request_info["url"] not in {"/logger_name", "/download"}:
        #     response.append(self._generate_caching_header(code))
        response.append(self._generate_connection_header(request_info))
        response.append("\n")
        response.append(self._generate_body(code, request_info["url"]))
        return "".join(response), code

    def _generate_connection_header(self, request_info):
        max_req = self._keep_alive_max_requests - request_info["requests-count"]
        return "Connection: close\n" if not request_info["connection"] \
            else (f"Connection: keep-alive\nKeep-Alive: "
                  f"timeout={self._keep_alive_timeout}, "
                  f"max={max_req}\n")

    def _generate_caching_header(self, code):
        return ""

    def _generate_content_type_header(self):
        return "Content-Type: text/html\n"

    def _generate_status_header(self, method, url):
        if method not in {"POST", "GET"}:
            return "HTTP/1.1 405 Method not allowed\n", 405
        if not self._indexer.contains(url):
            return "HTTP/1.1 404 Not found\n", 404
        return "HTTP/1.1 200 OK\n", 200

    def _generate_body(self, code, url):
        if code == 404:
            return "<h1>404</h1><p>Not found</p>\n"
        if code == 405:
            return "<h1>405</h1><p>Method not allowed</p>\n"
        if code == 200:
            page_code = self._indexer.get_page_code(url)
            # if method == "POST":
            #     content = self._generate_content(data)
            #     return page_code.format(content)
            return page_code

    def _generate_content(self, data):
        return f"{data.name} {data.surname}"

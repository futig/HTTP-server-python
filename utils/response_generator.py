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
        response.append(self._generate_content_type_header(
            request_info.url, code
        ))
        response.append(self._generate_caching_header(request_info.url))
        response.append(self._generate_connection_header(request_info))
        response.append("\n")
        content = self._generate_body(code, request_info)
        response_encoded = "".join(response).encode("utf-8")
        return response_encoded + content, code

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

    def _generate_content_type_header(sefl, url, code):
        suffix = Path(url).suffix
        content_type = ""
        if not suffix or code != 200:
            content_type = "text/html"
        if suffix in {'.jpg', '.jpeg'}:
            content_type = 'image/jpeg'
        elif suffix == '.png':
            content_type = 'image/png'
        elif suffix == '.gif':
            content_type = 'image/gif'
        return f"Content-Type: {content_type}\n"

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
            suffix = Path(request_info.url).suffix
            if request_info.method == "POST" and page == "logger_name":
                page_code = page_code.format(request_info.login_body)
            if page == "download":
                page_code = page_code.format(self._generate_media_body())
            return page_code if suffix else page_code.encode("utf-8")
        
    def _generate_media_body(self):
        result = []
        for url in self._indexer.get_media_links():
            result.append(f'<a href="{url}">{Path(url).name}</a>\n')
        return "".join(result)

from pathlib import Path


class ResponseGenerator:
    def __init__(self, indexer, keep_alive_max_requests,
                 browser_caching, cash_list, keep_alive_timeout):
        self._indexer = indexer
        self._browser_caching = browser_caching
        self._server_cash_list = cash_list
        self._keep_alive_timeout = keep_alive_timeout
        self._keep_alive_max_requests = keep_alive_max_requests

    def generate_response(self, request_info):
        url = request_info.url
        if (self._server_cash_list and 
            self._server_cash_list.contains(url)):
            return self._server_cash_list.get(url)
        
        response = []
        status_header, code = self._generate_status_header(
            request_info.method, url, request_info.too_many_requests
        )
        response.append(status_header)
        response.append(self._generate_content_type_header(
            url, code
        ))
        response.append(self._generate_caching_header(url))
        response.append(self._generate_connection_header(request_info))
        content = self._generate_body(code, request_info)
        response.append(self._generate_content_length_header(content))
        response.append("\n")
        response_encoded = "".join(response).encode("utf-8")
        result = response_encoded + content
        if (self._server_cash_list and url not in {"/logger_name", "/download"}):
            self._server_cash_list.put(url, result, code)
        return result, code

    def _generate_connection_header(self, request_info):
        max_req = self._keep_alive_max_requests - request_info.requests_count
        if not request_info.connection or request_info.method == "POST":
            return "Connection: close\n"
        else:
            return (f"Connection: keep-alive\nKeep-Alive: "
                    f"timeout={self._keep_alive_timeout}, "
                    f"max={max_req}\n")

    def _generate_content_length_header(self, content):
        return f"Content-Length: {len(content)}\n"

    def _generate_caching_header(self, url):
        cache_condition = (not self._browser_caching or url in
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

    def _generate_status_header(self, method, url, tmr):
        if tmr:
            return "HTTP/1.1 429 Too many requests\n", 429
        if method not in {"POST", "GET"}:
            return "HTTP/1.1 405 Method not allowed\n", 405
        if not self._indexer.contains(url):
            return "HTTP/1.1 404 Not found\n", 404
        return "HTTP/1.1 200 OK\n", 200

    def _generate_body(self, code, request_info):
        if code == 404:
            return "<h1>404</h1><p>Not found</p>\n".encode("utf-8")
        if code == 405:
            return "<h1>405</h1><p>Method not allowed</p>\n".encode("utf-8")
        if code == 429:
            return "<h1>429</h1><p>Too many requests</p>\n".encode("utf-8")
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

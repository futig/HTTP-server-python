def _generate_headers(method, url, indexer):
    if method not in ["POST", "GET"]:
        return "HTTP/1.1 405 Method not allowed\n\n", 405
    if not url == "/" and not indexer.contains(url):
        return "HTTP/1.1 404 Not found\n\n", 404
    return "HTTP/1.1 200 OK\n\n", 200


def _generate_body(code, url, method, data, indexer):
    if code == 404:
        return "<h1>404</h1><p>Not found</p>"
    if code == 405:
        return "<h1>405</h1><p>Method not allowed</p>"
    if code == 200:
        page_code = indexer.get_page_code(url)
        if method == "POST":
            content = _generate_content(data)
            return page_code.format(content)
        return page_code


def generate_response(request_info, post_data, indexer):
    method, url = request_info["method"], request_info["url"]
    headers, code = _generate_headers(method, url, indexer)
    body = _generate_body(code, url, method, post_data, indexer)
    return headers + body, code


def _generate_content(data):
    return f"{data.name} {data.surname}"

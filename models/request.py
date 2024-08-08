class Request:
    def __init__(self, method, url, http_version, page_name, 
                 connection=None, content_length=None,
                 user_agent=None, client=None,
                 requests_count=None, request_body=None):
        self.method = method
        self.url = url
        self.page_name = page_name
        self.http_version = http_version
        self.connection = connection
        self.content_length = content_length
        self.user_agent = user_agent
        self.client = client
        self.requests_count = requests_count
        self.request_body = request_body


from queue import Queue


class Page:
    def __init__(self, url, page_code, response_code):
        self.url = url
        self.page_code = page_code
        self.response_code = response_code
        self.r = True


class CashList:
    def __init__(self, maxsize):
        self.maxsize = maxsize
        self.queue = Queue(maxsize)
        self.pages = {}

    def get(self, url):
        page = self.pages[url]
        page.r = True
        return page.page_code, page.response_code

    def contains(self, url):
        return url in self.pages

    def put(self, url, page_code, response_code):
        while self.queue.full():
            page = self.queue.get()
            if page.r:
                page.r = False
                self.queue.put(page)
            else:
                self.pages.pop(page.url)
        page = Page(url, page_code, response_code)
        self.pages[url] = page
        self.queue.put(page)

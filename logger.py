from datetime import datetime
from queue import Queue

FORMAT = '{client_address} -- [{asctime}] {method} {path} {response_code} {user_agent}\n'
DATE_FORMAT = '%d/%m/%Y:%H:%M:%S'


class Logger:
    def __init__(self, path):
        self.file_path = path

    def add_record(self, request, response_code):
        date_string = datetime.strftime(datetime.now(), DATE_FORMAT)
        data_format = FORMAT.format(client_address=request['client'],
                                    method=request['method'],
                                    path=request['url'],
                                    response_code=response_code,
                                    user_agent=request['User-Agent'],
                                    asctime=date_string)
        with open(self.file_path, 'a') as f:
            f.write(data_format)
            f.flush()

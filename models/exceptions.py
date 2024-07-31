class ConfigFieldException(Exception):
    def __init__(self, exception):
        self.message = f"There is no such field in configuration: {exception}"

    def __str__(self):
        return self.message


class WrongPathException(Exception):
    def __init__(self, path):
        self.message = f"There is no file '{path}'"

    def __str__(self):
        return self.message


class WrongClientException(Exception):
    def __init__(self, client_ip):
        self.message = f"There is no client '{client_ip}'"

    def __str__(self):
        return self.message


class BadRequestException(Exception):
    def __init__(self, request):
        self.message = f"Could not parse request:\n{request}"

    def __str__(self):
        return self.message

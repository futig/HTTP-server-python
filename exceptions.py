class ConfigFieldException(Exception):
    def __init__(self, exception):
        self.message = f"There is not field '{exception}' in configuration"

    def __str__(self):
        return self.message


class WrongPathException(Exception):
    def __init__(self, path):
        self.message = f"There is no file '{path}'"

    def __str__(self):
        return self.message



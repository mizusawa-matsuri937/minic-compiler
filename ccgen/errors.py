"""Rule errors retain the location in the user's input file."""


class RuleError(ValueError):
    def __init__(self, path, line, message):
        self.path, self.line, self.message = str(path), line, message
        super().__init__(f"{path}:{line}: {message}")

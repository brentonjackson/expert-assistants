class AIHandler:
    """
    Interface for all AI handlers.
    """
    def setup(self):
        raise NotImplementedError("Subclasses should implement this method")

    def get_response(self, context: str, input: str, init=False):
        raise NotImplementedError("Subclasses should implement this method")



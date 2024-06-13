

class AbstractValidationModule:
    """
    module xlsx validation
    """

    def __init__(self, package, resourceName):
        self._package = package
        self._resourceName = resourceName
        assert self._package.has_resource(resourceName)
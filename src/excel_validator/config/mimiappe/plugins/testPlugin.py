from frictionless import Plugin, Check, Resource, errors

class testCheck(Check):
    type = "testcheck"
    Errors = [errors.CellError]
    def validate_row(self, row):
        if not row is None:
            pass
        yield from []

class testPlugin(Plugin):

    def select_check_class(self, type = None):
        if type==testCheck.type:
            return testCheck

    def select_resource_class(self, type = None, *, datatype = None):
        pass

    def select_package_class(self, type = None):
        pass

    def detect_resource(self, resource: Resource):
        pass
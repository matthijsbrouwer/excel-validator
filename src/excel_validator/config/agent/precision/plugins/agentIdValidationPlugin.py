from frictionless import Plugin, Check, Resource, errors
import attrs, requests

@attrs.define(kw_only=True, repr=False)
class agentIdValidationCheck(Check):

    type = "agent-id-validation"
    Errors = [errors.RowError]
    required = {}

    def __init__(self, *args, **kwargs):
        self.field = kwargs.get("fields",None)
        self.url = kwargs.get("url",None)
        self.token = kwargs.get("token",None)

    def validate_row(self, row):
        if self.field in row and not row[self.field] is None:
            agentId = row[self.field]
            if not self.url is None or self.token is None:
                pass
                # TODO: implement code to perform external validation
                # r = requests.get(self.url, timeout=60, params = {"token": self.token, "agent_id": agentId})
                # if r.ok:
                #     data = r.json()
                #     errorText = "..."
                #     yield errors.RowError(note="invalid '%s': '%s'" % (self.field,errorText),
                #     row_number=row.row_number, cells=row.cells)
        yield from []

    metadata_profile_patch = {
        "required": ["field","url","token"],
        "properties": {
            "field": {"type": "string"},
            "url": {"type": "string"},
            "token": {"type": "string"},
        },
    }

class agentIdValidationPlugin(Plugin):

    def select_check_class(self, type = None):
        if type==agentIdValidationCheck.type:
            return agentIdValidationCheck


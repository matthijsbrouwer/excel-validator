from frictionless import Plugin, Check, Resource, errors
import attrs

@attrs.define(kw_only=True, repr=False)
class agentRequiredRowValuesCheck(Check):

    type = "agent-required-row-values"
    Errors = [errors.RowError]
    required = {}

    def __init__(self, *args, **kwargs):
        self.fields = kwargs.get("fields",[])
        self.required = kwargs.get("required","all")

    def validate_row(self, row):
        fieldsWithValues = []
        for field in self.fields:
            if field in row and not row[field] is None:
                fieldsWithValues.append(field)
        if self.required=="all":
            missing = set(self.fields).difference(fieldsWithValues)
            if len(missing)>0:
                yield errors.RowError(
                    note="missing %s: '%s'" % ("value" if len(missing)==1 else "values", "', '".join(missing)),
                    row_number=row.row_number, cells=row.cells)
        elif self.required=="one":
            if len(fieldsWithValues)==0:
                yield errors.RowError(
                    note="at least one value required for '%s'" % ("', '".join(self.fields),),
                    row_number=row.row_number, cells=row.cells)
        yield from []

    metadata_profile_patch = {
        "required": ["fields","required"],
        "properties": {
            "fields": {"type": "array"},
            "required": {"type": "string"},
        },
    }

class agentRequiredRowValuesPlugin(Plugin):

    def select_check_class(self, type = None):
        if type==agentRequiredRowValuesCheck.type:
            return agentRequiredRowValuesCheck


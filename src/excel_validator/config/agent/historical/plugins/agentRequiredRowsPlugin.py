from frictionless import Plugin, Check, Resource, errors
import attrs

@attrs.define(kw_only=True, repr=False)
class agentRequiredRowsCheck(Check):

    type = "agent-required-rows"
    Errors = [errors.TableError]
    required = {}

    def __init__(self, *args, **kwargs):
        self.required = kwargs.get("required",[])

    def _check_row_for_required_item(self,key:str,item:dict,row):
        if row:
            for fieldName in item:
                if fieldName in row and row[fieldName]==item[fieldName]:
                    self._found.add(key)
    
    def validate_start(self):
        self._found = set()
        yield from []
    
    def validate_row(self, row):
        for key in self.required:
            if isinstance(self.required[key],list):
                for item in self.required[key]:
                    self._check_row_for_required_item(key,item,row)
            elif isinstance(self.required[key],dict):
                self._check_row_for_required_item(key,self.required[key],row)
        yield from []

    def validate_end(self):
        missing = set(self.required.keys()).difference(self._found)
        if len(missing)>0:
            yield errors.TableError(
                note="missing row %s: '%s'" % ("entry" if len(missing)==1 else "entries", "', '".join(list(missing))))
        yield from []

    metadata_profile_patch = {
        "required": ["required"],
        "properties": {
            "required": {"type": "object"},
        },
    }

class agentRequiredRowsPlugin(Plugin):

    def select_check_class(self, type = None):
        if type==agentRequiredRowsCheck.type:
            return agentRequiredRowsCheck


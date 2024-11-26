# pylint: disable=line-too-long,invalid-name,consider-using-f-string
"""Additional functions."""

import numpy as np
from numbers import Number

def checkDescriptorValueCondition(key,entry,dynamicResourcesEntry,logger):
    """
    check value condition for descriptor
    """
    try:
        if key in entry:
            if isinstance(entry[key],dict) and "condition" in entry[key]:
                for condition in entry[key]["condition"]:
                    value = dynamicResourcesEntry.get(condition["dynamicResource"],{}).get(condition["field"],None)
                    if value is None:
                        return False
                    elif isinstance(value,list):
                        if not any(valueEntry==condition["value"] for valueEntry in value):
                            return False
                    elif not value==condition["value"]:
                        return False
            return True
    except Exception as ex:
        logger.error("%s : %s, line %s" % (type(ex).__name__, __file__, ex.__traceback__.tb_lineno))
    return False

def setDescriptorValueDynamicString(key,descriptor,entry,dynamicResourcesEntry,mappings,linkedResources,logger):
    """
    set descriptor key/value for string
    """
    try:
        if checkDescriptorValueCondition(key,entry,dynamicResourcesEntry,logger):
            value = None
            if isinstance(entry[key],str):
                value = entry[key]
            elif "dynamicResource" in entry[key]:
                value = dynamicResourcesEntry.get(entry[key]["dynamicResource"],{}).get(entry[key]["field"],None)
            elif "linkedResource" in entry[key]:
                if entry[key]["linkedResource"] in linkedResources:
                    if linkedResources[entry[key]["linkedResource"]].shape[0]>0:
                        valueList = list(linkedResources[entry[key]["linkedResource"]][entry[key]["field"]].values)
                        for item in valueList:
                            if not item is None:
                                value = str(item)
                                break
            #mapping
            if not value is None:
                mappingValue = None
                if isinstance(entry[key],dict) and "mapping" in entry[key]:
                    if entry[key]["mapping"] in mappings:
                        if value in mappings[entry[key]["mapping"]]["map"]:
                            mappingValue = str(mappings[entry[key]["mapping"]]["map"][value])
                        elif "default" in mappings[entry[key]["mapping"]]:
                            mappingValue = str(mappings[entry[key]["mapping"]]["default"])
                else:
                    mappingValue = str(value)
                #prefix/postfix
                if not mappingValue is None:
                    prefix = entry[key].get("prefix","") if isinstance(entry[key],dict) else ""
                    postfix = entry[key].get("postfix","") if isinstance(entry[key],dict) else ""
                    descriptor[key] = "%s%s%s" % (prefix,mappingValue,postfix)
    except Exception as ex:
        logger.error("%s : %s, line %s" % (type(ex).__name__, __file__, ex.__traceback__.tb_lineno))
    return descriptor

def setDescriptorValueDynamicInteger(key,descriptor,entry,dynamicResourcesEntry,mappings,linkedResources,logger):
    """
    set descriptor key/value for integer
    """
    try:
        if checkDescriptorValueCondition(key,entry,dynamicResourcesEntry,logger):
            value = None
            if isinstance(entry[key],int):
                value = entry[key]
            elif "dynamicResource" in entry[key]:
                value = dynamicResourcesEntry.get(entry[key]["dynamicResource"],{}).get(entry[key]["field"],None)
            elif "linkedResource" in entry[key]:
                if entry[key]["linkedResource"] in linkedResources:
                    if linkedResources[entry[key]["linkedResource"]].shape[0]>0:
                        valueList = list(linkedResources[entry[key]["linkedResource"]][entry[key]["field"]].values)
                        for item in valueList:
                            if not item is None:
                                value = int(item)
                                break
            if not value is None:
                if isinstance(entry[key],dict) and "mapping" in entry[key]:
                    if entry[key]["mapping"] in mappings:
                        if value in mappings[entry[key]["mapping"]]["map"]:
                            descriptor[key] = int(mappings[entry[key]["mapping"]]["map"][value])
                        elif "default" in mappings[entry[key]["mapping"]]:
                            descriptor[key] = int(mappings[entry[key]["mapping"]]["default"])
                else:
                    descriptor[key] = int(value)
    except Exception as ex:
        logger.error("%s : %s, line %s" % (type(ex).__name__, __file__, ex.__traceback__.tb_lineno))
    return descriptor

def setDescriptorValueDynamicNumber(key,descriptor,entry,dynamicResourcesEntry,mappings,linkedResources,logger):
    """
    set descriptor key/value for integer
    """
    try:
        if checkDescriptorValueCondition(key,entry,dynamicResourcesEntry,logger):
            value = None
            if isinstance(entry[key],Number):
                value = entry[key]
            elif "dynamicResource" in entry[key]:
                value = dynamicResourcesEntry.get(entry[key]["dynamicResource"],{}).get(entry[key]["field"],None)
            elif "linkedResource" in entry[key]:
                if entry[key]["linkedResource"] in linkedResources:
                    if linkedResources[entry[key]["linkedResource"]].shape[0]>0:
                        valueList = list(linkedResources[entry[key]["linkedResource"]][entry[key]["field"]].values)
                        for item in valueList:
                            if not item is None:
                                value = item
                                break
            if not value is None:
                if isinstance(entry[key],dict) and "mapping" in entry[key]:
                    if entry[key]["mapping"] in mappings:
                        if value in mappings[entry[key]["mapping"]]["map"]:
                            descriptor[key] = mappings[entry[key]["mapping"]]["map"][value]
                        elif "default" in mappings[entry[key]["mapping"]]:
                            descriptor[key] = mappings[entry[key]["mapping"]]["default"]
                else:
                    descriptor[key] = value
    except Exception as ex:
        logger.error("%s : %s, line %s" % (type(ex).__name__, __file__, ex.__traceback__.tb_lineno))
    return descriptor

def setDescriptorValueDynamicBoolean(key,descriptor,entry,dynamicResourcesEntry,mappings,linkedResources,logger):
    """
    set descriptor key/value for boolean
    """
    try:
        if checkDescriptorValueCondition(key,entry,dynamicResourcesEntry,logger):
            value = None
            if isinstance(entry[key],bool):
                value = entry[key]
            elif "dynamicResource" in entry[key]:
                value = dynamicResourcesEntry.get(entry[key]["dynamicResource"],{}).get(entry[key]["field"],None)
            elif "linkedResource" in entry[key]:
                if entry[key]["linkedResource"] in linkedResources:
                    if linkedResources[entry[key]["linkedResource"]].shape[0]>0:
                        valueList = list(linkedResources[entry[key]["linkedResource"]][entry[key]["field"]].values)
                        for item in valueList:
                            if not item is None:
                                value = bool(item)
                                break
            if not value is None:
                if isinstance(entry[key],dict) and "mapping" in entry[key]:
                    if entry[key]["mapping"] in mappings:
                        if value in mappings[entry[key]["mapping"]]["map"]:
                            descriptor[key] = bool(mappings[entry[key]["mapping"]]["map"][value])
                        elif "default" in mappings[entry[key]["mapping"]]:
                            descriptor[key] = bool(mappings[entry[key]["mapping"]]["default"])
                else:
                    descriptor[key] = bool(value)
    except Exception as ex:
        logger.error("%s : %s, line %s" % (type(ex).__name__, __file__, ex.__traceback__.tb_lineno))
    return descriptor

def setDescriptorValueDynamicList(key,descriptor,entry,dynamicResourcesEntry,mappings,linkedResources,logger):
    """
    set descriptor key/value for list
    """
    try:
        if checkDescriptorValueCondition(key,entry,dynamicResourcesEntry,logger):
            value = None
            if isinstance(entry[key],list):
                value = entry[key].tolist()
            elif "dynamicResource" in entry[key]:
                value = None
            elif "linkedResource" in entry[key]:
                if entry[key]["linkedResource"] in linkedResources:
                    if linkedResources[entry[key]["linkedResource"]].shape[0]>0:
                        value = list(linkedResources[entry[key]["linkedResource"]][entry[key]["field"]].values.tolist())
            if not value is None:
                if isinstance(entry[key],dict) and "mapping" in entry[key]:
                    if entry[key]["mapping"] in mappings:
                        mapping = mappings[entry[key]["mapping"]]
                        descriptor[key] = []
                        for item in value:
                            if item in mapping["map"]:
                                descriptor[key].append(mapping["map"][item])
                            elif "default" in mapping:
                                descriptor[key].append(mapping["default"])
                else:
                    descriptor[key] = value
    except Exception as ex:
        logger.error("%s : %s, line %s" % (type(ex).__name__, __file__, ex.__traceback__.tb_lineno))
    return descriptor

def excelCoordinates(error):
    """
    compute excel coordinates for frictionless error
    """
    try:
        row = error.get_defined(name="row_number",default=None)
        col = error.get_defined(name="field_number",default=None)
        LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if not col is None and not np.isnan(col):
            result = []
            while col:
                col, rem = divmod(col-1, 26)
                result[:0] = LETTERS[int(rem)]
            if not row is None and not np.isnan(row):
                text = "{}{}".format("".join(result),int(row))
                return text
            text = "column {}".format("".join(result))
            return text
        if not row is None and not np.isnan(row):
            text = "row {}".format(int(row))
            return text
        return None
    except:
        return None

def excelTransformCoordinates(error, rowCellId=None):
    """
    compute excel coordinates for frictionless error
    """
    try:
        row = error.get_defined(name="row_number",default=None)
        col = error.get_defined(name="field_number",default=None)
        LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if not col is None and not np.isnan(col):
            result = []
            while col:
                col, rem = divmod(col-1, 26)
                result[:0] = LETTERS[int(rem)]
            if not row is None and not np.isnan(row):
                text = "{}{}".format("".join(result),int(row))
                return text
            text = "column {}".format("".join(result))
            return text
        if not row is None and not np.isnan(row):
            text = "row {}".format(int(row))
            return text
        return None
    except:
        return None

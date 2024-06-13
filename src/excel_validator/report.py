# pylint: disable=line-too-long,invalid-name,consider-using-f-string
"""Module providing report classes."""

import logging
import textwrap
from frictionless import Report
from .functions import excelCoordinates

class ValidationReport:
    """
    report xlsx validation
    """
    TYPE_GENERAL = "General"
    TYPE_RESOURCE = "Resource"
    TYPE_PACKAGE = "Package"

    def __init__(self, logger:logging.Logger):
        self._logger = logger
        self._reportNames = []
        self._reports = {}

    def addReport(self, name:str, title:str, forceReport:bool, reportType:str):
        """
        Add report
        """
        if name in self._reportNames or name in self._reports:
            if forceReport:
                if name in self._reportNames:
                    self._reportNames.remove(name)
                if name in self._reports:
                    del self._reports[name]
            else:
                raise KeyError
        self._reportNames.append(name)
        self._reports[name] = ValidationReportEntry(name,title,reportType)

    def addReportError(self, name:str, title:str, description:str, data:str=None):
        """
        Add error to report
        """
        if not (name in self._reportNames or name in self._reports):
            raise KeyError
        self._reports[name].addError(title,description,data)
        self._logger.info(f"[{name}] - {title}: {description}")

    def addReportWarning(self, name:str, title:str, description:str):
        """
        Add warning to report
        """
        if not (name in self._reportNames or name in self._reports):
            raise KeyError
        self._reports[name].addWarning(title,description)
        self._logger.info(f"[{name}] - {title}: {description}")

    def addReportDebug(self, name:str, description:str):
        """
        Add debug to report
        """
        if not (name in self._reportNames or name in self._reports):
            raise KeyError
        self._logger.info(f"[{name}] - {description}")

    def addReportInfo(self, name:str, description:str):
        """
        Add info to report
        """
        if not (name in self._reportNames or name in self._reports):
            raise KeyError
        self._reports[name].addInfo(description)
        self._logger.info(f"[{name}] - {description}")

    def setFrictionless(self, name:str, data):
        """
        Set frictionless data
        """
        if not (name in self._reportNames or name in self._reports):
            raise KeyError
        assert isinstance(data, Report)
        self._reports[name].setFrictionless(data)

    def createReportObjects(self):
        """
        Set frictionless data
        """
        return []
        
    def createTextReport(self, textWidth=100, examples=3, markdown=False, warnings=True):
        """
        Create text version report
        """
        #create error text
        reportErrorText = ""
        errorTypes = set()
        #add error text except package
        for reportName in self.reports:
            if not self._reports[reportName].reportType == ValidationReport.TYPE_PACKAGE:
                reportErrorText = reportErrorText + self._reports[reportName].createErrorTextReport(textWidth,examples,markdown,errorTypes)
                errorTypes.update(self._reports[reportName].getErrorTypes())
        #add error text package
        for reportName in self.reports:
            if self._reports[reportName].reportType == ValidationReport.TYPE_PACKAGE:
                reportErrorText = reportErrorText + self._reports[reportName].createErrorTextReport(textWidth,examples,markdown,errorTypes)
        #create warning text
        reportWarningText = ""
        if warnings:
            for reportName in self.reports:
                reportWarningText = reportWarningText + self._reports[reportName].createWarningTextReport(textWidth,markdown)
        #create text
        reportText = reportErrorText
        if len(reportWarningText)>0:
            if markdown:
                reportText = reportText + "**Warnings**:\n"
            else:
                reportText = reportText + "Warnings:\n"
            reportText = reportText + reportWarningText
        return reportText

    @property
    def valid(self):
        """
        Valid
        """
        for report in self._reportNames:
            if report in self._reports:
                #check report
                if not self._reports[report].valid:
                    return False
        return True

    @property
    def reports(self):
        """
        Report names
        """
        return self._reportNames

    def __getitem__(self, key):
        if key not in self._reports:
            raise KeyError
        return self._reports[key]

class ValidationReportEntry:
    """
    report entry xlsx validation
    """

    def __init__(self, name:str, title:str, reportType:str):
        self._name = name
        self._title = title
        self._reportType = reportType
        self._valid = True
        self._errors = []
        self._warnings = []
        self._info = []
        self._frictionless = None
        assert reportType in [ValidationReport.TYPE_RESOURCE,
                              ValidationReport.TYPE_PACKAGE,
                              ValidationReport.TYPE_GENERAL]

    def _escapeMarkdown(text:str):
        escapedText = text.replace("\\","\\\\")
        escapeCharacters = ["#","*","<",">","(",")","[","]"]
        for x in escapeCharacters:
            escapedText = escapedText.replace(x,"\\%s"%x)
        return escapedText

    def addError(self, title:str, description:str, data:str=None):
        """
        Add error
        """
        self._valid = False
        self._errors.append((title,description,data))

    def addWarning(self, title:str, description:str):
        """
        Add warning
        """
        self._warnings.append((title,description))

    def addInfo(self, description:str):
        """
        Add info
        """
        self._info.append(description)

    def setFrictionless(self, data):
        """
        Set frictionless
        """
        assert isinstance(data, Report)
        self._valid &= data.valid
        self._frictionless = data

    @property
    def valid(self):
        """
        Valid
        """
        return self._valid

    @property
    def title(self):
        """
        Title
        """
        return self._title

    @property
    def reportType(self):
        """
        Report type
        """
        return self._reportType

    @property
    def warnings(self):
        """
        Warnings
        """
        return self._warnings

    @property
    def errors(self):
        """
        Errors
        """
        return self._errors

    @property
    def frictionless(self):
        """
        Frictionless report
        """
        return self._frictionless

    def getErrorTypes(self):
        """
        Frictionless error types
        """
        errorTypes = set()
        if self._frictionless and not self._frictionless.valid:
            for task in self._frictionless.tasks:
                for error in task.errors:
                    errorTypes.add((task.name, error.type))
        return errorTypes

    def createFrictionlessTextReport(self, textWidth=100, examples=3, markdown=False, ignoreErrortypes=None):
        """
        Create text version report frictionless
        """
        #create text
        reportText = ""
        if self._frictionless and not self._frictionless.valid:
            errors = {}
            for task in self._frictionless.tasks:
                for error in task.errors:
                    key = (task.name, error.type)
                    if ignoreErrortypes and key in ignoreErrortypes:
                        continue
                    if key not in errors:
                        errors[key] = []
                    errors[key].append(error)
            if len(errors)>0:
                for errorKey in errors:
                    if self._reportType == ValidationReport.TYPE_RESOURCE:
                        detailText = ""
                    else:
                        detailText = " for '{}'".format(errorKey[0])
                    if markdown:
                        reportText = reportText + "  * **{}**: {}x{}<br/>".format(
                            ValidationReportEntry._escapeMarkdown(errors[errorKey][0].get_defined(name="title",default=errorKey[1])),
                            len(errors[errorKey]),ValidationReportEntry._escapeMarkdown(detailText))
                    else:
                        errorText1 = "{}x '{}' {}".format(len(errors[errorKey]),
                                          errors[errorKey][0].get_defined(name="title",default=errorKey[1]),detailText)
                        reportText = reportText + textwrap.fill(errorText1,textWidth-6,
                                                            initial_indent="  - ",subsequent_indent="    ")+"\n"
                    errorText2 = errors[errorKey][0].get_defined(name="description",default="")
                    if markdown:
                        reportText = reportText + "{}\n".format(ValidationReportEntry._escapeMarkdown(errorText2))
                    else:
                        reportText = reportText + textwrap.fill(errorText2,textWidth-6,
                                                            initial_indent="    ",subsequent_indent="    ")+"\n"
                    for entryId,entry in enumerate(errors[errorKey]):
                        if entryId>=examples:
                            if markdown:
                                reportText = reportText + "    * ...\n"
                            else:
                                reportText = reportText + "    - ...\n"
                            break
                        location = excelCoordinates(entry)
                        fieldName = entry.get_defined(name="field_name",default=None)
                        cell = entry.get_defined(name="cell",default=None)
                        note = entry.get_defined(name="note",default=None)
                        message = entry.get_defined(name="message",default=None)
                        if location:
                            if markdown:
                                errorText = "**{}**".format(ValidationReportEntry._escapeMarkdown(location))
                            else:
                                errorText = "{}".format(location)
                            if fieldName:
                                if cell:
                                    errorText = "{} ({} '{}'): ".format(errorText,
                                                                        ValidationReportEntry._escapeMarkdown(fieldName),
                                                                        ValidationReportEntry._escapeMarkdown(cell))
                                else:
                                    if markdown:
                                        errorText = "{} ({}): ".format(errorText,ValidationReportEntry._escapeMarkdown(fieldName))
                                    else:
                                        errorText = "{} ({}): ".format(errorText,fieldName)
                            else:
                                errorText = "{}: ".format(errorText)
                        else:
                            errorText = ""
                        if note:
                            if markdown:
                                errorText = errorText + "*{}*".format(ValidationReportEntry._escapeMarkdown(note))
                            else:
                                errorText = errorText + "{}".format(note)
                        else:
                            if markdown:
                                errorText = errorText + "*{}*".format(ValidationReportEntry._escapeMarkdown(message))
                            else:
                                errorText = errorText + "{}".format(message)
                        if markdown:
                            reportText = reportText + "    * {}\n".format(errorText)
                        else:
                            reportText = reportText + textwrap.fill(errorText,textWidth-8,
                                                            initial_indent="    - ",subsequent_indent="      ")+"\n"

        return reportText

    def createErrorTextReport(self, textWidth=100, examples=3, markdown=False, ignoreErrortypes=None):
        """
        Create error text report
        """
        #create text
        reportText = ""
        if not self._valid:
            errorTypes = self.getErrorTypes()
            if ignoreErrortypes:
                newErrorTypes = errorTypes.difference(ignoreErrortypes)
            else:
                newErrorTypes = errorTypes
            if len(self._errors)>0 or (self._frictionless and (not self._frictionless.valid) and len(newErrorTypes)>0):
                if self._reportType == ValidationReport.TYPE_RESOURCE:
                    if markdown:
                        reportText = reportText + "**Problem with sheet '{}'**\n".format(ValidationReportEntry._escapeMarkdown(self._title))
                    else:
                        reportText = reportText + "Problem with sheet '{}'\n".format(self._title)
                else:
                    if markdown:
                        reportText = reportText + "**Problem with {}**\n".format(ValidationReportEntry._escapeMarkdown(self._title))
                    else:
                        reportText = reportText + "Problem with {}\n".format(self._title)
                for error in self._errors:
                    if markdown:
                        reportText = reportText + textwrap.fill("**{}**: {}".format(
                            ValidationReportEntry._escapeMarkdown(error[0]),
                            ValidationReportEntry._escapeMarkdown(error[1])),
                            textWidth-4,
                            initial_indent="* ",subsequent_indent="  ") + "\n"
                    else:
                        reportText = reportText + textwrap.fill("{}: {}".format(error[0],error[1]),textWidth-4,
                            initial_indent="- ",subsequent_indent="  ") + "\n"
                if self._frictionless and (not self._frictionless.valid) and len(newErrorTypes)>0:
                    if markdown:
                        reportText = reportText + "* Frictionless validation failed\n"
                    else:
                        reportText = reportText + "- Frictionless validation failed\n"
                    reportText = reportText + self.createFrictionlessTextReport(textWidth,examples,markdown,ignoreErrortypes)
                if markdown:
                    reportText = reportText + "\n"
        return reportText

    def createWarningTextReport(self, textWidth=100, markdown=False):
        """
        Create warning text report
        """
        #create text
        reportText = ""
        if len(self._warnings)>0:
            if self._reportType == ValidationReport.TYPE_RESOURCE:
                if markdown:
                    reportText = reportText + "* Sheet '{}':\n".format(ValidationReportEntry._escapeMarkdown(self._title))
                else:
                    reportText = reportText + "- Sheet '{}':\n".format(self._title)
            else:
                if markdown:
                    reportText = reportText + "* {}:\n".format(ValidationReportEntry._escapeMarkdown(self._title))
                else:
                    reportText = reportText + "- {}:\n".format(self._title)
            for warning in self._warnings:
                if markdown:
                    reportText = reportText + textwrap.fill("**{}**: {}".format(warning[0],warning[1]),textWidth-4,
                        initial_indent="  * ",subsequent_indent="    ") + "\n"
                else:
                    reportText = reportText + textwrap.fill("{}: {}".format(warning[0],warning[1]),textWidth-4,
                        initial_indent="  - ",subsequent_indent="    ") + "\n"
        return reportText
        
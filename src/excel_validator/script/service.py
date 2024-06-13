import argparse
import os
import pathlib
import re
import glob
import sys
from rich.console import Console
from rich.markdown import Markdown
from .. import validator

parser = argparse.ArgumentParser(description="Validate an Excel file")
parser.add_argument("filename", type=str, help="Excel filename")
parser.add_argument("--config", type=str, nargs="?",
                    help="configuration name or file")
parser.add_argument("--update", action="store_true", default=False,
                    help="update file in validation; remove empty rows and columns, automatically adjust cell type")
parser.add_argument("--report", type=str, nargs="?", default=False, choices=["full"],
                    help="create and print a text report to stdout; optionally provide argument 'full' to include warnings")
parser.add_argument("--createPackageFile", type=str, nargs="?", default=False,
                    help="create and store a frictionless package file; optionaly provide a location, otherwise this will be derived from the XLSX filename")
parser.add_argument("--createTextReport", type=str, nargs="?", default=False,
                    help="create and store a text report; optionaly provide a location, otherwise this will be derived from the Excel filename")
parser.add_argument("--createMarkdownReport", type=str, nargs="?", default=False,
                    help="create and store a textmarkdown report; optionaly provide a location, otherwise this will be derived from the Excel filename")
parser.add_argument("--create", type=str, nargs="?",
                    help="create a new configuration and store this at the specified location")
args = parser.parse_args()

def service():
    #check xlsx filename
    xlsx_filename = os.path.abspath(args.filename)
    if os.path.exists(xlsx_filename):
        if not os.path.isfile(xlsx_filename):
            parser.error("Couldn't find %s" % args.filename)
        elif not os.access(xlsx_filename, os.R_OK):
            parser.error("Couldn't access %s" % args.filename)
        else:
            if args.create:
                _create(xlsx_filename)
            else:
                basename = os.path.basename(xlsx_filename)
                print("[%s]" % basename)
                validation = _validate(xlsx_filename)
                print(f"\033[F%s [%s]" % (
                    "  \033[92mVALID\033[0m" if validation.valid else "\033[31mINVALID\033[0m",
                    basename))
                if args.report is None or args.report:
                    console = Console()
                    reportText = validation.createMarkdownReport(warnings=(not args.report is None))
                    md = Markdown("%s\n---" % reportText)
                    console.print(md)
    else:
        xlsx_filenames = []
        for entry in glob.glob(xlsx_filename):
            if os.path.exists(entry) and os.path.isfile(entry) and os.access(entry, os.R_OK):
                xlsx_filenames.append(entry)
        if len(xlsx_filenames)==0:
            parser.error("Couldn't find %s" % args.filename)
        if args.create:
            _create(xlsx_filenames[0])
        else:
            for xlsx_filename in xlsx_filenames:
                basename = os.path.basename(xlsx_filename)
                print("[%s]" % basename)
                validation = _validate(xlsx_filename)
                print(f"\033[F%s [%s]" % (
                    "  \033[92mVALID\033[0m" if validation.valid else "\033[31mINVALID\033[0m",
                    basename))
                if args.report is None or args.report:
                    console = Console()
                    reportText = validation.createMarkdownReport(warnings=(not args.report is None))
                    md = Markdown("%s\n---" % reportText)
                    console.print(md)
        
def _create(xlsx_filename):
    if args.config:
        parser.error("You can't combine the CONFIG and CREATE parameter")
    else:
        try:
            validator.Validate(xlsx_filename, None, create=args.create, cli=True)
        except Exception as ex:
            parser.error(ex)

def _validate(xlsx_filename):
    internal_config_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)),"../config")
    #get configuration for validation
    if args.config:
        config_filename = os.path.abspath(args.config)
        if not os.path.exists(config_filename):
            config_filename = os.path.join(internal_config_directory, args.config)
        if not os.path.exists(config_filename):
            parser.error("Can't find configuration %s" % args.config)
        elif os.path.isdir(config_filename):
            config_filename = os.path.join(config_filename, "config.json")
            if not os.path.exists(config_filename):
                parser.error("Can't find configuration %s" % args.config)
    else:
        config_filename = os.path.join(internal_config_directory, "default/config.json")
    try:
        validation = validator.Validate(xlsx_filename, config_filename, updateFile=args.update, cli=True)
        if args.createPackageFile is None or isinstance(args.createPackageFile,str):
            if args.createPackageFile is None:
                package_filename = "%s.json" % os.path.splitext(xlsx_filename)[0]
            else:
                package_filename = args.createPackageFile
                if os.path.exists(package_filename):
                    raise FileExistsError("%s already exists" % package_filename)
            validation.createPackageJSON(package_filename)
        if args.createTextReport is None or isinstance(args.createTextReport,str):
            if args.createTextReport is None:
                textreport_filename = "%s.txt" % os.path.splitext(xlsx_filename)[0]
            else:
                textreport_filename = args.createTextReport
                if os.path.exists(textreport_filename):
                    raise FileExistsError("%s already exists" % textreport_filename)
            with open(textreport_filename, "w") as f:
                f.write(validation.createTextReport(textreport_filename))
        if args.createMarkdownReport is None or isinstance(args.createMarkdownReport,str):
            if args.createMarkdownReport is None:
                mdreport_filename = "%s.md" % os.path.splitext(xlsx_filename)[0]
            else:
                mdreport_filename = args.createMarkdownReport
                if os.path.exists(mdreport_filename):
                    raise FileExistsError("%s already exists" % mdreport_filename)
            with open(mdreport_filename, "w") as f:
                f.write(validation.createMarkdownReport(mdreport_filename))
        return validation
    except Exception as ex:
        parser.error(ex)
    
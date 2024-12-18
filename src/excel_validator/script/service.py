import argparse
import os
import pathlib
import re
import glob
import sys
import shutil
import logging
from rich.console import Console
from rich.markdown import Markdown
from .. import validator
from .. import webservice

logging.basicConfig(format="%(asctime)s | %(name)s |  %(levelname)s: %(message)s",
                    datefmt="%m-%d-%y %H:%M:%S")

parser = argparse.ArgumentParser(description="Excel Validator is a Python package designed to validate Excel files (.xlsx) based on configured schemas.")

#subparsers
sp = parser.add_subparsers(dest="command")
sp.required = True
parser_validate = sp.add_parser("validate", help="validate an Excel file")
parser_configuration = sp.add_parser("configuration", help="create a configuration")
parser_webservice = sp.add_parser("webservice", help="webservice for validation")

#parser validation
parser_validate.add_argument("--config", type=str, nargs="?", default=False,
                    help="configuration name or file for validation")
parser_validate.add_argument("--update", action="store_true", default=False,
                    help="update file in validation; remove empty rows and columns, automatically adjust cell type")
parser_validate.add_argument("--report", default=False, action="store_true",
                    help="create and print a text report to stdout")
parser_validate.add_argument("--reportType", type=str, nargs="?", default=False, choices=["full"],
                    help="set type to 'full' to include warnings")
parser_validate.add_argument("--createPackageFile", type=str, nargs="?", default=False,
                    help="create and store a frictionless package file; optionaly provide a location, otherwise this will be derived from the XLSX filename")
parser_validate.add_argument("--createTextReport", type=str, nargs="?", default=False,
                    help="create and store a text report; optionaly provide a location, otherwise this will be derived from the Excel filename")
parser_validate.add_argument("--createMarkdownReport", type=str, nargs="?", default=False,
                    help="create and store a textmarkdown report; optionaly provide a location, otherwise this will be derived from the Excel filename")
parser_validate.add_argument("filename", type=str, help="Excel filename", nargs="+")

#parser configuration
parser_configuration.add_argument("--output", type=str, help="location for configuration files", nargs="?", default=None)
parser_configuration.add_argument("filename", type=str, help="Excel filename")

#parser service
parser_webservice.add_argument("--config", type=str, nargs="?", default=False,
                    help="configuration file for webservice")

args = parser.parse_args()

def service():
    if args.command == "validate":
        service_validate()
    elif args.command == "configuration":
        service_configuration()
    elif args.command == "webservice":
        service_webservice()

def service_webservice():
    if args.config:
        config = os.path.abspath(args.config)
    else:
        config = os.path.abspath("config.ini")
        if not os.path.exists(config):
            answer = None
            while answer not in ["y", "n"]:
                answer = input("No configuration found, create new config.ini [y/n]? ").lower()
            if answer=="n":
                return
            shutil.copyfile(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../config.ini"),config)
    ws = webservice.Webservice(config)
    ws.service()

def service_configuration():
    if isinstance(args.filename,str):
        xlsx_filename = os.path.abspath(args.filename)
        if os.path.exists(xlsx_filename):
            if not os.path.isfile(xlsx_filename):
                parser.error("Couldn't find %s" % args.filename)
            elif not os.access(xlsx_filename, os.R_OK):
                parser.error("Couldn't access %s" % args.filename)
            else:
                if args.output is None:
                    outputLocation = os.path.join(
                        os.path.dirname(xlsx_filename),
                        "%s.config" % os.path.splitext(os.path.basename(xlsx_filename))[0]
                    )
                else:
                    outputLocation = args.output
                try:
                    basename = os.path.basename(xlsx_filename)
                    print("[%s]" % basename)
                    validator.Validate(xlsx_filename, None, create=outputLocation, cli=True)
                except Exception as ex:
                    parser.error(ex)
        else:
            parser.error("Couldn't find %s" % args.filename)

def service_validate():
    if isinstance(args.filename,str):
        xlsx_filename = os.path.abspath(args.filename)
        if os.path.exists(xlsx_filename):
            if not os.path.isfile(xlsx_filename):
                parser.error("Couldn't find %s" % args.filename)
            elif not os.access(xlsx_filename, os.R_OK):
                parser.error("Couldn't access %s" % args.filename)
            else:
                basename = os.path.basename(xlsx_filename)
                print("[%s]" % basename)
                validation = _validate(xlsx_filename)
                if not validation._config is None:
                    print(f"\033[F%s [%s]" % (
                        "  \033[92mVALID\033[0m" if validation.valid else "\033[31mINVALID\033[0m",
                        basename))
                    if args.report:
                        console = Console()
                        reportText = validation.createMarkdownReport(warnings=(args.reportType and args.reportType=="full"))
                        md = Markdown("%s\n---" % reportText)
                        console.print(md)
        else:
            parser.error("Couldn't find %s" % args.filename)
    else:
        xlsx_filenames = []
        for entry in args.filename:
            if os.path.exists(entry) and os.path.isfile(entry) and os.access(entry, os.R_OK):
                xlsx_filenames.append(os.path.abspath(entry))
        if len(xlsx_filenames)==0:
            parser.error("Couldn't find %s" % args.filename)
        for xlsx_filename in xlsx_filenames:
            basename = os.path.basename(xlsx_filename)
            print("[%s]" % basename)
            validation = _validate(xlsx_filename)
            if not validation._config is None:
                print(f"\033[F%s [%s]" % (
                    "  \033[92mVALID\033[0m" if validation.valid else "\033[31mINVALID\033[0m",
                    basename))
                if args.report:
                    console = Console()
                    reportText = validation.createMarkdownReport(warnings=(args.reportType and args.reportType=="full"))
                    md = Markdown("%s\n---" % reportText)
                    console.print(md)
    
def _validate(xlsx_filename):
    config_filename = validator.Validate.getConfigFilename(args.config)
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
    finally:
        pass
    
# Excel Validator

Excel Validator is a Python package designed to validate Excel files (.xlsx) based on configured schemas. The tool ensures your Excel files adhere to specified schemas and generates detailed reports in case of validation errors. Built on the robust Frictionless library, Excel Validator also allows for dynamic schema creation, where fields are included based on row data from other sheets.

## Features

* Validate Excel files against predefined schemas.
* Generate detailed reports highlighting any validation issues.
* Dynamic schema creation based on data from other sheets.
* Easy integration with your existing data processing workflows.
* Built on top of the Frictionless library for reliable and extensible validation.
* Integrated webservice for online validation.

## Installation

The software requires at least Python version 3.11. It is recommended to create and activate a dedicated conda environment for the installation of this software:

```
conda create -n excel-validator python=3.11
conda activate excel-validator
```

Now you can install Excel Validator via pip:

```
pip install excel-validator
```

## Usage

Once installed, the software can be directly used from the command line interface. Use the `--help` option to get additional instructions on how to use it:

```
usage: excel_validator [-h] {validate,configuration,webservice} ...
```

Three different commands can be used, each with its own options:

* **validate**: validates the provided Excel file
* **configuration**: creates an initial configuration based on the provided Excel file
* **webservice**: starts a web service for online validation of Excel files

---

The package can also imported directly in your Python application:

```
import excel_validator

import logging
logging.basicConfig(format="%(asctime)s | %(levelname)s: %(message)s", datefmt="%m-%d-%y %H:%M:%S")
logging.getLogger("excel_validator.validator").setLevel(logging.INFO)

excelFilename = "/path/to/filename.xlsx"
configFilename = "/path/to/specific/configuration"
validation = excel_validator.Validate(excelFilename,configFilename)
```

A configuration for [MIAPPE](https://www.miappe.org/) is already included in the software and can be used with:

```
configFilename = excel_validator.Validate.getConfigFilename("miappe")
```

The `validation` object contains the status (`validation.valid`) and can be used to create a report if the Excel file is found to be invalid:

```
# print(validation.createMarkdownReport())
print(validation.createTextReport())
```

---
This software has been developed for the [AGENT](https://www.agent-project.eu/) project


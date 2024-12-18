# Excel Validator

Excel Validator is a Python package designed to validate Excel files (.xlsx) based on configured schemas. The tool ensures your Excel files adhere to specified schemas and generates detailed reports in case of validation errors. Built on the robust Frictionless library, Excel Validator also allows for dynamic schema creation, where fields are included based on row data from other sheets.

## Features

* Validate Excel files against predefined schemas.
* Generate detailed reports highlighting any validation issues.
* Dynamic schema creation based on data from other sheets.
* Easy integration with your existing data processing workflows.
* Built on top of the Frictionless library for reliable and extensible validation.

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

Three different commands can be distinghuised:
* validate:
  validation of provided xlsx file
* configuration:
  create initial configuration based on provided xlsx file, which can manually be extended and improved
* webservice:
  start a webservice for online validation of xlsx files

---
This software has been developed for the [AGENT](https://www.agent-project.eu/) project


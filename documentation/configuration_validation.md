# Excel Validator Configuration of Validation

The [Excel Validator](..) is a Python package designed to validate Excel files (.xlsx) based on configured schemas. 

## Automatically create a new configuration

It is possible to generate an initial validation configuration based on an Excel file:

```
# create configuration filename.xlsx and store in location/configuration/initial
excel-validator configuration filename.xlsx --output location/configuration/initial
```

This configuration is intended to be adjusted manually afterward.

## Configuration of Validation

A typical validation configuration includes a central configuration file named `config.json`, along with optional separate sheet schemas, checklists, transformation pipelines, and plugins. The configuration file contains general settings as well as definitions for the various sheets, including links to schemas and other checks, transformations, or actions:

```
├── config.json
├── schema
│   ├── 01_first_sheet.json
│   ├── 02_second_sheet.json
│   ├── 03_final_sheet.json
├── plugin
```

The configuration is structured as an object with four items: `settings` and `sheets` are mandatory, while `package` and `webinterface` are optional. Below is a detailed description of these items, and a [JSON schema file](../src/excel_validator/config.json) is also available.

## Section: settings

The `settings` section is obligatory, and may contain:

- **allowAdditionalSheets**: boolean<br/>Allow presence of additional sheets
- **requireSheetOrder**: boolean<br/>Require the sheets to be in the defined order
- **adjustTypeForStringColumns**: boolean<br/>Automatically adjust type for string columns
- **removeEmptyRows**: boolean<br/>Automatically remove empty rows
- **removeEmptyColumns**: boolean<br/>Automatically remove empty columns
- **schemaPath**: boolean<br/>Location schemas
- **pluginPath**: boolean<br/>Location plugins

## Section: webinterface

The `webinterface` section is an optional array that defines parts of typically the settings configuration that can be configured. Each entry in this array is an object that corresponds to a section displayed on the website. This object should always contain an `options` array and may optionally include a `description` string. The `options` array contains the parts of the configuration that will be configurable on the website, with each entry being an object that should contain:

- **type**: string<br/>For now only `boolean` is supported
- **setting**: array<br/>An array of strings that describes the location of an entry in the configuration file
- **default**<br />The default value as presented on the website
- **label**: string<br />Description of the option presented op the website

## Section: sheets

The `sheets` section is a mandatory array that defines the different sheets to be validated. Each entry in this array is an object corresponding to a sheet in the Excel file. This object must always contain the `name` of the sheet. Below is a description of all items:

- **name**: string<br/>The name of the Excel sheet
- **optional**: boolean<br/>Should this sheet always be present in the Excel file
- **resource**: string<br />Name of the resource; can only contain lowercase alphanumeric characters plus ., - and _
- **dependencies**: array<br/>Array of strings describing the other resources that should be present
- **adjustTypeForStringColumns**: boolean<br/>Automatically adjust type for string columns, does override settings
- **removeEmptyRows**: boolean<br/>Automatically remove empty rows, does override settings
- **removeEmptyColumns**: boolean<br/>Automatically remove empty columns, does override settings
- **schema**: object<br/>Defining the validation schema (see below)
- **checklist**: object<br/>Defining the validation checklist (see below)
- **transforms**: array<br/>Defining the transform definitions for validation (see below)

### schema

The `schema` object should contain either a `file` or `data` entry, and it may optionally include a`dynamic` array:

- **file**: string<br/>A reference to a file containing a frictionless schema for resource validation
- **data**: object<br/>A frictionless schema for resource validation
- **dynamic** array<br/>Describing extension of the frictionless schema based on content other sheets. See the [JSON schema file](../src/excel_validator/config.json) or the included [configurations](../src/excel_validator/) for more details

### checklist

The `checklist` object should contain either a `file` or `data` entry:

- **file**: string<br/>A reference to a file containing a frictionless checklist definition for resource validation
- **data**: object<br/>A frictionless checklist definition for resource validation

### transforms

The `transform` array entry is an object that should contain a `resource` and `pipeline` entry, and optionally a `schema` entry:

- **resource**: string<br />Name of the resource; can only contain lowercase alphanumeric characters plus ., - and _
- **pipeline**: object<br/>Defining the transform pipeline with either a `file` or `data` entry:
  - **file**: string<br/>A reference to a file containing a frictionless pipeline definition
  - **data**: object<br/>A frictionless pipeline definition
- **schema**: object<br/>Defining the validation schema

## Section: package

The `package` section is optional, and may contain a `checklist` entry. This `checklist` object should contain either a `file` or `data` entry:

- **file**: string<br/>A reference to a file containing a frictionless checklist definition for package validation
- **data**: object<br/>A frictionless checklist definition for package validation


# Excel Validator Configuration

The [Excel Validator](..) is a Python package designed to validate Excel files (.xlsx) based on configured schemas.

## Configuration template for validation

Create initial validation configuration for Excel file:
```
# create configuration filename.xlsx and store in location/configuration/initial
excel-validator configuration filename.xlsx --output location/configuration/initial
```

A typical validation configuration includes a central configuration file named `config.json`, along with optional separate sheet schemas, checklists, transformation pipelines, and plugins. The central configuration file contains general settings as well as definitions for the various sheets, including links to schemas and other checks, transformations, or actions:

```
├── config.json
├── schema
│   ├── 01_first_sheet.json
│   ├── 02_second_sheet.json
│   ├── 03_final_sheet.json
```

The central configuration is structured like this:

```
{
    "settings": {},
    "webinterface": [],
    "package": {},
    "sheets": []
}
```

The `settings` section is obligatory, and may contain:

- **allowAdditionalSheets**: boolean<br/>Allow presence of additional sheets
- **requireSheetOrder**: boolean<br/>Require the sheets to be in the defined order
- **adjustTypeForStringColumns**: boolean<br/>Automatically adjust type for string columns
- **removeEmptyRows**: boolean<br/>Automatically remove empty rows
- **removeEmptyColumns**: boolean<br/>Automatically remove empty columns
- **schemaPath**: boolean<br/>Location schemas
- **pluginPath**: boolean<br/>Location plugins

The `webinterface` section is an optional array

TODO

The `package` section is optional

TODO

The `sheets` section is an obligatory array

TODO

- **


## Configuation webservice


```
[webservice]
debug=true
host=::
port=8080
threads=5
services=default,miappe
tmp=tmp
#title=Excel Validator
#text.intro=custom intro text with <b>html</b>-tags
#text.footer=custom footer text with <b>html</b>-tags

[validation]
threads=5
timeout=300

[default]
name=Default validation
config=default

[miappe]
name=MIAPPE validation
#text.upload=Select XLSX File for validation
config=miappe
download=true
```

TODO
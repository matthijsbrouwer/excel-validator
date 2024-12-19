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

The `settings` section 

- **


## Configuation webservice
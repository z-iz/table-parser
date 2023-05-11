# table-parser
Simple script to parse and join tables from PDF files

## Overview
Use this script to parse PDF file with multiple tables having the same 
layout to a single CSV file for further analysis.

The script was developed and tested with native PDF files, i.e. files created
from electronic documents.

## How to install
The script runs with Python 3.8 and above and uses the following dependencies:
* [Pandas](https://pandas.pydata.org)
* [Camelot](https://camelot-py.readthedocs.io/en/master/)

Install the above dependencies first, then download the [script file](main.py).

## How to use
Run the script with the following command-line arguments:

```
python3 main.py \
-s <path to source PDF file> \
-r <path to output dir> \
-c <path to config dir>
```

### Source PDF file
Source PDF file should be native (i.e. created from electronic document), 
not a scanned one.

Also, it should contain multiple tables having the same 
layout (number of columns and their names).

### Config directory
This directory should contain CSV files describing the 
configuration of parsing.

Each of these config files describe a single type of 
table (set of tables having the same layout) in the source document.

### Config file
Config file for each table type is a CSV file having the following columns:
* `<Any_name>` - data that differentiates tables between each other
* `Page` - page number where the table is located or starts
* `Table` - index number of the table on the page (in case of several tables on a page)
* `Header_Size` - number of rows in the table header
* `Footer_Size` - number of rows in the table footer

[Example config file](examples/config_file_example.csv).

### Output directory
The parse results in CSV format will be placed in this directory.
A resulting file is generated for each config file (i.e. table type)

## Result

Resulting CSV file for a particular table type will contain 
the parsed data from the tables of this type from the source PDF file.

Tables are appended in the order they were listed in the config file.

Before appending, the script checks that the number of columns match between the appended part and the main part.

The first column of the resulting table will be filled with data from the "distinguishing" column of the config file.

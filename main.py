import camelot
import pandas
import argparse
from pathlib import Path

PAGE_COL_NAME = 'Page'
TABLE_COL_NAME = 'Table'
HEADER_SIZE_COL_NAME = 'Header_Size'
FOOTER_SIZE_COL_NAME = 'Footer_Size'


def detect_delimiter(csv_file):
    with open(csv_file, 'r') as myCsvfile:
        header = myCsvfile.readline()
        if header.find(";") != -1:
            return ";"
        if header.find(",") != -1:
            return ","
    # default delimiter (MS Office export)
    return ";"

    # TODO Paths validation
    # TODO Exception handling


if __name__ == '__main__':
    # Get paths from command line arguments
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-s", "--source", help="Path to source PDF file", type=Path)
    argParser.add_argument("-r", "--result", help="Path to resulting CSV directory", type=Path)
    argParser.add_argument("-c", "--config", help="Path to config CSV directory", type=Path)

    args = argParser.parse_args()

    # Get path to the config directory and extract files list from it
    config_dir_path = Path(str(args.config)).glob('**/*')
    csv_files = [x for x in config_dir_path if x.is_file() & (x.suffix == '.csv')]

    for config_file in csv_files:

        print('********************************************************************************************')
        print("Processing configuration file: " + str(config_file))

        # Convert paths to strings
        source_path = str(args.source)
        result_path = str(args.result) + '/' + str(config_file.stem) + '_result.csv'
        config_path = str(config_file)

        # Get CSV delimiter
        delimiter = detect_delimiter(config_path)

        # Read column row to specify types
        col_names = pandas.read_csv(config_path, nrows=0, sep=delimiter).columns.values
        first_col_name = col_names[0]
        types_dict = {first_col_name: str,
                      PAGE_COL_NAME: int,
                      TABLE_COL_NAME: int,
                      HEADER_SIZE_COL_NAME: int,
                      FOOTER_SIZE_COL_NAME: int}

        # Read config file to get page numbers where tables are located in the document and rows to delete
        tables_to_parse = pandas.read_csv(config_path, dtype=types_dict, sep=delimiter)
        tables_to_parse.set_index([PAGE_COL_NAME, TABLE_COL_NAME], inplace=True,
                                  append=True, drop=False)

        page_numbers_list = tables_to_parse[PAGE_COL_NAME].astype(str).values.tolist()
        page_numbers_string = ','.join(page_numbers_list)

        # Read the document on specified pages
        print('Parsing ' + str(len(page_numbers_list)) + ' tables from the file: ' + source_path)
        print('Using config file: ' + config_path)
        tables = camelot.read_pdf(source_path, pages=page_numbers_string)

        # Initializing the table to store parsing results and its properties
        resulting_table = None
        resulting_table_width = None
        # List to store results of table parsing accuracy
        accuracy_results_list = []
        processed_tables_count = 0

        print('Parsing complete, starting data export')
        for table in tables:
            page = table.page
            order = table.order

            country_row = tables_to_parse.loc[(tables_to_parse[PAGE_COL_NAME] == page)
                                              & (tables_to_parse[TABLE_COL_NAME] == order)].head()

            if not country_row.empty:
                # Create a new table to export data with the same columns as the first table plus country column
                if resulting_table is None:
                    resulting_table = table.df.iloc[:country_row[HEADER_SIZE_COL_NAME].values[0], :].copy()
                    resulting_table.insert(0, first_col_name, None)
                    resulting_table.at[0, first_col_name] = first_col_name
                    resulting_table_width = len(resulting_table.columns)

                # Fetch dataframe
                df = table.df

                # Check that width of table matches the expected width
                table_width = len(df.columns)
                if table_width != resulting_table_width - 1:
                    print(
                        'Table #' + str(order) + ' on page # ' + str(page) + ' has incorrect width: ' + str(table_width)
                        + '. Table was not appended to the resulting table')
                    continue

                # Remove header and footer rows, getting their size from spec
                header_size = country_row[HEADER_SIZE_COL_NAME].values[0]
                footer_size = country_row[FOOTER_SIZE_COL_NAME].values[0]
                df.drop(df.head(header_size).index, inplace=True)
                df.drop(df.tail(footer_size).index, inplace=True)

                # Add country data
                df.insert(0, first_col_name, country_row[first_col_name].values[0])

                # Append data to the resulting table
                resulting_table = pandas.concat([resulting_table, df])

                # Save stats
                processed_tables_count += 1
                accuracy_results_list.append(table.parsing_report['accuracy'])

        resulting_table.to_csv(result_path, index=False, header=False, sep=delimiter)
        if processed_tables_count > 0:
            print('Finished data export, parsed ' + str(processed_tables_count) + ' tables with average accuracy of '
                  + str(sum(accuracy_results_list) / len(accuracy_results_list)))
            print('Results saved to file: ' + str(result_path))
        else:
            print('No data was exported. Check that specification is correct')

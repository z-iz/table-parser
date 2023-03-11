import camelot
import pandas
import argparse
from pathlib import Path

if __name__ == '__main__':
    # Get paths from command line arguments
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-s", "--source", help="Path to source PDF file", type=Path)
    argParser.add_argument("-r", "--result", help="Path to resulting CSV file", type=Path)
    argParser.add_argument("-c", "--config", help="Path to config CSV file", type=Path)

    args = argParser.parse_args()

    print(args.source, type(args.source), args.source.exists())
    print(args.result, type(args.result), args.result.exists())
    print(args.config, type(args.config), args.config.exists())

    # TODO Paths validation

    # Convert paths to strings
    source_path = str(args.source)
    result_path = str(args.result)
    config_path = str(args.config)

    # Read config file to get page numbers where tables are located in the document
    columns = ['Country', 'Page', 'Table']
    tables_to_parse = pandas.read_csv(config_path, dtype={
        'Country': str,
        'Page': int,
        'Table': int
    })
    tables_to_parse.set_index(["Page", "Table"], inplace=True,
                              append=True, drop=False)

    page_numbers_list = tables_to_parse['Page'].astype(str).values.tolist()
    page_numbers_string = ','.join(page_numbers_list)

    # Read the document on specified pages
    print('Parsing ' + str(len(page_numbers_list)) + ' tables from the file: ' + source_path)
    print('Using config file: ' + config_path)
    tables = camelot.read_pdf(source_path, pages=page_numbers_string)

    # Initializing the table to store parsing results and its properties
    resulting_table = None
    first_column_name = None
    resulting_table_width = None
    # List to store results of table parsing accuracy
    accuracy_results_list = []
    processed_tables_count = 0

    print('Parsing complete, starting data export')
    for table in tables:
        page = table.page
        order = table.order

        country_row = tables_to_parse.loc[(tables_to_parse['Page'] == page)
                                          & (tables_to_parse['Table'] == order)].head()

        if not country_row.empty:
            # Create a new table to export data with the same columns as the first table plus country column
            if resulting_table is None:
                resulting_table = table.df.iloc[:1, :].copy()
                resulting_table.insert(0, 'Country', 'Country')
                first_column_name = str(resulting_table.iloc[0, 1]).lower()
                resulting_table_width = len(resulting_table.columns)

            # Fetch dataframe
            df = table.df

            # Check that width of table matches the expected width
            table_width = len(df.columns)
            if table_width != resulting_table_width - 1:
                print('Table #' + str(order) + ' on page #' + str(page) + 'has incorrect width: ' + str(table_width)
                      + '. Table was not appended to the resulting table')
                continue

            # Remove header and total rows
            df.drop(df.loc[df[0].str.lower().str.startswith(first_column_name)].index, inplace=True)
            df.drop(df.loc[df[0].str.lower().str.startswith('total')].index, inplace=True)

            # Add country data
            df.insert(0, 'Country', country_row['Country'].values[0])

            # Append data to the resulting table
            resulting_table = pandas.concat([resulting_table, df])

            # Save stats
            processed_tables_count += 1
            accuracy_results_list.append(table.parsing_report['accuracy'])

    resulting_table.to_csv(result_path, index=False, header=False)
    if processed_tables_count > 0:
        print('Finished data export, parsed ' + str(processed_tables_count) + ' tables with average accuracy of '
              + str(sum(accuracy_results_list) / len(accuracy_results_list)))
        print('Results saved to file: ' + str(result_path))
    else:
        print('No data was exported. Check that specification is correct')

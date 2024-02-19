# Wells Fargo Statement Extractor
Do you have PDF statements, but want to do something useful for them? Never fear, statement extractor is here!
Things you need:
 - Python
 - pdfplumber (installed via pip or something)
 - Run `python convertStatement.py "011516 WellsFargo.pdf"`
You will receive a shiny new CSV file with its beautiful contents.

## Combine CSVs
This will combine multiple statements in a directory (recursively).
Things you need:
 - pandas (pip install pandas)
 - Run `python combineCSVByDate.py my-converted-csv-folder`

This took a lot of trial and error and pain, profit from my suffering!
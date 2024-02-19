import argparse
import os
import pdfplumber
import sys
import re
import csv
from dateutil.relativedelta import relativedelta
from datetime import datetime

def extract_transactions_for_page(page, columns, statement_date):
    transactions = []
    column_positions = {column: None for column in columns}
            
    words = page.extract_words(keep_blank_chars=True)
    words.sort(key=lambda word: (word['top'], word['x0']))

    if None in column_positions.values():
      processed_indices = []
      for i, word in enumerate(words):
        if word['text'] in columns and column_positions[word['text']] is None:
          column_positions[word['text']] = word['x0']
          processed_indices.append(i)

      # Remove processed words
      for index in sorted(processed_indices, reverse=True):
        del words[index]
    
    # Group words by row
    rows = []
    for word in words:
      row = word['top']
      if not rows or rows[-1][0] != row:
        rows.append((row, []))
      rows[-1][1].append(word)

    # Sort words in each row by x0 attribute
    for _, words_in_row in rows:
      words_in_row.sort(key=lambda word: word['x0'])

    # Now you can process each row
    for i, (row, words_in_row) in enumerate(rows):
      # Initialize a new transaction
      transaction = {column: '' for column in columns}

      for word in words_in_row:
        if 'Ending balance' in word['text']:
          break
        for column in columns:
          try:
            if column_positions[column] <= word['x0'] < column_positions.get(next(iter(columns[columns.index(column)+1:]), ''), float('inf')):
              if column == "Date" and re.match(r'\d{1,2}/\d{1,2}', word['text']):
                transaction["Date"] = word['text']
              elif column != "Date":
                transaction[column] += word['text'] + ' '
          except:
            print(f'Error processing word: {word}')
            print(f'Columns: {columns}')
            print(f'Column positions: {column_positions}')
            print(f'Word: {word}')
            sys.exit(1)
      # Check if the line starts with a date
      if re.match(r'\d{1,2}/\d{1,2}', transaction['Date']):
        transactions.append(transaction)
      elif i > 0 and re.match(r'\d{1,2}/\d{1,2}', rows[i-1][1][0]['text']):
        # If the previous row starts with a date, append to the previous transaction
        for column in columns:
          if column != "Date":
            transactions[-1][column] += '\n' + transaction[column]

    # When processing the date, add the year and handle the new year transition
    for transaction in transactions:
        month, day = map(int, transaction['Date'].split('/'))
        transaction_date = datetime(statement_date.year, month, day)
        month_difference = relativedelta(transaction_date, statement_date).months

        if month_difference > 10:
            transaction_date = transaction_date.replace(year=statement_date.year - 1)
        elif month_difference < -10:
            transaction_date = transaction_date.replace(year=statement_date.year + 1)

        transaction['Date'] = transaction_date.strftime('%m/%d/%Y')


    return transactions

def extract_transactions_across_pages(file_path, end_pattern, columns):
    transactions = []
    is_extracting = False

    # Extract the date from the filename
    match = re.search(r'(\d{6})', file_path)
    if match:
        date_str = match.group(1)
        statement_date = datetime.strptime(date_str, '%m%d%y')
    else:
        print(f'Could not extract date from filename: {file_path}')
        return

    with pdfplumber.open(file_path) as pdf:
      for page in pdf.pages:
        page_text = page.extract_text()
        if page.page_number == 2:
          is_extracting = True
        if is_extracting:
          transactions.extend(extract_transactions_for_page(page, columns, statement_date))
        if end_pattern in page_text and is_extracting:
          is_extracting = False
          break
    return transactions

def convert_pdf(file_path):
  columns = ["Date", "Number", "Description", "Deposits/", "Withdrawals/", "Ending daily"]
  end_pattern = "The Ending Daily Balance does not reflect any pending withdrawals "
  
  transactions = extract_transactions_across_pages(file_path, end_pattern, columns)

  # Export to CSV
  csv_file = file_path.replace('.pdf', '_transactions.csv')
  with open(csv_file, 'w', newline='') as csvfile:
      writer = csv.DictWriter(csvfile, fieldnames=columns)
      writer.writeheader()
      for transaction in transactions:
          writer.writerow({column: transaction[column].strip() for column in columns})

  print(f"CSV file created: {csv_file}")

def batch_convert(directory):
  for root, dirs, files in os.walk(directory):
      for file in files:
          if file.endswith(".pdf"):
              convert_pdf(os.path.join(root, file))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", help="Convert all PDFs in the specified directory", action="store_true")
    parser.add_argument("path", help="The path to the PDF file or directory to convert")
    args = parser.parse_args()

    if args.batch:
        batch_convert(args.path)
    else:
        convert_pdf(args.path)
    
    

if __name__ == "__main__":
    main()

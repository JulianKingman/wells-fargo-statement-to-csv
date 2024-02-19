import argparse
import os
import pdfplumber
import sys
import re
import csv

def extract_transactions_for_page(page, columns):
    transactions = []
    page_text = page.extract_text()
    column_positions = {column: None for column in columns}
    current_date = None
            
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
          if column_positions[column] <= word['x0'] < column_positions.get(next(iter(columns[columns.index(column)+1:]), ''), float('inf')):
            if column == "Date" and re.match(r'\d{1,2}/\d{1,2}', word['text']):
              transaction["Date"] = word['text']
            elif column != "Date":
              transaction[column] += word['text'] + ' '
      # Check if the line starts with a date
      if re.match(r'\d{1,2}/\d{1,2}', transaction['Date']):
        transactions.append(transaction)
      elif i > 0 and re.match(r'\d{1,2}/\d{1,2}', rows[i-1][1][0]['text']):
        # If the previous row starts with a date, append to the previous transaction
        for column in columns:
          if column != "Date":
            transactions[-1][column] += '\n' + transaction[column]

    return transactions
def extract_transactions_across_pages(file_path, start_pattern, end_pattern, columns):
    transactions = []
    is_extracting = False

    with pdfplumber.open(file_path) as pdf:
      for page in pdf.pages:
        page_text = page.extract_text()
        if start_pattern in page_text:
          is_extracting = True
        if is_extracting:
          transactions.extend(extract_transactions_for_page(page, columns))
        if end_pattern in page_text and is_extracting:
          is_extracting = False
          break
    return transactions
def convert_pdf(file_path):
  columns = ["Date", "Number", "Description", "Deposits/", "Withdrawals/", "Ending daily"]
  start_pattern = "Transaction history"
  end_pattern = "Ending balance on"
  transactions = extract_transactions_across_pages(file_path, start_pattern, end_pattern, columns)
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

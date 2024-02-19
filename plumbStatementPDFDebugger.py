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
    words_by_row = {}
    for word in words:
      # Round the top attribute to avoid minor differences in positioning
      row = round(word['top'])
      if row not in words_by_row:
        words_by_row[row] = []
      words_by_row[row].append(word)

    # Sort words in each row by x0 attribute
    for row in words_by_row:
      words_by_row[row].sort(key=lambda word: word['x0'])

    # Process each row
    for row, words_in_row in sorted(words_by_row.items()):
      # Check if the line starts with a date
      if re.match(r'\d{1,2}/\d{1,2}', words_in_row[0]['text']):
        # If it does, start a new transaction
        transaction = {column: '' for column in columns}
        transaction['Date'] = re.findall(r'\d{1,2}/\d{1,2}', words_in_row[0]['text'])[0]
        for word in words_in_row:
          if 'Ending balance' in word['text']:
            break
          for column in columns:
            if column_positions[column] <= word['x0'] < column_positions.get(next(iter(columns[columns.index(column)+1:]), ''), float('inf')):
              if column != "Date":
                transaction[column] += word['text'] + ' '
        transactions.append(transaction)

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
          print(f"End pattern found on page {page.page_number}")
          is_extracting = False
          break
    return transactions

def main():
    if len(sys.argv) != 2:
        print("Usage: python extractPDFData.py filename.pdf")
        sys.exit(1)

    file_path = sys.argv[1]
    columns = ["Date", "Number", "Description", "Deposits/", "Withdrawals/", "Ending daily"]
    transactions = extract_transactions_across_pages(file_path, "Transaction history", "Ending balance on", columns)

    
    # Export to CSV
    csv_file = file_path.replace('.pdf', '_transactions.csv')
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        for transaction in transactions:
            # Print extracted data
            # for transaction in transactions:
            # print(' | '.join([f"{column}: {transaction[column].strip()}" for column in columns]))
            writer.writerow({column: transaction[column].strip() for column in columns})

    print(f"CSV file created: {csv_file}")

if __name__ == "__main__":
    main()

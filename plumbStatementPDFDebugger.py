import pdfplumber
import sys
import re
import csv

def extract_transactions_across_pages(file_path, start_pattern, end_pattern, headers):
    transactions = []
    header_positions = {header: None for header in headers}
    processing_section = False

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            
            # Check if we've reached the start of the section
            if start_pattern in text:
                print('start found, processing')
                processing_section = True
            
            if processing_section:
                words = page.extract_words(keep_blank_chars=True)

                # Find header positions on the first page where the section starts
                if None in header_positions.values():
                    for word in words:
                        if word['text'] in headers and header_positions[word['text']] is None:
                            header_positions[word['text']] = word['x0']

                lines = text.split('\n')
                for line in lines:
                    print(line)
                    if re.match(r'\d{1,2}/\d{1,2}', line):  # Checks if the line starts with a date
                        transaction = {header: '' for header in headers}
                        date_matched = False
                        for word in words:
                            for header in headers:
                                print({
                                    'text': word['text'], 
                                    'word': word['x0'], 
                                    'low': header_positions[header], 
                                    'high': header_positions.get(next(iter(headers[headers.index(header)+1:]), ''), float('inf')),
                                })
                                if header_positions[header] <= word['x0'] < header_positions.get(next(iter(headers[headers.index(header)+1:]), ''), float('inf')):
                                    if word['text'] in line:
                                        if header == "Date":
                                            if not date_matched and re.match(r'\d{1,2}/\d{1,2}', word['text']):
                                                transaction[header] += word['text'] + ' '
                                                date_matched = True
                                        else:
                                            transaction[header] += word['text'] + ' '
                        transactions.append(transaction)

            # Check if we've reached the end of the section
            if end_pattern in text and processing_section:
                print('end found')
                processing_section = False
                break  # Exit loop after processing the section

    return transactions

def main():
    if len(sys.argv) != 2:
        print("Usage: python extractPDFData.py filename.pdf")
        sys.exit(1)

    file_path = sys.argv[1]
    headers = ["Date", "Number", "Description", "Deposits/", "Withdrawals/", "Ending daily"]
    transactions = extract_transactions_across_pages(file_path, "Transaction history", "Ending balance on", headers)

    # Print extracted data
    # for transaction in transactions:
        # print(' | '.join([f"{header}: {transaction[header].strip()}" for header in headers]))
    
    # Export to CSV
    csv_file = file_path.replace('.pdf', '_transactions.csv')
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for transaction in transactions:
            writer.writerow({header: transaction[header].strip() for header in headers})

    print(f"CSV file created: {csv_file}")

if __name__ == "__main__":
    main()

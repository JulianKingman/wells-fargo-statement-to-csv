import os
import pandas as pd
import re
from datetime import datetime
import argparse

def combine_csvs(directory):
  csv_files = []

  # Step 1: Find CSVs and extract date from filename
  for root, dirs, files in os.walk(directory):
    for file in files:
      if file.endswith(".csv"):
        match = re.search(r'(\d{6})', file)
        if match:
          date_str = match.group(1)
          date = datetime.strptime(date_str, '%m%d%y')
          csv_files.append((date, os.path.join(root, file)))

  # Step 2: Sort them chronologically
  csv_files.sort()

  # Step 3: Combine them into one CSV
  combined_df = pd.concat([pd.read_csv(file) for date, file in csv_files])
  combined_df.to_csv(os.path.join(directory, 'combined.csv'), index=False)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("directory", help="The directory to process")
  args = parser.parse_args()

  combine_csvs(args.directory)

if __name__ == "__main__":
  main()
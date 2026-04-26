import argparse

import pandas as pd


parser = argparse.ArgumentParser(description="Print the first rows from a SOM Excel workbook.")
parser.add_argument("input_file", help="Path to the Excel workbook to read.")
args = parser.parse_args()

df = pd.read_excel(args.input_file)

print(df.head())

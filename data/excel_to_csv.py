# pip install pandas openpyxl

import os
import pandas as pd

def convert_xlsx_to_csv(folder_path):
    # Folder to store CSV files
    output_folder = os.path.join(folder_path, "csv_format")
    os.makedirs(output_folder, exist_ok=True)

    # Loop through all files in the folder
    for file in os.listdir(folder_path):
        if file.endswith(".xlsx"):
            xlsx_path = os.path.join(folder_path, file)

            # Load Excel file
            df = pd.read_excel(xlsx_path)

            # Convert extension and save CSV
            csv_filename = os.path.splitext(file)[0] + ".csv"
            csv_path = os.path.join(output_folder, csv_filename)

            df.to_csv(csv_path, index=False)
            print(f"Converted: {file} → {csv_filename}")

    print("Conversion complete!")

convert_xlsx_to_csv("./xlsx_format/")
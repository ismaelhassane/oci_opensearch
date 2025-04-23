import pandas as pd
import json

# Read your file
df = pd.read_excel(r"cross_reference_search\Raw_Data\Belgium_Dataset.xlsx") 

# Replace NaN with None
df = df.where(pd.notnull(df), None)


ndjson_file = r"cross_reference_search\Final_Data\Belgium_Dataset.json"
index_name = "belgium_dataset"

with open(ndjson_file, 'w', encoding='utf-8') as f_out:
    for _, row in df.iterrows():
        action = {"index": {"_index": index_name}}
        f_out.write(json.dumps(action, ensure_ascii=False) + "\n")
        f_out.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")

print("NDJSON file created:", ndjson_file)

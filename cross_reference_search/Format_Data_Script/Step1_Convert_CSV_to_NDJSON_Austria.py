import pandas as pd
import json

# Read your file
df = pd.read_excel(r"cross_reference_search\Raw_Data\Austria_Dataset.xlsx") 

# Replace NaN with None
df = df.where(pd.notnull(df), None)

# Convert the 'MA date' column to ISO 8601 format if it's not None
def reformat_date(date_value):
    if pd.notnull(date_value):
        # Convert to ISO 8601 string format
        return pd.to_datetime(date_value).isoformat()
    return None

df['MA date'] = df['MA date'].apply(reformat_date)

ndjson_file = r"cross_reference_search\Final_Data\Austria_Dataset.json"
index_name = "austria_dataset"

with open(ndjson_file, 'w', encoding='utf-8') as f_out:
    for _, row in df.iterrows():
        action = {"index": {"_index": index_name}}
        f_out.write(json.dumps(action, ensure_ascii=False) + "\n")
        f_out.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")

print("NDJSON file created:", ndjson_file)

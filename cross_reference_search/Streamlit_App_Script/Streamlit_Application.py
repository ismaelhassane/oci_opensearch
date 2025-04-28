import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from dotenv import load_dotenv
load_dotenv()
import os
import streamlit as st
import requests
import pandas as pd
from transformers import AutoTokenizer, AutoModel
import torch
import json

os.environ["STREAMLIT_WATCHER_TYPE"] = "none"
# Streamlit layout
st.set_page_config(layout="wide")
st.title("Medicinal Product Explorer")
# Load RXCUI to ATC4 mapping
with open("cross_reference_search\RXCUI_TO_ATC4\rxcui_to_atc4_mapping.json", "r") as f:
    rxcui_to_atc4 = json.load(f)

# OpenSearch details
OPENSEARCH_URL_EU = os.environ.get("OPENSEARCH_URL_EU")
INDEX_NAME_EU = "europe_dataset_v2_reindexed"

OPENSEARCH_URL_US = os.environ.get("OPENSEARCH_URL_US")
INDEX_NAME_US = "usa_dataset_filtered_embeddings_generic"
VECTOR_FIELD = "search_vector"
KNN_K = 20

USERNAME = os.environ.get("OPENSEARCH_USER")
PASSWORD = os.environ.get("OPENSEARCH_PASS")

# Load DistilRoBERTa model
model_name = "sentence-transformers/all-distilroberta-v1"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
model.eval()

def get_embedding(text):
    with torch.no_grad():
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        outputs = model(**inputs)
        embedding = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
        return embedding.tolist()

# UI Tabs
tab1, tab2 = st.tabs(["Europe Keyword Search", "US Semantic Search"])

# Europe keyword search
with tab1:
    st.subheader("Search in Europe Dataset")
    keyword = st.text_input("Enter search keyword:")
    country = st.text_input("Optional: Country filter (e.g., Belgium, Austria):")

    if st.button("Search Europe Dataset"):
        if keyword:
            base_query = {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": keyword,
                                "fields": [
                                    "Medicine name^4",
                                    "ATC code.keyword^2",
                                    "Active substance^3"
                                ]
                            }
                        },
                        {
                            "wildcard": {
                                "ATC code.keyword": {
                                    "value": f"{keyword.upper()}*",
                                    "boost": 2
                                }
                            }
                        }
                    ]
                }
            }

            query = {
                "size": 100,
                "query": {
                    "bool": {
                        "must": base_query,
                        "filter": [{"term": {"Country.keyword": country}}] if country else []
                    }
                },
                "_source": [
                    "Medicine name", "ATC code", "Active substance",
                    "Authorisation number", "Company", "Country", "Status"
                ]
            }

            response = requests.post(f"{OPENSEARCH_URL_EU}/{INDEX_NAME_EU}/_search", json=query, auth=(USERNAME, PASSWORD))
            if response.status_code == 200:
                hits = response.json().get("hits", {}).get("hits", [])
                st.write(f"Found {len(hits)} result(s).")
                if hits:
                    df = pd.DataFrame([{
                        "Medicine name": h["_source"].get("Medicine name", "N/A"),
                        "ATC code": h["_source"].get("ATC code", "N/A"),
                        "Active substance": h["_source"].get("Active substance", "N/A"),
                        "Authorisation number": h["_source"].get("Authorisation number", "N/A"),
                        "Company": h["_source"].get("Company", "N/A"),
                        "Country": h["_source"].get("Country", "N/A"),
                        "Status": h["_source"].get("Status", "N/A")
                    } for h in hits]).astype(str)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No results found.")
            else:
                st.error("OpenSearch error.")
        else:
            st.warning("Enter a keyword to search.")


# USA semantic search
with tab2:
    st.subheader("Semantic Search in US Dataset (DistilRoBERTa)")
    semantic_query = st.text_input("Describe the medical need:")

    if st.button("Semantic Search - USA Dataset"):
        if semantic_query:
            query_vector = get_embedding(semantic_query)
            query = {
                "size": KNN_K,
                "query": {
                    "knn": {
                        VECTOR_FIELD: {
                            "vector": query_vector,
                            "k": KNN_K
                        }
                    }
                }
            }

            url = f"{OPENSEARCH_URL_EU}/usa_cluster:{INDEX_NAME_US}/_search"
            response = requests.post(url, json=query, auth=(USERNAME, PASSWORD))

            if response.status_code == 200:
                hits = response.json().get("hits", {}).get("hits", [])
                st.write(f"Found {len(hits)} similar entries:")
                if hits:
                    data = []
                    for h in hits:
                        source = h["_source"]
                        openfda = source.get("openfda", {})
                        rxcui = openfda.get("rxcui", "N/A")

                        # Handle RXCUI as list or string
                        if isinstance(rxcui, list):
                            flat_rxcui = [str(r) for r in rxcui]
                        else:
                            flat_rxcui = [str(rxcui)]

                        # Lookup ATC codes
                        atc_codes = set()
                        for r in flat_rxcui:
                            if r in rxcui_to_atc4:
                                atc_codes.update(rxcui_to_atc4[r])

                        def clean_field(value):
                            if isinstance(value, list):
                                return ", ".join(str(v) for v in value)
                            return str(value)

                        data.append({
                            "Brand Name": clean_field(openfda.get("brand_name", "N/A")),
                            "Generic Name": clean_field(openfda.get("generic_name", "N/A")),
                            "Active Ingredient": clean_field(source.get("active_ingredient", "N/A")),
                            "Manufacturer": clean_field(openfda.get("manufacturer_name", "N/A")),
                            "RXCUI": ", ".join(flat_rxcui),
                            "ATC Code(s)": ", ".join(sorted(atc_codes)) if atc_codes else "N/A",
                            "NDC Authorization Code": clean_field(openfda.get("package_ndc", "N/A")),
                            "Indications and Usage": clean_field(source.get("indications_and_usage", "N/A")),
                            "Dosage": clean_field(source.get("dosage_forms_and_strengths", "N/A")),
                            "Purpose": clean_field(source.get("purpose", "N/A"))
                        })


                    df = pd.DataFrame(data).astype(str)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No similar results found.")
            else:
                st.error("OpenSearch semantic query failed.")
        else:
            st.warning("Enter a semantic query to search.")
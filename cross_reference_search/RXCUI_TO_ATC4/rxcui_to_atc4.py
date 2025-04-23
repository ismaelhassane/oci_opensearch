import requests
from opensearchpy import OpenSearch, helpers
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import json
import os
# Connect to OpenSearch
client = OpenSearch(
    hosts=[{
        'host': os.environ.get("OPENSEARCH_URL_US"),
        'port': 9200
    }],
    http_auth=(os.environ.get("OPENSEARCH_USER"), os.environ.get("OPENSEARCH_PASS")),
    use_ssl=True,
    verify_certs=True,
    ssl_show_warn=False
)

INDEX_NAME = "usa_dataset_filtered_embeddings_v2"

def get_unique_rxcuis():
    rxcuis = set()
    query = {"query": {"exists": {"field": "openfda.rxcui"}}, "_source": ["openfda.rxcui"]}
    results = helpers.scan(client, index=INDEX_NAME, query=query, scroll="5m")
    for doc in results:
        ids = doc['_source'].get("openfda", {}).get("rxcui", [])
        for rid in ids:
            if rid != "N/A":
                rxcuis.add(rid)
    return list(rxcuis)

def fetch_atc4(rxcui):
    try:
        url = f"https://rxnav.nlm.nih.gov/REST/rxclass/class/byRxcui.json?rxcui={rxcui}&classTypes=ATCPROD"
        response = requests.get(url, timeout=10)
        data = response.json()
        classes = data.get('rxclassDrugInfoList', {}).get('rxclassDrugInfo', [])
        atc4s = [item['rxclassMinConceptItem']['classId']
                 for item in classes if item['rxclassMinConceptItem']['classType'] == 'ATC1-4']
        return rxcui, atc4s if atc4s else ["N/A"]
    except Exception as e:
        return rxcui, ["N/A"]

def get_rxcui_to_atc4_mapping(rxcui_list, max_workers=10):
    mapping = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_atc4, rxcui): rxcui for rxcui in rxcui_list}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Fetching ATC4 codes"):
            rxcui, atc4 = future.result()
            mapping[rxcui] = atc4
    return mapping

# Run it
rxcui_list = get_unique_rxcuis()
print(f"Total RXCUIs: {len(rxcui_list)}")

mapping = get_rxcui_to_atc4_mapping(rxcui_list)

# Save to file
with open(r"cross_reference_search\RXCUI_TO_ATC4\rxcui_to_atc4_mapping.json", "w") as f:
    json.dump(mapping, f, indent=2)

print("Saved mapping to rxcui_to_atc4_mapping.json")

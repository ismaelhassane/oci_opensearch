import os
from opensearchpy import OpenSearch, helpers
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from dotenv import load_dotenv
load_dotenv()


# OpenSearch connection
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

# Index names
source_index = "usa_dataset_filtered_v2"
target_index = "usa_dataset_filtered_embeddings_generic"

# Load SentenceTransformer model
model = SentenceTransformer('sentence-transformers/all-distilroberta-v1')

def embed_text(text):
    return model.encode(text, convert_to_numpy=True).tolist()

# Create target index if it doesn't exist
if not client.indices.exists(index=target_index):
    client.indices.create(index=target_index, body={
        "settings": {
            "index": {
                "knn": True,
                "number_of_shards": 1,
                "number_of_replicas": 0
            }
        },
        "mappings": {
            "properties": {
                "search_vector": {
                    "type": "knn_vector",
                    "dimension": 768,
                    "method": {
                        "name": "hnsw",
                        "engine": "nmslib",
                        "space_type": "cosinesimil"
                    }
                }
            }
        }
    })

# Get existing document IDs in the target index
def get_existing_ids():
    ids = set()
    result = helpers.scan(client, index=target_index, query={"query": {"match_all": {}}}, _source=False, scroll="5m")
    for doc in result:
        ids.add(doc["_id"])
    return ids

existing_ids = get_existing_ids()

# Generate documents for indexing
def generate_actions(batch_size=100):
    search_after = None
    while True:
        query = {
            "size": batch_size,
            "sort": [{"_id": "asc"}],
            "_source": True  # Get all fields
        }
        if search_after:
            query["search_after"] = [search_after]

        response = client.search(index=source_index, body=query)
        hits = response["hits"]["hits"]
        if not hits:
            break

        for doc in hits:
            doc_id = doc["_id"]
            search_after = doc_id

            if doc_id in existing_ids:
                continue

            _source = doc["_source"]
            text = _source.get("combined_text")
            if not text:
                continue

            # Compute embedding
            embedding = embed_text(text)
            _source["search_vector"] = embedding

            yield {
                "_index": target_index,
                "_id": doc_id,
                "_source": _source
            }

# Start indexing
batch_size = 64
success_count = 0
error_count = 0
actions = generate_actions(batch_size=batch_size)

for ok, result in tqdm(helpers.parallel_bulk(client, actions, chunk_size=batch_size),
                       desc="Indexing embeddings"):
    if ok:
        success_count += 1
    else:
        error_count += 1
        print("Error:", result)

# Final status
print(f"\nDone. {success_count} documents indexed.")
if error_count:
    print(f"{error_count} errors occurred.")

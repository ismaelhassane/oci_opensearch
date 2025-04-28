# oci_opensearch
Projects related to OCI Search with OpenSearch

## **Cross-Reference Code Mapping System**
  Dynamically map medical products across terminologies and regulatory frameworks.


## Overview

This project enables semantic search using DistilRoBERTa and keyword-based filtering on structured drug data from Austria & Belgium

---

## Setup Instructions

1. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

2. **Set Environment Variables**
    ```bash
    export OPENSEARCH_HOST=...
    export OPENSEARCH_USER=...
    export OPENSEARCH_PASS=...
    ```

3. **Run the App**
    ```bash
    streamlit run Streamlit_App_Script/Streamlit_Application.py
    ```

---

## Data Preparation

### Ingest Data using Data Prepper

```bash
version: 2
pipeline_configurations:
  oci:
    secrets:
      opensearch-username:
        secret_id: "<username_in_vault>"
      opensearch-password:
        secret_id: "<password_in_vault>"
simple-sample-pipeline:
  source:
    oci-object:
      codec:
        csv:
      acknowledgments: true
      compression: none
      scan:
        scheduling:
          interval: PT40S
        buckets:
          - bucket:
              namespace: <namespace>
              name: <bucket_name>
              region: <region>
  processor:
    - date:
        match:
          - key: "MA date"
            patterns: ["dd-MM-yyyy", "MM/dd/yyyy", "yyyy-MM-dd"]
        output_format: "yyyy-MM-dd'T'HH:mm:ss.SSSXXX"
        destination: "MA date"

  sink:
    - opensearch:
        hosts: [ "<cluster_id>" ]
        username: ${{oci_secrets:opensearch-username}}
        password: ${{oci_secrets:opensearch-password}}
        insecure: false
        index: <index_name>
```

---

## Index Configuration (Dev Tools)

Performed in OpenSearch Dev Tools:

## Create europe_dataset index mappings

```bash
PUT europe_dataset
{
  "mappings": {
    "properties": {
      "Medicine name": { "type": "text" },
      "Active substance": { "type": "text" },
      "ATC code": { "type": "keyword" },
      "Company": { "type": "keyword" },
      "Status": { "type": "keyword" },
      "Authorisation number": { "type": "keyword" },
      "Country": { "type": "keyword" }
    }
  }
}
```
## Reindex austria_dataset
```bash
POST _reindex?requests_per_second=1000
{
  "source": {
    "index": "austria_dataset",
    "_source": ["Name", "Active substances", "ATC code", "Holder", "Withdrawal period", "MA number"]
  },
  "dest": {
    "index": "europe_dataset"
  },
  "script": {
    "lang": "painless",
    "source": """
      def new_doc = new HashMap();
      if (ctx._source.containsKey('Name')) {
        new_doc['Medicine name'] = ctx._source.Name;
      }
      if (ctx._source.containsKey('Active substances')) {
        new_doc['Active substance'] = ctx._source['Active substances'];
      }
      if (ctx._source.containsKey('ATC code')) {
        new_doc['ATC code'] = ctx._source['ATC code'];
      }
      if (ctx._source.containsKey('Holder')) {
        new_doc.Company = ctx._source.Holder;
      }
      if (ctx._source.containsKey('Withdrawal period')) {
        if (ctx._source['Withdrawal period'] == null) {
          new_doc.Status = 'Available';
        } else {
          new_doc.Status = ctx._source['Withdrawal period'];
        }
      } else {
        new_doc.Status = 'Available';
      }
      if (ctx._source.containsKey('MA number')) {
        new_doc['Authorisation number'] = ctx._source['MA number'];
      }
      new_doc.Country = 'Austria';
      ctx._source = new_doc;
    """
  }
}
```
## Reindex belgium_dataset
```bash
POST _reindex?requests_per_second=1000
{
  "source": {
    "index": "belgium_dataset",
    "_source": ["Medicine", "Active substance", "ATC", "Company", "Notification status", "Authorisation number"]
  },
  "dest": {
    "index": "europe_dataset"
  },
  "script": {
    "lang": "painless",
    "source": """
      def new_doc = new HashMap();
      if (ctx._source.containsKey('Medicine')) {
        new_doc['Medicine name'] = ctx._source.Medicine;
      }
      if (ctx._source.containsKey('Active substance')) {
        new_doc['Active substance'] = ctx._source['Active substance'];
      }
      if (ctx._source.containsKey('ATC')) {
        new_doc['ATC code'] = ctx._source['ATC'];
      }
      if (ctx._source.containsKey('Company')) {
        new_doc.Company = ctx._source.Company;
      }
      if (ctx._source.containsKey('Notification status')) {
        new_doc['Status'] = ctx._source['Notification status'];
      }
      if (ctx._source.containsKey('Authorisation number')) {
        new_doc['Authorisation number'] = ctx._source['Authorisation number'];
      }
      new_doc.Country = 'Belgium';
      ctx._source = new_doc;
    """
  }
}
```
## Creating a new index for with new mappings
A text field → for full-text search
A keyword subfield → for exact matching and filters
```bash
PUT europe_dataset_v2_reindexed
{
  "settings": {
    "index": {
      "number_of_shards": 1,
      "number_of_replicas": 0
    }
  },
  "mappings": {
    "properties": {
      "ATC code": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      },
      "Active substance": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      },
      "Authorisation number": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      },
      "Company": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      },
      "Country": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      },
      "Medicine name": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      },
      "Status": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      }
    }
  }
}

POST _reindex
{
  "source": {
    "index": "europe_dataset"
  },
  "dest": {
    "index": "europe_dataset_v2_reindexed"
  }
}
```
## US Data - Filtered with relevant fields 

```bash
PUT /usa_dataset
{
  "settings": {
    "index": {
      "number_of_shards": 3,
      "number_of_replicas": 1
    }
  },
  "mappings": {
    "properties": {
      "spl_product_data_elements": { "type": "text" },
      "purpose": { "type": "text" },
      "indications_and_usage": { "type": "text" },
      "active_ingredient": { "type": "text" },
      "dosage_and_administration": { "type": "text" },
      "dosage_forms_and_strengths": { "type": "text" },
      "contraindications": { "type": "text" },
      "adverse_reactions": { "type": "text" },
      "use_in_specific_populations": { "type": "text" },
      "storage_and_handling": { "type": "text" },
      "openfda.application_number": { "type": "keyword" },
      "openfda.manufacturer_name": { "type": "keyword" },
      "openfda.route": { "type": "keyword" },
      "openfda.substance_name": { "type": "keyword" },
      "openfda.generic_name": { "type": "keyword" },
      "openfda.brand_name": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
      "openfda.package_ndc": { "type": "keyword" },
      "openfda.rxcui": { "type": "keyword" },
      "source": { "type": "text" }
    }
  }
}
```

## Reindex usa_dataset
```bash
POST _reindex?requests_per_second=1000
{
  "source": {
    "index": "fda_drug_labels",
    "_source": [
      "spl_product_data_elements",
      "purpose",
      "indications_and_usage",
      "active_ingredient",
      "dosage_and_administration",
      "dosage_forms_and_strengths",
      "contraindications",
      "adverse_reactions",
      "use_in_specific_populations",
      "storage_and_handling",
      "openfda.application_number",
      "openfda.manufacturer_name",
      "openfda.route",
      "openfda.substance_name",
      "openfda.generic_name",
      "openfda.brand_name",
      "openfda.package_ndc",
      "openfda.rxcui"
    ]
  },
  "dest": {
    "index": "usa_dataset"
  },
  "script": {
    "lang": "painless",
    "source": """
      def new_doc = new HashMap();
      for (def entry : ctx._source.entrySet()) {
        new_doc[entry.getKey()] = entry.getValue();
      }
      new_doc['source'] = 'USA FDA';
      ctx._source = new_doc;
    """
  }
}
```

## Reindex if only openfda exists in document
```bash
POST _reindex
{
  "source": {
    "index": "usa_dataset",
    "query": {
      "exists": {
        "field": "openfda"
      }
    }
  },
  "dest": {
    "index": "usa_dataset_filtered"
  }
}
```
## For semantic search, create combined_text field
```bash
PUT _ingest/pipeline/combine-text-pipeline_test
{
  "description": "Combine fields for semantic search embedding using SapBERT",
  "processors": [
    {
      "script": {
        "lang": "painless",
        "source": """
          String combined = "";

          if (ctx.containsKey('indications_and_usage') && ctx.indications_and_usage != null) {
            combined += ctx.indications_and_usage + " ";
          }
          if (ctx.containsKey('purpose') && ctx.purpose != null) {
            combined += ctx.purpose + " ";
          }
          if (ctx.containsKey('dosage_and_administration') && ctx.dosage_and_administration != null) {
            combined += ctx.dosage_and_administration + " ";
          }
          if (ctx.containsKey('active_ingredient') && ctx.active_ingredient != null) {
            combined += ctx.active_ingredient + " ";
          }
          if (ctx.containsKey('openfda') && ctx.openfda != null) {
            if (ctx.openfda.containsKey('substance_name') && ctx.openfda.substance_name != null) {
              combined += ctx.openfda.substance_name + " ";
            }
          }

          ctx.combined_text = combined.trim();
        """
      }
    }
  ]
}

POST _reindex
{
  "source": {
    "index": "usa_dataset_filtered"
  },
  "dest": {
    "index": "usa_dataset_filtered_v2",
    "pipeline": "combine-text-pipeline_test"
  }
}

```
## Mapping for index to include knn_vector field
```bash
PUT usa_dataset_filtered_embeddings_generic
{
  "settings": {
    "index": { "knn": true, "number_of_shards": 1, "number_of_replicas": 0 }
  },
  "mappings": {
    "properties": {
      "search_vector": {
        "type": "knn_vector",
        "dimension": 768,
        "method": {
          "name": "hnsw", "engine": "nmslib", "space_type": "cosinesimil"
        }
      }
    }
  }
}
```

---

## Embedding Pipeline

Script: `US_Vector_Embeddings.py`

- Uses `SentenceTransformer (DistilRoBERTa)`
- Pulls from `usa_dataset_filtered_v2`
- Pushes embeddings to `usa_dataset_filtered_embeddings_generic`

---
## RXCUI to ATC4 Mapping

Script: `rxcui_to_atc4.py`

- Extracts unique `RXCUI` identifiers from documents with `openfda` fields
- Queries the **RxNav API** to retrieve corresponding **ATC Level 4 codes**
- Outputs a mapping file: `rxcui_to_atc4_mapping.json`
- Used during semantic search to enhance interpretability and align US products to global standards

## Streamlit Search App

Script: `Streamlit_Application.py`

Features:
- Europe keyword search with boosted `ATC code` wildcard for ATC5 retrieval with ATC4
- US semantic search using DistilRoBERTa and mapped ATC4 via `RxNav`

---





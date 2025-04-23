# Cross-Reference Code Mapping System
The objective is to dynamically map medical products across terminologies and regulatory frameworks.


## 1. architecture

![image](https://github.com/user-attachments/assets/d6cc63d1-da01-4dc7-8e6a-07816aa2afd0)

**Application layer**

**Streamlit**: an open-source Python library that allows data scientists and machine-learning engineers to quickly build and share interactive web applications for data exploration and visualization. It lets you turn your Python scripts into shareable web apps in minutes.
  Deployed on a VM or in OCI Function.

**Data Persistence**

**OpenSearch**: a scalable, open-source search and analytics suite derived from Elasticsearch and Kibana. It enables users to store, search, analyze, and visualize large volumes of data in real time for use cases like log analytics, application monitoring, and enterprise search.

**OCI Object Storage**: a highly scalable, durable, and cost-effective cloud storage service for storing unstructured data of any type. It allows you to store and retrieve data directly from the internet or within the OCI cloud platform, offering virtually unlimited storage capacity and high durability.

**Data Integration**

**OpenSearch Data Prepper**: a server-side data collector for OpenSearch that helps you ingest, filter, transform, enrich, and route data at scale before it's indexed. It acts as a processing pipeline that sits between your data sources and your OpenSearch cluster.
  
**Search engine**

**OpenSearch**: a scalable, open-source search and analytics suite derived from Elasticsearch and Kibana. It enables users to store, search, analyze, and visualize large volumes of data in real time for use cases like log analytics, application monitoring, and enterprise search.

**OCI API Gateway**: a fully managed service that enables you to publish, secure, manage, and monitor APIs. It acts as a single entry point for accessing multiple backend services, including OCI Functions, compute instances, and other HTTP endpoints.


## 2. Create an OCI postgreSQL database and OCI OpenSearch cluster
- Set up default VCN with private and public subnet, open ports for OCI OpenSearch (OSD:5601, DB: 9200)
- Create an OCI OpenSearch cluster using the VCM created above as per this [documentation](https://docs.oracle.com/en-us/iaas/Content/search-opensearch/Tasks/creatingsearchclusters.htm).

## 3. Import data from source
- Europe - [European Medecines Agency](https://www.ema.europa.eu/en/homepage)
- Austria - [Austrian medicinal product index](https://aspregister.basg.gv.at/aspregister/faces/aspregister.jspx)
- Belgium - [Medicinal products for human use | Medicinal product database](https://medicinesdatabase.be/human-use)
- USA - [Federal Drug Administration](https://open.fda.gov/)

  
## 4. Data Model

**Keyword search**

![arch_design-europe_data_model](https://github.com/user-attachments/assets/64e89d82-3ecc-4c21-bb61-d7f4012df70f)

**Semantic search**

![image](https://github.com/user-attachments/assets/07224433-ddb4-42cd-97e8-f70579ded057)

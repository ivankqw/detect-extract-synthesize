# Detect-Extract-Synthesize: Knowledge Retrieval from Visually Rich Documents

## Project Overview
This repository contains the source code for my Final Year Project (FYP) focused on an end-to-end framework for knowledge retrieval from visually rich documents, with applications in the venture capital domain.

## B.Comp. Dissertation

**An End-to-end Framework for Knowledge Retrieval from Visual Documents with Applications in Venture Capital**

By  
Koh Quan Wei Ivan

Department of Information Systems and Analytics  
School of Computing  
National University of Singapore  
2023/2024

## Citation
If you use this work in your research or project, please cite:

```
Koh, Q. W. I. (2024). An End-to-end Framework for Knowledge Retrieval from Visual Documents with Applications in Venture Capital. B.Comp. Dissertation, Department of Information Systems and Analytics, School of Computing, National University of Singapore.
```

For any inquiries, please contact: ivankohquanwei@gmail.com

## Abstract
This dissertation presents an end-to-end framework for knowledge retrieval from visually rich documents, focusing on applications in the venture capital domain. The framework addresses the challenges faced by venture capital professionals in manually analysing pitch decks during the deal-sourcing process. It comprises three phases: Detection, Extraction, and Synthesis.

The Detection Phase introduces the IIIT-OSV-Charts dataset, a novel combination of the IIIT-AR-13K dataset and a proprietary dataset from Openspace Ventures. State-of-the-art YOLO object detection models are employed to accurately identify and localize chart instances within pitch decks.

In the Extraction Phase, the Set-of-Marks prompting strategy is adapted for grounded zero-shot understanding of charts using large multimodal models. Relevant insights are extracted and stored in a vector database for efficient retrieval.

The Synthesis Phase develops a Retrieval-Augmented Generation pipeline tailored to generate comprehensive responses to frequently asked questions crucial for decision-making. This pipeline is integrated with a user-friendly web application.

## Key Achievements
- Development of a three-phase approach: Detection, Extraction, and Synthesis
- Creation of the IIIT-OSV-Charts dataset for chart detection in venture capital documents
- Adaptation of the Set-of-Marks prompting strategy for chart understanding
- Development of a tailored Retrieval-Augmented Generation (RAG) pipeline
- Integration with a user-friendly web application for multi-turn conversations

## Limitations
The current implementation relies heavily on closed-source models from providers such as OpenAI and Anthropic, which poses risks in terms of reliability and scalability. Future work should focus on reducing dependence on closed-source models and exploring alternative solutions.

## Setup and Installation

### GCP setup
```bash
gcloud auth login
gcloud config set project $GCP_PROJECT_ID
```

### Frontend Start
```bash
cd frontend
npm run dev 
```

### Backend Start
```bash
cd backend
python main.py
```

### Vector DB Start
```bash
cd backend 
source vector_db_start.sh
```

```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

### Dockerise Backend

```bash
cd backend 
docker build -t fyp-backend .

docker run -p 80:80 \
-e OPENAI_API_TOKEN="" \
-e APP_HTTP_HOST="127.0.0.1" \
-e APP_HTTP_PORT="8000" \
-e APP_HTTP_URL="http://${APP_HTTP_HOST}:${APP_HTTP_PORT}" \
-e PGURL="" \
-e QDRANT_URL="" \
-e QDRANT_API_KEY="" \
fyp-backend

docker tag fyp-backend gcr.io/$GCP_PROJECT_ID/fyp-backend:v1

docker push gcr.io/$GCP_PROJECT_ID/fyp-backend:v1
```
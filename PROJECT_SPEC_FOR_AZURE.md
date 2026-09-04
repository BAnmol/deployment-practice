# 🛒 OWASP Juice Shop (Indian Edition) - Comprehensive Azure Deployment Specification

> **Purpose of this document:**  
> This specification provides the complete technical architecture, container topology, file map, API schema, environment configuration, and step-by-step Azure deployment options for deploying this full-stack Python + FastAPI + ChromaDB + AI application to **Microsoft Azure**.

---

## 1. Executive Summary & Architecture Overview

### Project Description
A full-stack, containerized e-commerce application inspired by OWASP Juice Shop, localized for the Indian market (INR ₹ pricing, UPI/QR, RuPay, NetBanking) with an integrated AI Shopping Assistant (**RasAI**) powered by RAG (Retrieval-Augmented Generation) using ChromaDB vector database and LLM APIs (OpenRouter / Groq).

### High-Level Architecture Diagram
```
                              Internet / User Browser
                                        │
                                        ▼ HTTPS (Port 443 / 80)
                     ┌──────────────────────────────────────┐
                     │     Azure Ingress / Reverse Proxy    │
                     │  (App Service / Container App / VM)  │
                     └──────────────────┬───────────────────┘
                                        │ Port 8000
                                        ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │                      DOCKER COMPOSE / CONTAINER NETWORK                │
    │                                                                        │
    │  ┌───────────────────────────────┐   Internal HTTP   ┌──────────────┐  │
    │  │       Service: `web`          │ ────────────────> │  `chromadb`  │  │
    │  │  FastAPI + Uvicorn            │   Port 8000       │  Vector DB   │  │
    │  │  SQLite DB (`shop.db`)        │                   │  Store       │  │
    │  │  HTML5 / CSS / Vanilla JS UI  │                   └──────┬───────┘  │
    │  └──────────────┬────────────────┘                          │          │
    └─────────────────┼───────────────────────────────────────────┼──────────┘
                      │ Outbound HTTPS API Calls                  │
                      ▼                                           ▼
             OpenRouter / LLM APIs                     Persistent Azure Volume
       (Gemini / Claude / Llama 3)                     (Storage Share / Disk)
```

---

## 2. Technology Stack & Dependencies

| Component | Technology / Library | Description |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI (`0.100.0+`), Uvicorn | High-performance asynchronous REST API |
| **ORM & Database** | SQLAlchemy (`2.0.0+`), SQLite (migratable to Azure PostgreSQL) | Relational database holding catalog, users, baskets, reviews, orders |
| **Vector Database** | ChromaDB (`chromadb/chroma:latest` / `chromadb>=0.5.0`) | Semantic knowledge store for product search, reviews & promo policies |
| **AI / RAG Engine** | OpenRouter API / Groq API (`httpx`) | Generative AI assistant (RasAI) answering shopper queries |
| **Authentication** | JWT (`PyJWT`), `passlib[bcrypt]` / `hashlib` | Customer registration, login, token authentication, guest sessions |
| **Frontend** | Vanilla HTML5, Modern Responsive CSS, JavaScript (ES6+) | Single-page e-commerce storefront, shopping cart, dummy payment gateway |
| **Containerization** | Docker, Multi-stage Dockerfile, Docker Compose | Two-service orchestration (`web` + `chromadb`) |

---

## 3. Project Directory & File Map

```
Deployment Project/
├── Dockerfile                  # Python 3.11-slim container blueprint for web service
├── docker-compose.yml          # Multi-container orchestrator (web + chromadb + volumes)
├── .dockerignore               # Ignores venv, git, local cache, and IDE configs
├── requirements.txt            # Python production dependencies
├── .env                        # Secret environment variables (API keys)
│
├── main.py                     # FastAPI application entry point, lifecycle, and REST routing
├── database.py                 # SQLAlchemy engine and session dependency
├── models.py                   # ORM models (Product, User, BasketItem, Review, Order, Coupon)
├── schemas.py                  # Pydantic validation schemas for API requests & responses
├── auth.py                     # Password hashing, JWT creation & auth dependency injection
├── seed_data.py                # Database seeder populating Indian localized juice products & reviews
├── ai_service.py               # RasAI chatbot logic with prompt injection protection & RAG injection
├── rag_service.py              # ChromaDB vector indexing and similarity search with retry logic
│
├── static/                     # Frontend static assets
│   ├── index.html              # Main storefront & catalog UI
│   ├── login.html              # Customer authentication UI
│   ├── css/
│   │   └── styles.css          # Modern dark-themed CSS design system
│   ├── js/
│   │   └── app.js              # Frontend client state, cart management, dummy checkout, AI chat
│   └── images/                 # SVG product icons and branding logos
│
└── tests/
    ├── test_app.py             # Pytest suite for catalog, cart, and authentication
    ├── test_ai.py              # Pytest suite for AI assistant endpoints
    └── test_rag.py             # Pytest suite for ChromaDB indexing and vector search
```

---

## 4. Key Configuration Files

### 📄 `Dockerfile`
```dockerfile
# Use official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/categories || exit 1

# Start the application with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### 📄 `docker-compose.yml`
```yaml
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: juice_shop_web
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - CHROMA_HOST=chromadb
      - CHROMA_PORT=8000
      - PORT=8000
    depends_on:
      - chromadb
    volumes:
      - .:/app
    restart: unless-stopped

  chromadb:
    image: chromadb/chroma:latest
    container_name: juice_shop_chromadb
    ports:
      - "8002:8000"
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE
      - ALLOW_RESET=TRUE
    volumes:
      - chroma_data:/chroma/chroma
    restart: unless-stopped

volumes:
  chroma_data:
```

---

### 📄 `requirements.txt`
```text
fastapi>=0.100.0
uvicorn[standard]>=0.22.0
sqlalchemy>=2.0.0
pydantic[email]>=2.0.0
email-validator>=2.0.0
PyJWT>=2.8.0
python-dotenv>=1.0.0
httpx>=0.24.0
python-multipart>=0.0.6
chromadb>=0.5.0
pytest>=7.0.0
```

---

## 5. Environment Variables & Secrets Required

| Variable Name | Required | Default / Example Value | Description |
| :--- | :---: | :--- | :--- |
| `OPENROUTER_API_KEY` | **Yes** (for AI) | `sk-or-v1-...` | API Key for OpenRouter LLM inference |
| `GROQ_API_KEY` | Optional | `gsk_...` | Alternate fast LLM provider |
| `CHROMA_HOST` | **Yes** | `chromadb` (Docker) / `localhost` | Hostname of ChromaDB vector store |
| `CHROMA_PORT` | **Yes** | `8000` (Docker internal) / `8002` | Port of ChromaDB instance |
| `PORT` | Optional | `8000` | Port for FastAPI / Uvicorn server |
| `SECRET_KEY` | Optional | `juice-shop-secret-jwt-key` | Secret key for signing JWT auth tokens |
| `DATABASE_URL` | Optional | `sqlite:///./shop.db` | Connection string (can point to Azure PostgreSQL) |

---

## 6. Target Azure Deployment Options

When deploying this project to Microsoft Azure, choose one of the following 3 architectural paths:

### Option A: Azure App Service for Containers (Multi-Container / Docker Compose) — **Recommended for Quickest Setup**
* **Azure Service**: Azure App Service (Linux B1 or P1v3 tier)
* **Mechanism**: Deploy directly by providing `docker-compose.yml` and container images hosted on Azure Container Registry (ACR) or Docker Hub.
* **Persistent Storage**: Azure App Service path mapping or Azure Files storage mounted to `/chroma/chroma`.

### Option B: Azure Container Apps (ACA) — **Recommended for Modern Cloud-Native & Serverless**
* **Azure Service**: Azure Container Apps Environment
* **Mechanism**: Two microservice container apps (`web-app` and `chromadb-app`) deployed within the same internal ACA environment with internal DNS resolution.
* **Scaling**: Scales to zero or scales on demand based on HTTP traffic.
* **Storage**: Azure Files volume mount for persistent vector database storage.

### Option C: Azure Virtual Machine (Ubuntu 22.04 LTS) — **Recommended for Full Control & Lowest Flat Cost**
* **Azure Service**: Standard B2s (2 vCPU, 4GB RAM) Ubuntu VM
* **Mechanism**:
  1. Install Docker & Docker Compose via Cloud-Init.
  2. Clone git repository.
  3. Configure `.env` file.
  4. Run `docker compose up -d`.
  5. Configure Nginx with free Let's Encrypt SSL (`certbot`) for HTTPS on custom domain.

---

## 7. Azure Deployment Step-by-Step Blueprint (Azure CLI Reference)

### Step 1: Create Azure Resource Group & Container Registry (ACR)
```bash
# Login to Azure
az login

# Create a Resource Group
az group create --name rg-juiceshop-prod --location centralindia

# Create Azure Container Registry
az acr create --resource-group rg-juiceshop-prod --name acrjuiceshopprod --sku Basic --admin-enabled true

# Login to ACR
az acr login --name acrjuiceshopprod
```

### Step 2: Build & Push Docker Image to Azure Container Registry
```bash
# Build and tag image
docker build -t acrjuiceshopprod.azurecr.io/juice-shop-web:v1.0 .

# Push image to ACR
docker push acrjuiceshopprod.azurecr.io/juice-shop-web:v1.0
```

### Step 3: Deploy on Azure App Service with Docker Compose
```bash
# Create App Service Plan (Linux)
az appservice plan create \
    --name plan-juiceshop \
    --resource-group rg-juiceshop-prod \
    --sku B1 \
    --is-linux

# Create Multi-Container Web App
az webapp create \
    --resource-group rg-juiceshop-prod \
    --plan plan-juiceshop \
    --name juiceshop-indian-app \
    --multicontainer-config-type COMPOSE \
    --multicontainer-config-file docker-compose.yml

# Set Environment Variables in App Service
az webapp config appsettings set \
    --resource-group rg-juiceshop-prod \
    --name juiceshop-indian-app \
    --settings \
        OPENROUTER_API_KEY="your-openrouter-key" \
        CHROMA_HOST="chromadb" \
        CHROMA_PORT="8000" \
        WEBSITES_PORT="8000"
```

---

## 8. Verification & Post-Deployment Health Checks

After deployment, verify the endpoints:

1. **Storefront Home**: `https://<your-azure-app>.azurewebsites.net/`
2. **Interactive Swagger Docs**: `https://<your-azure-app>.azurewebsites.net/docs`
3. **Health Check Endpoint**: `https://<your-azure-app>.azurewebsites.net/api/categories`
4. **Vector Knowledge Reindex**: `POST https://<your-azure-app>.azurewebsites.net/api/ai/reindex`
5. **AI Shopping Assistant**: `POST https://<your-azure-app>.azurewebsites.net/api/ai/chat`

---

## 9. Summary for AI Deployment Prompts

> **Copy & paste this prompt into any AI agent:**  
> *"I have a multi-container full-stack application (FastAPI + ChromaDB + SQLite + HTML/JS frontend) specified in the provided markdown file. Please generate complete step-by-step instructions, Terraform/Bicep infrastructure-as-code scripts, and a GitHub Actions `.github/workflows/deploy.yml` pipeline to automatically build, push to ACR, and deploy to Azure App Service / Azure Container Apps with persistent storage and HTTPS."*

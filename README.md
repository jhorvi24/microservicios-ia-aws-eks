# 🧠 AI Sentiment Analysis — Microservices on Amazon EKS

> Plataforma de análisis de sentimientos en tiempo real construida con microservicios, desplegada sobre **Amazon EKS** con imágenes en **ECR** y persistencia en **RDS PostgreSQL**. Diseñada para ser reproducible, escalable y lista para pipelines de CI/CD.

---

## 📌 Descripción

Este proyecto implementa una arquitectura de microservicios para inferencia de IA sobre **Amazon EKS (Elastic Kubernetes Service)**. El sistema recibe texto de usuario, lo clasifica como positivo o negativo usando el modelo **DistilBERT** (HuggingFace), persiste los resultados en una base de datos PostgreSQL administrada en RDS, y los expone en un dashboard interactivo construido con Streamlit.

Toda la infraestructura se gestiona con `eksctl`, los contenedores se almacenan en **Amazon ECR**, y el despliegue en Kubernetes se realiza con manifiestos declarativos.

---

## 🏗️ Arquitectura

```
                        ┌─────────────────────────────────────────┐
                        │              Amazon EKS Cluster          │
                        │                                          │
  Usuario ──► 🌐 LB ──► │  [Dashboard :8501]                       │
                        │       │                                  │
                        │       ▼                                  │
                        │  [NLP Service :5000]  ◄── DistilBERT     │
                        │       │                                  │
                        │       ▼                                  │
                        │  [Data Service :8001] ──► 🗄️ RDS PostgreSQL│
                        └─────────────────────────────────────────┘
```

| Servicio | Tecnología | Exposición |
|---|---|---|
| `dashboard` | Streamlit | LoadBalancer (público) |
| `nlp-service` | Flask + DistilBERT | ClusterIP (interno) |
| `data-service` | Flask + SQLAlchemy | ClusterIP (interno) |

---

## ✅ Requisitos previos

Asegúrate de tener instaladas y configuradas las siguientes herramientas:

| Herramienta | Versión recomendada | Descripción |
|---|---|---|
| [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) | v2+ | Interacción con servicios AWS |
| [eksctl](https://eksctl.io/) | v0.180+ | Creación y gestión del cluster EKS |
| [kubectl](https://kubernetes.io/docs/tasks/tools/) | v1.29+ | Gestión de recursos Kubernetes |
| [Docker](https://docs.docker.com/get-docker/) | v24+ | Build y push de imágenes |
| Git | v2+ | Clonar el repositorio |

Configura tu perfil de AWS antes de comenzar:

```bash
aws configure --profile aws-academy
```

---

## 🚀 Guía de inicio rápido

### 1️⃣ Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd <nombre-del-repositorio>
```

### 2️⃣ Crear el cluster EKS

```bash
eksctl create cluster -f eks/cluster.yml
```

> ⏳ Este proceso tarda aproximadamente 15-20 minutos. Al finalizar, `kubectl` quedará configurado automáticamente para apuntar al nuevo cluster.

Verifica que el cluster esté activo:

```bash
kubectl get nodes
```

### 3️⃣ Crear los repositorios en Amazon ECR

```bash
bash scripts/create-ecr.sh
```

Esto crea los repositorios `nlp-service`, `data-service` y `dashboard` en ECR.

### 4️⃣ Construir y subir las imágenes Docker a ECR

```bash
bash scripts/push-ecr.sh
```

El script realiza automáticamente:
- Login a ECR
- `docker build` de cada servicio
- `docker tag` y `docker push` al registro

### 5️⃣ Crear la base de datos PostgreSQL en RDS

```bash
bash scripts/create-rds.sh
```

> 📋 Al finalizar, el script imprime el **endpoint** de la base de datos. Si el endpoint difiere del configurado, actualiza el valor de `DATABASE_URL` en `k8s/data-service.yaml` antes de continuar.

### 6️⃣ Desplegar los microservicios en Kubernetes

```bash
kubectl apply -f k8s/
```

Verifica que todos los pods estén en estado `Running`:

```bash
kubectl get pods
kubectl get svc
```

El dashboard estará disponible en la `EXTERNAL-IP` del servicio `dashboard`:

```bash
kubectl get svc dashboard
# Accede en: http://<EXTERNAL-IP>
```

---

## 📁 Estructura del proyecto

```
.
├── 📄 eks/
│   └── cluster.yml              # Configuración del cluster EKS (eksctl)
│
├── 📄 k8s/
│   ├── dashboard.yaml           # Deployment + Service del dashboard (LoadBalancer)
│   ├── nlp-service.yaml         # Deployment + Service del NLP service (ClusterIP)
│   └── data-service.yaml        # Deployment + Service del data service (ClusterIP)
│
├── 📄 Services/
│   ├── dashboard/
│   │   ├── app.py               # UI Streamlit — ingreso de texto y visualización
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── nlp-service/
│   │   ├── app.py               # API Flask — inferencia con DistilBERT
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── data-service/
│       ├── app.py               # API Flask — CRUD de resultados
│       ├── database.py          # Inicialización de SQLAlchemy
│       ├── models.py            # Modelo SentimentResult
│       ├── Dockerfile
│       └── requirements.txt
│
├── 📄 scripts/
│   ├── create-ecr.sh            # Crea repositorios ECR en AWS
│   ├── push-ecr.sh              # Build y push de imágenes Docker a ECR
│   └── create-rds.sh            # Crea instancia RDS PostgreSQL en la VPC del cluster
│
└── 📄 README.md
```

---

## 🛠️ Scripts de automatización

| Script | Descripción |
|---|---|
| `scripts/create-ecr.sh` | Crea los tres repositorios ECR (`nlp-service`, `data-service`, `dashboard`) si no existen. |
| `scripts/push-ecr.sh` | Autentica Docker contra ECR, construye las imágenes desde cada `Dockerfile` y las sube con el tag `latest`. |
| `scripts/create-rds.sh` | Crea un Security Group, un DB Subnet Group y una instancia RDS PostgreSQL `db.t3.micro` dentro de la VPC del cluster EKS. Imprime el connection string al finalizar. |

Todos los scripts usan el perfil AWS `aws-academy` y la región `us-east-1`. Puedes modificar estas variables al inicio de cada archivo.

---

## ⚙️ Variables de entorno

| Variable | Servicio | Valor por defecto |
|---|---|---|
| `NLP_SERVICE_URL` | dashboard | `http://nlp-service:5000` |
| `STORAGE_SERVICE_URL` | dashboard | `http://data-service:8001` |
| `BD_SERVICE_URL` | nlp-service | `http://data-service:8001` |
| `DATABASE_URL` | data-service | Connection string de RDS |

---

## 🔌 API Reference

**NLP Service** — `nlp-service:5000`

```http
GET  /health
POST /analyze   Body: { "text": "I love this product" }
                Response: { "sentiment": "positive", "confidence": 0.9987 }
```

**Data Service** — `data-service:8001`

```http
GET  /health
POST /results              # Guarda un resultado de análisis
GET  /results?skip=0&limit=100  # Lista resultados paginados
GET  /results/<id>         # Obtiene un resultado por ID
GET  /stats                # Estadísticas: total, positivos, negativos
```

---

## 📝 Notas técnicas

- 🔁 **CI/CD ready**: La separación entre scripts de infraestructura, manifiestos de K8s e imágenes Docker permite integrar este proyecto fácilmente en pipelines de GitHub Actions, GitLab CI o AWS CodePipeline.
- 🧪 **Entorno reproducible**: El archivo `eks/cluster.yml` define toda la configuración del cluster de forma declarativa, lo que facilita recrear el entorno en cualquier cuenta AWS.
- 🤖 **Modelo de IA**: El NLP service usa `distilbert-base-uncased-finetuned-sst-2-english` de HuggingFace, descargado automáticamente en el primer arranque del contenedor. Se recomienda usar un volumen persistente o pre-bake el modelo en la imagen para entornos de producción.
- 🔒 **Seguridad**: La base de datos RDS no es accesible públicamente (`--no-publicly-accessible`). Solo los pods dentro de la VPC del cluster pueden conectarse al puerto 5432.

---

## 🧹 Limpieza de recursos

Para evitar costos innecesarios, elimina los recursos cuando termines:

```bash
# Eliminar deployments de Kubernetes
kubectl delete -f k8s/

# Eliminar el cluster EKS
eksctl delete cluster -f eks/cluster.yml

# Eliminar la instancia RDS (desde la consola AWS o con AWS CLI)
aws rds delete-db-instance --db-instance-identifier sentiments-db \
  --skip-final-snapshot --profile aws-academy --region us-east-1
```

---

## 🧰 Stack tecnológico

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![Streamlit](https://img.shields.io/badge/Streamlit-1.29-red?logo=streamlit)
![HuggingFace](https://img.shields.io/badge/HuggingFace-DistilBERT-yellow?logo=huggingface)
![Docker](https://img.shields.io/badge/Docker-24-blue?logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-1.35-blue?logo=kubernetes)
![AWS EKS](https://img.shields.io/badge/AWS-EKS-orange?logo=amazonaws)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-blue?logo=postgresql)

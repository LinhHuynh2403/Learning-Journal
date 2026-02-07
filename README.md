# Learning-Journal-AI

An AI-powered journal that helps developers reflect on their problem-solving process and improve their learning strategy.

## Status
🚧 In progress

## Goals
- Build a meaningful AI-assisted learning tool
- Showcase full-stack + AI integration skills

---

## Getting Started

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd Learning-Journal

``` 
### 2. Creating a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
# On Windows:
# venv\Scripts\activate
```

### 3. Upgrade pip
```bash
pip install --upgrade pip
```

### 4. Install dependencies
```bash
pip install -r requirements.txt

# Mac M1/M2 users, if the psycopg2-binary fails to build, run: 

ARCHFLAGS="-arch x86_64" pip install psycopg2-binary
``` 

### 5. Setup environment variables
create a .env file in the root of backend/
```bash
DATABASE_URL=postgresql://<username>:<password>@localhost:5432/<db_name>
OPENAI_API_KEY=<your_openai_api_key>
``` 

### 6. Run the backend
```bash 
uvicorn backend.main:app --reload
```


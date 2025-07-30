
# **AI-Powered Educational Chatbot with RAG Capabilities**

This project is an advanced educational chatbot system that combines multiple AI technologies for intelligent student assistance. The system leverages **Rasa** for natural language understanding, **OpenAI** for advanced language processing, **LangChain** for building RAG (Retrieval-Augmented Generation) pipelines, **PostgreSQL** for robust data management, and **Nginx** for secure endpoint management. The RAG system enables the chatbot to provide contextually relevant answers by retrieving information from educational documents and materials.

---

## **Project Setup**

### **1. Clone the Repository**
Clone this repository to your local machine:
```bash
git clone https://github.com/your-repository-url.git
cd your-repository
```

---

### **2. Environment Variables**

The project relies on a `.env` file to define the necessary configuration values. Below is an example of what your `.env` file should look like:

#### **PostgreSQL Configuration**
| Variable      | Description                                 | Example Value          |
|---------------|---------------------------------------------|------------------------|
| `DB_HOST`     | Hostname or IP of the PostgreSQL server     | `postgres`            |
| `DB_USER`     | Username for PostgreSQL authentication      | `postgres`            |
| `DB_PASSWORD` | Password for PostgreSQL authentication      | `mysecretpassword`    |
| `DB_PORT`     | Port for PostgreSQL (default is 5432)       | `5432`                |
| `DB_NAME`     | Name of the database to use                | `ice`                 |

#### **pgAdmin Configuration**
| Variable               | Description                                 | Example Value          |
|------------------------|---------------------------------------------|------------------------|
| `PGADMIN_DEFAULT_EMAIL` | Default email for pgAdmin login             | `example@gmail.com`   |
| `PGADMIN_DEFAULT_PASSWORD` | Default password for pgAdmin login         | `mysupersecret`        |

#### **Service URLs Configuration**
| Variable             | Description                                 | Example Value            |
|----------------------|---------------------------------------------|--------------------------|
| `NGINX_SERVER_URL`   | Public-facing URL for Nginx                 | `http://172.17.93.85:8888` |
| `RASA_SERVER_URL`    | URL of the Rasa server                      | `http://172.17.93.85:5005` |
| `AUTH_SERVER_URL`    | URL of the authentication server            | `http://172.17.93.85:5000` |

#### **AI Services Configuration**
| Variable             | Description                                 | Example Value            |
|----------------------|---------------------------------------------|--------------------------|
| `OPENAI_API_KEY`     | OpenAI API key for language processing     | `sk-proj-...`            |
| `RASA_CORS`          | CORS settings for Rasa server              | `*`                      |

#### Example `.env` File
```env
# PostgreSQL Configuration
DB_HOST=postgres
DB_USER=postgres
DB_PASSWORD=mysecretpassword
DB_PORT=5432
DB_NAME=ice

# pgAdmin Configuration
PGADMIN_DEFAULT_EMAIL=example@gmail.com
PGADMIN_DEFAULT_PASSWORD=mysupersecret

# Service URLs
NGINX_SERVER_URL=http://172.17.93.85:8888
RASA_SERVER_URL=http://172.17.93.85:5005
AUTH_SERVER_URL=http://172.17.93.85:5000

# AI Services
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
RASA_CORS=*
```

---

### **3. Setting Up the Environment**

1. Copy the example `.env` file to create your configuration:
   ```bash
   cp .env_example .env
   ```

2. Edit the `.env` file with your specific values.

---

### **4. Services Architecture**

The system consists of multiple interconnected services:

#### **Core Services**
- **PostgreSQL Database**: Stores user data, course information, and chat history
- **pgAdmin Interface**: Web-based database management tool
- **Authentication Service**: Handles user login and session management
- **Nginx Reverse Proxy**: Load balancing and secure endpoint management

#### **AI & NLP Services**
- **Rasa Server**: Core conversational AI engine for intent recognition and dialogue management
- **Rasa Actions**: Custom action server for database queries and business logic
- **RAG Service**: Retrieval-Augmented Generation using OpenAI and LangChain for document-based Q&A

#### **Running with Docker**
Start all services with Docker Compose:
```bash
docker-compose up --build
```

This orchestrates the entire microservices architecture automatically.

---

### **5. Securing Nginx Endpoints**
To secure your Nginx endpoints:
1. Use HTTP Basic Authentication with a username and password.
2. Set up your `.htpasswd` file:
   ```bash
   sudo htpasswd -c /etc/nginx/.htpasswd your_username
   ```
3. Configure the Nginx server block with the following:
   ```nginx
   auth_basic "Restricted Access";
   auth_basic_user_file /etc/nginx/.htpasswd;
   ```

---

### **6. Accessing the Services**
- **pgAdmin**: Navigate to `http://HOST:8081` and log in with the `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD`.
- **Chatbot Interface**: Interact with the AI chatbot at `http://<NGINX_SERVER_URL>/bot`.
- **Authentication**: User login and registration at `http://<AUTH_SERVER_URL>`.
- **RAG Service**: Document-based Q&A API at `http://HOST:8000/get_context`.
- **Database**: Manage your PostgreSQL database through pgAdmin.

---

### **7. Testing and Debugging**

- To test Nginx endpoint security:
  ```bash
  curl -u your_username http://<NGINX_SERVER_URL>/
  ```

- To debug Rasa:
  ```bash
  rasa shell
  ```

---

### **8. Database Management**

The project includes a comprehensive database migration utility built with **SQLAlchemy** and **Alembic**.

#### **Quick Start**
```bash
# Navigate to database directory
cd database

# Install dependencies
pip install -r requirements.txt

# Initialize database with tables and seed data
python manage.py init
```

#### **Available Commands**
```bash
# Run pending migrations
python manage.py migrate

# Create new migration
python manage.py new-migration "Add user preferences table"

# Reset database (⚠️ DESTRUCTIVE!)
python manage.py reset

# Show help
python manage.py help
```

#### **Features**
- **Automated database creation**: Creates PostgreSQL database if it doesn't exist
- **Version-controlled migrations**: Track and manage schema changes over time
- **Seed data management**: Populate database with initial academic data from CSV files
- **Type-safe models**: SQLAlchemy models with relationships and validation
- **Performance optimized**: Includes indexes for common query patterns

For detailed information about the database schema and models, see `database/README.md`.

---

### **9. Contribution**
No contributions are accepted since this is a thesis related project. Feel free to contact me at senountanikos@gmail.com for any inquiries.

---

### **10. License**
This project is licensed under the MIT License. See the `LICENSE` file for details.

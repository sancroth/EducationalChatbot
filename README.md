
# **Educational Chatbot with PostgreSQL, pgAdmin, and Nginx**

This project is an educational chatbot system leveraging Rasa for natural language understanding, PostgreSQL as the database, pgAdmin for database management, and Nginx for secure endpoint management. The project requires a `.env` file to configure all necessary settings.

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

#### **Nginx Configuration**
| Variable             | Description                                 | Example Value            |
|----------------------|---------------------------------------------|--------------------------|
| `NGINX_SERVER_URL`   | Public-facing URL for Nginx                 | `http://172.17.93.85:8888` |
| `RASA_SERVER_URL`    | URL of the Rasa server                      | `http://172.17.93.85:5005` |
| `AUTH_SERVER_URL`    | URL of the authentication server            | `http://172.17.93.85:5000` |

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

# nginx Configurations
NGINX_SERVER_URL=http://172.17.93.85:8888
RASA_SERVER_URL=http://172.17.93.85:5005
AUTH_SERVER_URL=http://172.17.93.85:5000
```

---

### **3. Setting Up the Environment**

1. Copy the example `.env` file to create your configuration:
   ```bash
   cp .env_example .env
   ```

2. Edit the `.env` file with your specific values.

---

### **4. Running the Project**

#### **With Docker**
The project can be run with Docker Compose:
```bash
docker-compose up --build
```

This will start all necessary services:
- PostgreSQL Database
- pgAdmin Interface
- Rasa Server
- Nginx Proxy

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
- **Chatbot**: Interact with the Rasa chatbot at `http://<NGINX_SERVER_URL>/bot`.
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

### **8. Contribution**
No contributions are accepted since this is a thesis related project. Feel free to contact me at senountanikos@gmail.com for any inquiries.

---

### **9. License**
This project is licensed under the MIT License. See the `LICENSE` file for details.

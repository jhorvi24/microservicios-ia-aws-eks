FROM python:3.10-slim

WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY app.py database.py models.py ./

# Exponer puerto
EXPOSE 8001

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]

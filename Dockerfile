FROM registry.access.redhat.com/ubi9/python-311

# Crear carpeta de trabajo
WORKDIR /opt/app-root/src

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . .

# Exponer el puerto que OpenShift espera
EXPOSE 8080

# Ejecutar la app desde app/main.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# --- OPTIMIZATION: LAYER CACHING ---
# Copy ONLY the requirements first
COPY requirements.txt .

# Install dependencies (this layer will stay cached unless requirements change)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port
EXPOSE 8501

# Command to run
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
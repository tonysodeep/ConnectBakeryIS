# Stage 1: Use an official Python runtime as a base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
# Use --no-cache-dir to minimize image size and --upgrade to ensure latest pip
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code and the start script
COPY . .

# Expose the port the application will run on (default Gunicorn port)
EXPOSE 5000

# Make the start script executable
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:application"]



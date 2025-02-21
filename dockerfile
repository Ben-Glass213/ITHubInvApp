# Use an official lightweight Python image.
FROM python:3.9-slim

# Set the working directory inside the container.
WORKDIR /app

# Copy the requirements file into the container.
COPY requirements.txt .

# Upgrade pip and install dependencies.
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Expose port 5000 for the Flask app.
EXPOSE 5000

# Define the default command to run the Flask application.
CMD ["python", "app.py"]

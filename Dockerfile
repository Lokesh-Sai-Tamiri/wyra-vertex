# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Define the command to run your application (e.g., if you have a web server or a main script)
# If your script just runs and exits, you might need a wrapper or a web framework.
# For a simple script, you might define an entrypoint that calls your generate() function.
# If this is meant to be a web endpoint, you'd use something like gunicorn to run a Flask/FastAPI app.
# Example for a simple script (assuming your generate() function is in main.py and just runs once):
CMD ["python", "main.py"]

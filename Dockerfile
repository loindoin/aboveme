# Use the official Python image as the base
FROM python:3.9-slim


# Set the working directory in the container
WORKDIR /app

COPY config/ /app/config/
# Copy the Python script and the configuration file to the container
COPY aboveme.py /app/
# Install the required dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Run the Python script
CMD ["python", "aboveme.py"]
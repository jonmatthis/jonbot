# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Add current directory code to working directory in Docker image
ADD . /app

# Install Poetry so we can use it to install dependencies
RUN pip install -e .

# Make port 1123 available to the world outside this container
EXPOSE 1235

# Run the command to start your application
CMD ["python", "golem_garden/__main__.py"]

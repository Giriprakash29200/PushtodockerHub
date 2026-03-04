# Use official Python image
FROM python:3.10

# Set working directory inside container
WORKDIR /app

# Copy all files into container
COPY . .

# Run the Python script
CMD ["python", "hello.py"]

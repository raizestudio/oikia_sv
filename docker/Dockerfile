# Image
FROM python:3.13-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install Rust
# RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
# ENV PATH="/root/.cargo/bin:${PATH}"

# Install dependencies
RUN apk add --no-cache python3 python3-dev py3-pip build-base libffi-dev openssl-dev cargo gcc musl-dev postgresql-dev
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the code
COPY . .

# Expose port 8000
EXPOSE 8000

# Run install
RUN python3 manage.py install

# Start Django
CMD ["python3", "manage.py", "runserver"]
# Use an official Ubuntu image as a base
FROM ubuntu:latest

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    apt-add-repository universe && \
    apt-get install -y ffmpeg && \
    apt-get install -y python3 && \
    apt-get update && \
    apt-get install -y curl

# Download yt-dlp
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp && \
    chmod a+rx /usr/local/bin/yt-dlp

# Set the working directory in the container
WORKDIR /home/brandon/flaskapp

# Copy the requirements file into the Docker image
COPY requirements.txt .

# Copy the current directory contents into the container at /app
COPY . .

# Install any needed dependencies specified in requirements.txt
RUN apt-get update && apt-get install -y python3-pip
    
#RUN pip install --break-system-packages Cython 

RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=app.py

# Run app.py when the container launches
CMD ["flask", "run", "--host", "0.0.0.0"]


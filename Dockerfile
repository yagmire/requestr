# Use an official Ubuntu base image
FROM ubuntu:22.04

# Update the package list and install Python 3.11
RUN apt-get update && \
    apt-get install -y python3.11 python3-pip qbittorrent-nox


# Download additional tools
RUN apt-get update && apt-get install -y wget unzip

# Install Python packages
ADD requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Set up qBittorrent configuration
RUN mkdir -p /config

# Copy your Python script to the container
ADD rqst.py /app/rqst.py
ADD filter.txt /app/filter.txt
ADD limits.txt /app/limits.txt
ADD movies.txt /app/movies.txt
ADD qb_login.txt /app/qb_login.txt
ADD token.txt /app/token.txt
ADD channel.txt /app/channel.txt

# Expose the necessary ports
EXPOSE 8080 6881

WORKDIR /app

# Start qBittorrent and run the Python script
CMD qbittorrent-nox --webui-port=8080 & python3 /app/rqst.py

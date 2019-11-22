#Dockerfile 

#====== using docker run ==========

# base image
FROM python:3.6

#create env variable 
ENV PYTHONUNBUFFERED 1

# download vim
RUN ["apt-get", "update"]
RUN ["apt-get", "install", "-y", "vim"]

#add logs
RUN mkdir -p /var/log/scorebot2
#add files to directories
WORKDIR /x/local/scorebot/scorebot-service
ADD . /x/local/scorebot/scorebot-service

# Get pip to download and install requirements:
RUN ["pip", "install", "-r", "requirements.txt"]

# EXPOSE port 8025 to allow communication to/from server
EXPOSE 8025

COPY ./runall.sh /
RUN ["chmod", "+x", "/runall.sh"]
ENTRYPOINT ["/runall.sh", "restart"]

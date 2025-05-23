FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    gnupg \
    lsb-release && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

EXPOSE 11434

RUN ollama serve

CMD ["python3", "app.py"]

# build: docker build -t ollama-cpu .
# run: docker run -p 11434:11434 --name ollama-cpu ollama-cpu
# interact (seperate terminal): docker exec -it ollama-cpu bash

#


# ollama api is accessable from inside the container but not from the local machine. Either figure that
# or move everything inside the container.
#
# * opting to move everything inside the container for the Docker version. To run with ollama already
#   installed, just app.py from the main folder, not the docker folder.
#

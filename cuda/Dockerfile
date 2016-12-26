FROM nvidia/cuda

ENV APP_PORT 1234
ENV APP_ROOT /opt/plugins/cuda

RUN apt-get update
RUN apt-get install -y git python3-dev python3-pip

RUN pip3 install numpy
RUN pip3 install pycuda

# Check if pycuda installed ok
RUN python3 -c "import pycuda"

RUN mkdir -p ${APP_ROOT}_service
EXPOSE ${APP_PORT}
CMD cd ${APP_ROOT}_service && python3 -m http.server ${APP_PORT}

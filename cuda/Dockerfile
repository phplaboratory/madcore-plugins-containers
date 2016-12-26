FROM nvidia/cuda

ENV APP_PORT 1234
ENV APP_ROOT /opt/plugins/cuda

RUN apt-get update
RUN apt-get install -y git python3-dev python3-pip

RUN pip3 install numpy
RUN pip3 install pycuda

# Check if pycuda installed ok
RUN python3 -c "import pycuda"

# clone pycuda to run examples files
RUN git clone --recursive http://git.tiker.net/trees/pycuda.git ${APP_ROOT}/pycuda

ADD pycuda_example.sh /usr/local/bin/pycuda_example
RUN chmod +x /usr/local/bin/pycuda_example

RUN mkdir -p ${APP_ROOT}_service
EXPOSE ${APP_PORT}
CMD cd ${APP_ROOT}_service && python3 -m http.server ${APP_PORT}

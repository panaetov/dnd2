FROM ubuntu:22.04

RUN apt update && apt -y install libmicrohttpd-dev libjansson-dev \
	libssl-dev libsofia-sip-ua-dev libglib2.0-dev \
	libopus-dev libogg-dev libcurl4-openssl-dev liblua5.3-dev \
	libconfig-dev pkg-config libtool automake git

# Сборка libnice
RUN git clone https://gitlab.freedesktop.org/libnice/libnice

RUN apt -y install python3 ninja-build meson

RUN cd ./libnice && \
    meson --prefix=/usr build && ninja -C build && ninja -C build install

RUN apt install -y gcc make wget

RUN cd /tmp && \
    wget https://github.com/cisco/libsrtp/archive/v2.2.0.tar.gz && \
    tar xfv v2.2.0.tar.gz && \
    cd libsrtp-2.2.0 && \
    ./configure --prefix=/usr --enable-openssl && \
    make shared_library && make install

RUN apt install -y g++

# RUN cd /tmp && \
#     wget https://github.com/Kitware/CMake/releases/download/v4.2.1/cmake-4.2.1.tar.gz &&\
#     tar -zxvf cmake-4.2.1.tar.gz &&\
#     cd cmake-4.2.1 && \
#     ./bootstrap
# RUN cd /tmp/cmake-4.2.1 && ./bootstrap && make && make install

RUN apt install -y cmake

RUN cd /tmp && git clone https://boringssl.googlesource.com/boringssl && \
    cd boringssl && \
    sed -i s/" -Werror"//g CMakeLists.txt && \
    mkdir -p build && \
    cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/opt/boringssl -DCMAKE_CXX_FLAGS="-lrt" .. && \
    make && \
    make install

RUN cd /tmp && git clone https://github.com/sctplab/usrsctp && \
    cd usrsctp && \
    ./bootstrap && \
    ./configure --prefix=/usr --disable-programs --disable-inet --disable-inet6 && \
    make && make install


RUN cd /tmp && git clone https://libwebsockets.org/repo/libwebsockets && \
    cd libwebsockets && \
    mkdir build && \
    cd build && \
    cmake -DLWS_MAX_SMP=1 -DLWS_WITHOUT_EXTENSIONS=0 -DCMAKE_INSTALL_PREFIX:PATH=/usr -DCMAKE_C_FLAGS="-fpic" .. && \
    make && make install

RUN cd /tmp && git clone https://github.com/eclipse/paho.mqtt.c.git && \
    cd paho.mqtt.c && make && make install

RUN apt install -y libnanomsg-dev


RUN cd /tmp && git clone https://github.com/alanxz/rabbitmq-c && \
    cd rabbitmq-c && \
    git submodule init && git submodule update && \
    mkdir build && cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/usr .. && \
    make && make install

RUN cd /tmp && git clone https://github.com/meetecho/janus-gateway.git && \
    cd janus-gateway && \
    sh autogen.sh && ./configure --prefix=/opt/janus && make && make install && make configs

RUN apt install -y vim

EXPOSE 8088 8188 7088 10000-10200/udp

CMD ["/opt/janus/bin/janus"]
# CMD ["tail", "-f", "/dev/null"]

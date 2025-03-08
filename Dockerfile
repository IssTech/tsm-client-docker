FROM python:3.13-bookworm AS final

WORKDIR /__issassist/

COPY ["install_client.py", "*-TIV-TSMBAC-LinuxX86_DEB.tar", "dsm.opt.template",\
      "dsm.sys.template", "entrypoint.py", "./"]
COPY ./tsm_client* ./tsm_client
COPY ./pipes /usr/local/bin/pipes

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    TZ=UTC \
    DSM_LOG=/opt/tivoli/tsm/client/ba/bin \
    JAVA_HOME=/opt/tivoli/tsm/tdpvmware/common/jre/jre \
    LD_LIBRARY_PATH=/opt/tivoli/tsm/client/ba/bin:/opt/tivoli/tsm/tdpvmware/common/jre/jre/bin/classic:/usr/local/ibm/gsk8_64/lib64/ \
    PATH=/opt/tivoli/tsm/tdpvmware/common/jre/jre/bin:/sbin:/usr/sbin:/usr/local/sbin:/root/bin:/usr/local/bin:/usr/bin:/bin

# Install the TSM client and set the locale
RUN python3 install_client.py && \
    apt-get update && \
    apt-get -y install locales && \
    sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen && \
    mkdir -p /__issassist/data && \
    ln -s /__issassist/data/dsm.sys /opt/tivoli/tsm/client/ba/bin/dsm.sys && \
    ln -s /__issassist/data/dsm.opt /opt/tivoli/tsm/client/ba/bin/dsm.opt && \
    rm -rf /__issassist/tsm_client && \
    rm -rf /__issassist/*.tar && \
    chmod +x entrypoint.py /usr/local/bin/pipes

ENTRYPOINT ./entrypoint.py

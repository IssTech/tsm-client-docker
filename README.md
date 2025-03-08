Docker Container for IBM's Storage Protect Client
==============================================

Code to deploy IBM's Storage Protect client (dsmc in particular) inside a Docker container.

Binaries are downloaded from [IBM](https://public.dhe.ibm.com/storage/tivoli-storage-management/maintenance/client/v8r1/Linux/LinuxX86_DEB/BA/) when you build the image.


Why?
------
IssTech AB initially wrote this code to run restore tests for 
IBM Storage Protect. 
But in any situation where you need an IBM Storage Protect client in a 
containerized/isolated Linux environment, this code may be useful.

How to use
-----------
When you run a container from the image, 
you will need to provide the following environment variables:

| **Variable name**  | **Description**            |
|--------------------|----------------------------|
| TSM_SERVER_NAME    | Arbitrary SP server name.  |
| TSM_SERVER_HOST    | SP server host.            |
| TSM_SERVER_PORT    | SP server port.            |
| USE_IPV6           | Use IPv6? (1 or 0)         |
| TSM_NODE_NAME      | SP proxy target node name. |
| TSM_PROXY_NAME     | SP proxy agent node name.  |
| TSM_PROXY_PASSWORD | SP proxy agent password.   |
| TLS_ENABLED        | Use TLS? (1 or 0)          |
| TLS_FORCE_V12      | Force TLS 1.2 (1 or 0)     |

Make sure to also mount the CA certificate of the SP server at:
```
/__issassist/data/ca.crt
```
inside the container.

Use the **exec** functionality of your container environment 
(Docker, Kubernetes, etc.) to invoke `dsmc`.

Docker example:
```shell
docker exec -it my_client_container dsmc
```
# omero server local installation

Created: Jan 29, 2021 4:11 PM
Updated: Feb 11, 2021 6:29 PM

Install Omero server + omera web with docker compose.

1) Install docker + ubuntu

[https://docs.docker.com/docker-for-windows/install/](https://docs.docker.com/docker-for-windows/install/) visit here and install docker.
After installation
set wsl version = 2 from
[https://docs.microsoft.com/en-us/windows/wsl/install-win10](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

now

![omero%20server%20local%20instalation/Untitled.png](omero%20server%20local%20instalation/Untitled.png)

You can see that docker is runnin you can test it 

if all okay you can look manual to work with docker (not necessary)

[https://docs.docker.com/get-started/](https://docs.docker.com/get-started/)

2) Install omero-server from [https://github.com/ome/docker-example-omero](https://github.com/ome/docker-example-omero)

go to terminal.

create new folder 'omero' then
```shell
$ mkdir omero
$ cd omero
$ git clone [https://github.com/ome/docker-example-omero.git](https://github.com/ome/docker-example-omero.git)
$ cd docker-example-omero
$ docker-compose up -d
$ docker-compose logs -f
```

after several minutes in my pc it 15 minutes 

![omero%20server%20local%20instalation/Untitled%201.png](omero%20server%20local%20instalation/Untitled%201.png)

if saw something like this all ok then.

for testing, you can open http://127.0.0.1:4080/webclient/login/
```
login: root
password: omero 
```

if you need to transfer files inside server you can git examples from here 

[https://downloads.openmicroscopy.org/images/](https://downloads.openmicroscopy.org/images/)

if you need to transfer example images from local computer to omero local server you can download,

[https://github.com/ome/omero-insight/releases/download/v5.5.14/OMERO.insight-5.5.14.exe](https://github.com/ome/omero-insight/releases/download/v5.5.14/OMERO.insight-5.5.14.exe) 

it is windows native client

for another platforms 

[https://www.openmicroscopy.org/omero/downloads/](https://www.openmicroscopy.org/omero/downloads/)

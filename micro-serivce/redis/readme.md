1) change password in redis.conf
    requirepass password (check what password in microservice env)


2) docker build --pull --rm -f "DockerFile" -t redislabs/rejson:latest "." 

then 

3) docker images

redislabs/rejson                      latest    2b7df03157e6   11 minutes ago   105MB you need something like this

4) docker run -p 6379:6379 --name redis-redisjson 

there = 2b7df03157e6 from 3

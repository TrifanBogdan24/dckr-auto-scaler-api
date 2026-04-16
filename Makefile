build:
	docker build -t job-worker:latest ./job-worker && \
	docker build -t api-service:latest ./api-service

deploy:
	docker stack deploy -c docker-swarm.yml api-scaler

stop:
	docker stack rm api-scaler

rm-jobs:
	docker service rm $(docker service ls --filter "name=job-" -q)

distclean:
	docker volume rm api-scaler_pgdata 

real-time-inspect:
	watch -n 1 "docker service ls"

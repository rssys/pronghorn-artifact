all: build-docker redeploy-k8s

rebuild-docker: build-docker redeploy-k8s

redeploy-docker: deploy-docker

build-docker:
	docker build --tag skharban/database:latest .
	docker push skharban/database:latest

deploy-docker:
	docker run -d --network=host --privileged --name database skharban/database:latest

remove-docker:
	(docker stop database && docker rm database) || true

redeploy-k8s: delete-k8s deploy-k8s

deploy-k8s:
	kubectl apply -f pod.yaml

delete-k8s:
	kubectl delete -f pod.yaml
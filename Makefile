build:
	docker-compose build

run:
	docker-compose up web

test:
	docker-compose up autotests

.PHONY: build run test


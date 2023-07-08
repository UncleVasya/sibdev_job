build:
	docker-compose build

run:
	docker-compose up web

test:
	docker-compose up autotests

bash:
	docker-compose run web bash

.PHONY: build run test bash


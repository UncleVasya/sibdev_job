build:
	docker-compose build

run:
	docker-compose up web

test:
	docker-compose run autotests bash -c "coverage run manage.py test && coverage report"

bash:
	docker-compose run web bash

.PHONY: build run test bash


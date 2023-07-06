# sibdev_job
Тестовое задание для компании Sibdev


# Установка:

```
git clone https://github.com/UncleVasya/sibdev_job.git

cd sibdev_job

docker-compose up
```

------------------

Для удобства важные команды вынесены в Makefile:

```
* make build
* make run
* make test
* make bash
```

------------------

# Использование

## Эндпоинты API (также доступны через веб-морду DRF):
```
http://localhost:8000/api/deals-upload/  - импорт данных о сделках

http://localhost:8000/api/top-customers/ - Список наиболее потратившихся покупателей

По умолчанию показываются Топ 5 покупателей. Это настраивается параметров limit в запросе:
http://localhost:8000/api/top-customers/?limit=10
```

```
# Запуск тестов:

`docker-compose run autotests`

или

`make test`

## Что было сделано по заданию.

### Основные требования:

    1. Данные хранятся в реляционной БД, взаимодействие с ней осуществляется посредством django ORM.
    +
    
    2. Ранее загруженные версии файла deals.csv не должны влиять на результат обработки новых.
    +

    3. Эндпоинты соответствуют спецификации
    +

    4. Приложение должно быть контейнирезировано при помощи docker;
    +

    5. Проект не использует глобальных зависимостей за исключением:  python, docker, docker-compose;
    +

    6. Readme проекта описывает весь процесс установки, запуска и работы с сервисом;
    +

    7. Требования к фронтенду не предъявляются, интерфейс взаимодействия — RestFul API;
    +

    8. Проект запускается одной командой.
    +

### Дополнительно:

    1. Команда, используемая для запуска проекта - docker-compose up;
    +

    2. Кэширование данных, возвращаемых GET-эндпоинтом, с обеспечением достоверности ответов;
    +
    Кеш очищается при импорте данных.

    3. Сервис django работает на многопоточном WSGI-сервере;
    +
    Использовал gunicorn.

    4. API реализован на основе  DRF.
    +
    
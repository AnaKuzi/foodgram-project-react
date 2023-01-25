# Проект «Foodgram»

Проект сделан в декабре 2022 года, в рамках дипломной работы на курсе Яндекс.Практикум "Python-разработчик".

Foodgram реализован для публикации рецептов. Авторизованные пользователи могут подписываться на понравившихся авторов, добавлять рецепты в избранное, в покупки, скачать список покупок ингредиентов для добавленных в покупки рецептов. 

- Для пользователей https://localhost/
- API https://localhost/api/
- Документация API с примерами запросов https://localhost/api/docs/

## Подготовка и запуск проекта
### Склонировать репозиторий на локальную машину:
```
git clone https://github.com/AnaKuzi/foodgram-project-react
```
## Для работы с удаленным сервером (на ubuntu):
* Выполните вход на свой удаленный сервер

* Установите docker на сервер:
```
sudo apt install docker.io 
```
* Установите docker-compose на сервер:
```
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```
* Локально отредактируйте файл infra/nginx.conf и в строке server_name впишите свой IP
* Скопируйте файлы docker-compose.yml и nginx.conf из директории infra на сервер:
```
scp docker-compose.yml <username>@<host>:/home/<username>/docker-compose.yml
scp nginx.conf <username>@<host>:/home/<username>/nginx.conf
```

* Cоздайте .env файл по аналогии с example.env и впишите:
    ```
    DB_ENGINE=<django.db.backends.postgresql>
    DB_NAME=<имя базы данных postgres>
    DB_USER=<пользователь бд>
    DB_PASSWORD=<пароль>
    DB_HOST=<db>
    DB_PORT=<5432>
    SECRET_KEY=<секретный ключ проекта django>
    ```
  
* На сервере соберите docker-compose:
```
sudo docker-compose up -d --build
```
* После успешной сборки на сервере выполните команды (только после первого деплоя):
    - Соберите статические файлы:
    ```
    sudo docker-compose exec django python manage.py collectstatic --noinput
    ```
    - Примените миграции:
    ```
    sudo docker-compose exec django python manage.py migrate --noinput
    ```
    - Загрузите ингридиенты  в базу данных (необязательно):  
    ```
    sudo docker-compose exec django python manage.py fill_ingredients
    ```
    - Создать суперпользователя Django:
    ```
    sudo docker-compose exec django python manage.py createsuperuser
    ```
    - Проект будет доступен по вашему IP
# Predishun

The marketplace for sports analysts and cappers

## Installation

- Clone the repository

**With docker**
- Run `docker compose up -d --build` to build

**Without docker**
- Make sure you have postgres on your machine
- Activate environment variables `pyenv activate predishun-env`
- Install dependencies `pip install -r requirements.txt`
- Run server `python manage.py runserver`


Add .env file with variables

```
DEBUG=1
SECRET_KEY=cdhj6q8r&68+0n@l*t9&s$r-!&1%n=uq4x2i(v72ua=23df4dd567d/d89t24,nl0m.s33si&++=
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,[::1]
CLIENT_LOGIN_URL=http://localhost:3000/login
CLIENT_ACTIVATE_ACCOUNT_URL=http://localhost:3000/account/activate
CLIENT_RESET_PASSWORD_URL=http://localhost:3000/account/password
PAYSTACK_SECRET_KEY=
REDIS_URL=redis://127.0.0.1:6379/1
RDS_ENGINE=django.db.backends.postgresql
RDS_DATABASE=predishun
RDS_USER=postgres
RDS_PASSWORD=postgres
RDS_HOST=localhost
RDS_PORT=5432
EMAIL_HOST=
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
WHATSAPP_WEBHOOK_VERIFY_TOKEN=
WHATSAPP_API_ID=
WHATSAPP_API_SECRET=
WHATSAPP_API_VERSION=v13.0
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_ACCESS_TOKEN=
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_BOT_TOKEN=
TELEGRAM_PHONE_NUMBER=
```

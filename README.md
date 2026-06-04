# Almaz Birthday Bot

Бот без сервера: GitHub Actions каждый день запускает Python-скрипт, проверяет `birthdays.csv`, генерирует случайную футзальную открытку и отправляет ее тебе в Telegram.

## Что внутри

- `main.py` — основной код
- `birthdays.csv` — список игроков и дат рождения
- `assets/logo.jpeg` — логотип МФК «Алмаз»
- `.github/workflows/birthday.yml` — расписание запуска в GitHub Actions
- `requirements.txt` — библиотеки Python

## Как редактировать игроков

Открой `birthdays.csv` и добавляй строки в формате:

```csv
name,birthday
Ім'я Прізвище,04.06.1995
```

Дата должна быть строго в формате `дд.мм.гггг`.

## GitHub Secrets

В репозитории открой:

`Settings → Secrets and variables → Actions → New repository secret`

Добавь:

- `BOT_TOKEN` — токен от BotFather
- `CHAT_ID` — твой Telegram chat_id

## Ручной запуск

`Actions → Birthday Bot → Run workflow`

Для теста временно поставь в `birthdays.csv` сегодняшнюю дату.

## Расписание

Сейчас запуск стоит каждый день в 06:00 UTC, это примерно 09:00 по Украине летом.

Если зимой нужно 09:00 по Украине, поменяй в `.github/workflows/birthday.yml`:

```yaml
- cron: "0 7 * * *"
```

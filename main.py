import csv
import json
import os
import random
from datetime import datetime, timedelta

import requests


BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TODAY = datetime.now() + timedelta(hours=3)
TODAY_DOT = TODAY.strftime("%d.%m")

CONGRATS_FILE = "congratulations.txt"
USED_FILE = "used_congratulations.json"


def calc_age(birthday):
    birth = datetime.strptime(birthday, "%d.%m.%Y")
    age = TODAY.year - birth.year

    if (TODAY.month, TODAY.day) < (birth.month, birth.day):
        age -= 1

    return age


def is_today_birthday(birthday):
    return birthday[:5] == TODAY_DOT


def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
        },
        timeout=30,
    )

    response.raise_for_status()


def load_congratulations():
    with open(CONGRATS_FILE, "r", encoding="utf-8") as file:
        texts = [line.strip() for line in file if line.strip()]

    return texts


def load_used_indexes():
    if not os.path.exists(USED_FILE):
        return []

    with open(USED_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_used_indexes(used_indexes):
    with open(USED_FILE, "w", encoding="utf-8") as file:
        json.dump(used_indexes, file, ensure_ascii=False, indent=2)


def choose_congratulation():
    congratulations = load_congratulations()
    used_indexes = load_used_indexes()

    all_indexes = list(range(len(congratulations)))
    available_indexes = [i for i in all_indexes if i not in used_indexes]

    if not available_indexes:
        used_indexes = []
        available_indexes = all_indexes

    selected_index = random.choice(available_indexes)
    used_indexes.append(selected_index)
    save_used_indexes(used_indexes)

    return congratulations[selected_index]


def format_message(name, age):
    text = choose_congratulation()
    text = text.replace("{name}", name)
    text = text.replace("{age}", str(age))

    return text


def main():
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("Не заданы BOT_TOKEN или CHAT_ID")

    found = False

    with open("birthdays.csv", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            name = row["name"].strip()
            birthday = row["birthday"].strip()

            if is_today_birthday(birthday):
                found = True
                age = calc_age(birthday)
                message = format_message(name, age)
                send_message(message)

    if not found:
        print("Сегодня дней рождения нет")


if __name__ == "__main__":
    main()

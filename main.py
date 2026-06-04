import csv
import json
import os
import random
import requests
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TIMEZONE_SHIFT_HOURS = int(os.getenv("TIMEZONE_SHIFT_HOURS", "3"))

TODAY = datetime.utcnow() + timedelta(hours=TIMEZONE_SHIFT_HOURS)
TODAY_DOT = TODAY.strftime("%d.%m")

BIRTHDAYS_FILE = "birthdays.csv"
CONGRATS_FILE = "congratulations.txt"
USED_FILE = "used_congratulations.json"


def send_message(text: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("Не заданы BOT_TOKEN или CHAT_ID в GitHub Secrets")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=30,
    )
    response.raise_for_status()


def calc_age(birthday: str) -> int:
    birth = datetime.strptime(birthday, "%d.%m.%Y")
    age = TODAY.year - birth.year
    if (TODAY.month, TODAY.day) < (birth.month, birth.day):
        age -= 1
    return age


def is_today_birthday(birthday: str) -> bool:
    return birthday[:5] == TODAY_DOT


def load_congratulations() -> list[str]:
    with open(CONGRATS_FILE, "r", encoding="utf-8") as file:
        raw = file.read()
    texts = [item.strip() for item in raw.split("---") if item.strip()]
    if not texts:
        raise ValueError("Файл congratulations.txt пустой")
    return texts


def load_used_history() -> dict:
    if not os.path.exists(USED_FILE):
        return {}
    with open(USED_FILE, "r", encoding="utf-8") as file:
        content = file.read().strip()
    if not content:
        return {}
    return json.loads(content)


def save_used_history(history: dict) -> None:
    with open(USED_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)
        file.write("
")


def choose_unique_congratulation(name: str, age: int, birthday: str) -> str:
    texts = load_congratulations()
    history = load_used_history()
    used_indexes = set(history.get("used_indexes", []))

    # Если все варианты уже использованы, начинаем новый круг.
    if len(used_indexes) >= len(texts):
        used_indexes = set()

    available_indexes = [i for i in range(len(texts)) if i not in used_indexes]
    selected_index = random.choice(available_indexes)
    used_indexes.add(selected_index)

    history["used_indexes"] = sorted(used_indexes)
    history.setdefault("sent", [])
    history["sent"].append({
        "date": TODAY.strftime("%Y-%m-%d"),
        "name": name,
        "birthday": birthday,
        "age": age,
        "congratulation_index": selected_index,
    })
    save_used_history(history)

    return texts[selected_index].format(name=name, age=age)


def main() -> None:
    found = False
    with open(BIRTHDAYS_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = row["name"].strip()
            birthday = row["birthday"].strip()
            if is_today_birthday(birthday):
                found = True
                age = calc_age(birthday)
                text = choose_unique_congratulation(name, age, birthday)
                message = (
                    f"🎂 <b>Сегодня день рождения</b>
"
                    f"👤 <b>{name}</b>
"
                    f"🎉 <b>{age} лет</b>

"
                    f"{text}"
                )
                send_message(message)

    if not found:
        print("Сегодня дней рождения нет")


if __name__ == "__main__":
    main()

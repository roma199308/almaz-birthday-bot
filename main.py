import csv
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ======================
# Настройки
# ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TIMEZONE_OFFSET_HOURS = int(os.getenv("TIMEZONE_OFFSET_HOURS", "3"))  # Украина: +3 летом
SEND_TOMORROW_REMINDER = os.getenv("SEND_TOMORROW_REMINDER", "true").lower() == "true"

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "birthdays.csv"
LOGO_PATH = ROOT / "assets" / "logo.jpeg"
OUTPUT_PATH = ROOT / "birthday_card.png"

WIDTH = 1080
HEIGHT = 1350

BLUE = (30, 95, 215)
DARK_BLUE = (22, 48, 100)
LIGHT_BLUE = (224, 242, 255)
YELLOW = (255, 207, 51)
WHITE = (255, 255, 255)
BLACK = (30, 30, 35)
RED = (230, 55, 55)
GREEN = (40, 175, 80)
ORANGE = (255, 140, 45)
WOOD = (225, 166, 85)
WOOD_DARK = (190, 122, 55)


def now_local() -> datetime:
    return datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET_HOURS)


TODAY = now_local()
TODAY_DOT = TODAY.strftime("%d.%m")
TOMORROW = TODAY + timedelta(days=1)
TOMORROW_DOT = TOMORROW.strftime("%d.%m")


def get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def draw_center(draw: ImageDraw.ImageDraw, text: str, y: int, size: int, fill=WHITE, bold=True):
    f = get_font(size, bold)
    w, h = text_size(draw, text, f)
    draw.text(((WIDTH - w) / 2, y), text, font=f, fill=fill)


def draw_text_fit_center(draw: ImageDraw.ImageDraw, text: str, y: int, max_width: int, start_size: int, fill=WHITE):
    size = start_size
    while size > 22:
        f = get_font(size, True)
        w, _ = text_size(draw, text, f)
        if w <= max_width:
            break
        size -= 2
    draw_center(draw, text, y, size, fill)


def short_name(full_name: str) -> str:
    parts = full_name.strip().split()
    if len(parts) >= 2:
        return f"{parts[1]} {parts[0]}"
    return full_name.strip()


def surname(full_name: str) -> str:
    return full_name.strip().split()[0].upper()


def calc_age(birthday: str) -> int:
    birth = datetime.strptime(birthday.strip(), "%d.%m.%Y")
    age = TODAY.year - birth.year
    if (TODAY.month, TODAY.day) < (birth.month, birth.day):
        age -= 1
    return age


def is_today_birthday(birthday: str) -> bool:
    return birthday.strip()[:5] == TODAY_DOT


def is_tomorrow_birthday(birthday: str) -> bool:
    return birthday.strip()[:5] == TOMORROW_DOT


def send_message(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("Не заданы BOT_TOKEN или CHAT_ID")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(
        url,
        data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=30,
    )
    response.raise_for_status()


def send_photo(image_path: Path, caption: str):
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("Не заданы BOT_TOKEN или CHAT_ID")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(image_path, "rb") as photo:
        response = requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"},
            files={"photo": photo},
            timeout=60,
        )
    response.raise_for_status()


def create_futsal_background(light=True) -> Image.Image:
    bg = Image.new("RGB", (WIDTH, HEIGHT), LIGHT_BLUE if light else (18, 34, 70))
    draw = ImageDraw.Draw(bg)

    # светлая стена зала
    for y in range(0, 760):
        ratio = y / 760
        r = int((235 if light else 30) * (1 - ratio) + (205 if light else 20) * ratio)
        g = int((246 if light else 55) * (1 - ratio) + (228 if light else 35) * ratio)
        b = int((255 if light else 100) * (1 - ratio) + (245 if light else 85) * ratio)
        draw.line((0, y, WIDTH, y), fill=(r, g, b))

    # паркет
    draw.rectangle((0, 760, WIDTH, HEIGHT), fill=WOOD)
    for y in range(760, HEIGHT, 70):
        draw.line((0, y, WIDTH, y), fill=WOOD_DARK, width=3)
    for x in range(-200, WIDTH, 130):
        draw.line((x, 760, x + 130, HEIGHT), fill=(205, 135, 60), width=2)

    # ворота
    draw.rectangle((330, 575, 750, 760), outline=WHITE, width=12)
    draw.rectangle((365, 615, 715, 760), outline=WHITE, width=5)
    for x in range(350, 750, 40):
        draw.line((x, 580, x, 760), fill=(230, 238, 245), width=2)
    for y in range(600, 760, 35):
        draw.line((335, y, 750, y), fill=(230, 238, 245), width=2)

    # линии футзала
    draw.arc((205, 610, 875, 980), 200, 340, fill=WHITE, width=8)
    draw.line((0, 760, WIDTH, 760), fill=WHITE, width=6)
    draw.ellipse((500, 840, 580, 920), outline=WHITE, width=5)

    return bg


def paste_logo(img: Image.Image, x: int, y: int, size: int = 170):
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo.thumbnail((size, size), Image.LANCZOS)
        canvas = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        lx = (size - logo.width) // 2
        ly = (size - logo.height) // 2
        canvas.alpha_composite(logo, (lx, ly))
        img.paste(canvas, (x, y), canvas)
    except Exception:
        draw = ImageDraw.Draw(img)
        draw.ellipse((x, y, x + size, y + size), fill=WHITE, outline=BLUE, width=8)
        draw.text((x + 35, y + 55), "АЛМАЗ", font=get_font(34), fill=DARK_BLUE)


def draw_ball(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int):
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE, outline=BLACK, width=5)
    draw.polygon(
        [(cx, cy - r // 2), (cx + r // 2, cy - r // 6), (cx + r // 3, cy + r // 2), (cx - r // 3, cy + r // 2), (cx - r // 2, cy - r // 6)],
        fill=BLACK,
    )


def add_footer(draw: ImageDraw.ImageDraw):
    draw.rounded_rectangle((90, 1215, 990, 1300), radius=25, fill=DARK_BLUE)
    draw_center(draw, "З ДНЕМ НАРОДЖЕННЯ! ⚽", 1235, 42, WHITE)


def template_red_card(name: str, age: int) -> Path:
    img = create_futsal_background(light=True)
    draw = ImageDraw.Draw(img)
    paste_logo(img, 455, 45, 170)

    draw_center(draw, "ЧЕРВОНА КАРТКА ВІКУ!", 245, 56, DARK_BLUE)

    # судья-схематично
    draw.ellipse((110, 500, 230, 620), fill=(255, 210, 170), outline=BLACK, width=4)
    draw.rectangle((135, 620, 205, 850), fill=BLACK)
    draw.line((205, 650, 310, 545), fill=BLACK, width=15)
    draw.rounded_rectangle((300, 495, 370, 590), radius=8, fill=RED)
    draw.line((140, 650, 70, 760), fill=BLACK, width=14)
    draw.line((155, 850, 120, 1010), fill=BLACK, width=18)
    draw.line((190, 850, 250, 1010), fill=BLACK, width=18)

    draw.rounded_rectangle((410, 470, 610, 720), radius=25, fill=WHITE, outline=RED, width=8)
    draw_center(draw, str(age - 1), 515, 105, RED)
    draw_center(draw, "ВИДАЛЕНО", 680, 30, BLACK)

    draw.rounded_rectangle((710, 455, 965, 735), radius=30, fill=YELLOW, outline=GREEN, width=8)
    draw_center(draw, str(age), 500, 120, GREEN)
    draw_center(draw, "ВИХОДИТЬ", 680, 30, BLACK)

    draw_text_fit_center(draw, short_name(name).upper(), 840, 780, 58, DARK_BLUE)
    draw_center(draw, "Рішення остаточне. VAR підтвердив 😄", 930, 38, BLACK)
    draw_ball(draw, 540, 1070, 75)
    add_footer(draw)
    img.save(OUTPUT_PATH)
    return OUTPUT_PATH


def template_substitution(name: str, age: int) -> Path:
    img = create_futsal_background(light=True)
    draw = ImageDraw.Draw(img)
    paste_logo(img, 455, 45, 170)

    draw_center(draw, "ЗАМІНА ВІКУ", 260, 70, DARK_BLUE)
    draw.rounded_rectangle((140, 395, 940, 695), radius=45, fill=(22, 32, 44), outline=YELLOW, width=10)
    draw.text((230, 455), str(age - 1), font=get_font(120), fill=RED)
    draw.text((470, 470), "➜", font=get_font(105), fill=WHITE)
    draw.text((660, 455), str(age), font=get_font(120), fill=GREEN)

    draw.rounded_rectangle((160, 750, 920, 930), radius=30, fill=WHITE, outline=BLUE, width=6)
    draw_center(draw, "Гравець той самий", 775, 42, BLACK)
    draw_center(draw, "досвіду стало більше", 835, 42, BLUE)

    draw_text_fit_center(draw, short_name(name).upper(), 1010, 850, 58, DARK_BLUE)
    draw_center(draw, "Тренер схвалив. Коліна — під питанням 😄", 1100, 34, BLACK)
    add_footer(draw)
    img.save(OUTPUT_PATH)
    return OUTPUT_PATH


def template_scoreboard(name: str, age: int) -> Path:
    img = create_futsal_background(light=True)
    draw = ImageDraw.Draw(img)
    paste_logo(img, 455, 40, 165)

    draw.rounded_rectangle((90, 305, 990, 815), radius=45, fill=(25, 32, 42), outline=BLUE, width=10)
    draw_center(draw, "ДЕНЬ НАРОДЖЕННЯ", 350, 56, YELLOW)
    draw.text((190, 465), "МОЛОДІСТЬ", font=get_font(38), fill=WHITE)
    draw.text((660, 465), "ДОСВІД", font=get_font(38), fill=WHITE)
    draw.text((200, 560), str(age - 1), font=get_font(135), fill=RED)
    draw.text((488, 585), ":", font=get_font(100), fill=WHITE)
    draw.text((645, 560), str(age), font=get_font(135), fill=GREEN)
    draw_center(draw, "ПЕРЕМІГ ДОСВІД 🏆", 760, 46, YELLOW)

    draw_ball(draw, 540, 910, 70)
    draw_text_fit_center(draw, short_name(name).upper(), 1030, 850, 56, DARK_BLUE)
    draw_center(draw, "Матч завершено. Протест не приймається 😄", 1120, 34, BLACK)
    add_footer(draw)
    img.save(OUTPUT_PATH)
    return OUTPUT_PATH


def template_tactic_plan(name: str, age: int) -> Path:
    img = create_futsal_background(light=True)
    draw = ImageDraw.Draw(img)
    paste_logo(img, 455, 35, 160)

    draw.rounded_rectangle((95, 270, 985, 980), radius=35, fill=WHITE, outline=DARK_BLUE, width=8)
    draw_center(draw, "ТАКТИЧНИЙ ПЛАН", 310, 58, DARK_BLUE)
    draw_center(draw, "НА ДЕНЬ НАРОДЖЕННЯ", 380, 42, BLUE)

    items = [
        "1. Приймати привітання",
        "2. Їсти торт без пресингу",
        "3. Не рахувати калорії",
        "4. Відпочити як чемпіон",
        "5. На наступній грі забити гол",
    ]
    y = 500
    for item in items:
        draw.text((155, y), item, font=get_font(38), fill=BLACK)
        y += 80

    # мини-схема
    draw.rectangle((700, 535, 920, 805), outline=BLUE, width=5)
    draw.line((700, 670, 920, 670), fill=BLUE, width=3)
    draw.ellipse((785, 630, 835, 680), outline=BLUE, width=3)
    draw.text((735, 720), "X  O  X", font=get_font(24), fill=BLACK)

    draw_text_fit_center(draw, f"{short_name(name).upper()} — {age}", 1030, 850, 54, DARK_BLUE)
    draw_center(draw, "Головне — задоволення від гри 😄", 1125, 36, BLACK)
    add_footer(draw)
    img.save(OUTPUT_PATH)
    return OUTPUT_PATH


def template_locker_ball(name: str, age: int) -> Path:
    img = create_futsal_background(light=True)
    draw = ImageDraw.Draw(img)
    paste_logo(img, 455, 40, 160)

    # шкафчик
    draw.rounded_rectangle((290, 260, 790, 945), radius=30, fill=DARK_BLUE, outline=BLUE, width=10)
    draw_text_fit_center(draw, surname(name), 330, 420, 58, WHITE)
    draw_center(draw, str(age), 430, 140, YELLOW)
    draw_center(draw, "РОКІВ", 590, 44, WHITE)
    draw.line((330, 705, 750, 705), fill=WHITE, width=4)
    draw_center(draw, "ФОРМА ГОТОВА", 740, 36, WHITE)

    # мяч со словами
    draw_ball(draw, 270, 1000, 95)
    draw.rounded_rectangle((405, 900, 930, 1035), radius=28, fill=WHITE, outline=BLACK, width=5)
    draw.text((440, 925), "Ну що, старий...", font=get_font(34), fill=BLACK)
    draw.text((440, 975), "пас ще віддаси? 😉", font=get_font(34), fill=BLACK)

    draw_text_fit_center(draw, short_name(name).upper(), 1110, 850, 50, DARK_BLUE)
    add_footer(draw)
    img.save(OUTPUT_PATH)
    return OUTPUT_PATH


def template_futsal_still_can(name: str, age: int) -> Path:
    img = create_futsal_background(light=True)
    draw = ImageDraw.Draw(img)
    paste_logo(img, 455, 40, 160)

    draw_center(draw, f"{age} РОКІВ", 285, 88, DARK_BLUE)
    draw_center(draw, "НА МАЙДАНЧИК ЩЕ МОЖУ!", 390, 58, BLUE)

    # схематичный игрок лежит на паркете
    draw.ellipse((440, 610, 560, 730), fill=(255, 210, 170), outline=BLACK, width=4)
    draw.rectangle((395, 725, 685, 840), fill=BLUE)
    draw.line((420, 820, 250, 940), fill=BLUE, width=28)
    draw.line((660, 820, 830, 940), fill=BLUE, width=28)
    draw.line((430, 735, 270, 680), fill=BLUE, width=22)
    draw.line((650, 735, 820, 690), fill=BLUE, width=22)
    draw.text((470, 765), surname(name)[:8], font=get_font(38), fill=WHITE)

    draw.rounded_rectangle((130, 980, 950, 1110), radius=30, fill=WHITE, outline=BLUE, width=6)
    draw_center(draw, "Відпочинок — теж частина тренування 😄", 1015, 38, BLACK)

    draw_ball(draw, 850, 795, 70)
    draw_text_fit_center(draw, short_name(name).upper(), 1145, 850, 50, DARK_BLUE)
    add_footer(draw)
    img.save(OUTPUT_PATH)
    return OUTPUT_PATH


def generate_image(name: str, age: int) -> Path:
    templates = [
        template_red_card,
        template_substitution,
        template_scoreboard,
        template_tactic_plan,
        template_locker_ball,
        template_futsal_still_can,
    ]
    return random.choice(templates)(name, age)


def generate_caption(name: str, age: int) -> str:
    texts = [
        f"🎂 <b>{name}, з днем народження!</b>\n\n{age} — це не вік, це просто новий сезон з більшим досвідом 😄⚽",
        f"⚽ <b>{name}, вітаю!</b>\n\nБажаю голів побільше, травм поменше, а третій тайм — тільки переможний 😄",
        f"🎉 <b>{name}, з днюхою!</b>\n\nНехай ноги біжать, паси проходять, а суддя сьогодні не помічає дрібних фолів 😄",
        f"🏆 <b>{name}, вітаю з {age}!</b>\n\nМолодість пішла в пресинг, але досвід красиво вийшов з-під тиску 😄",
        f"📋 <b>{name}, офіційний протокол:</b>\n\nВік оновлено до {age}. Гравець допущений до привітань, торта і третього тайму 😄",
    ]
    return random.choice(texts)


def read_players():
    with open(CSV_PATH, encoding="utf-8") as file:
        return list(csv.DictReader(file))


def main():
    players = read_players()
    today_players = []
    tomorrow_players = []

    for row in players:
        name = row["name"].strip()
        birthday = row["birthday"].strip()

        if is_today_birthday(birthday):
            today_players.append((name, birthday))
        elif SEND_TOMORROW_REMINDER and is_tomorrow_birthday(birthday):
            tomorrow_players.append((name, birthday))

    for name, birthday in tomorrow_players:
        age_tomorrow = calc_age(birthday)
        send_message(
            f"⏰ <b>Завтра день народження</b>\n\n"
            f"👤 {name}\n"
            f"🎂 Буде {age_tomorrow} років\n\n"
            f"Не забудь привітати ⚽😄"
        )

    for name, birthday in today_players:
        age = calc_age(birthday)
        image_path = generate_image(name, age)
        caption = generate_caption(name, age)
        send_photo(image_path, caption)

    if not today_players and not tomorrow_players:
        print("Сегодня и завтра дней рождения нет")


if __name__ == "__main__":
    main()

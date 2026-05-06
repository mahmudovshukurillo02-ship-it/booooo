import os
import re
import socket
import logging
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest

# ================== LOG ==================
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

load_dotenv()

# ================== TELEFON FORMAT ==================
def normalize_uz_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 9:
        return "+998" + digits
    if len(digits) == 12 and digits.startswith("998"):
        return "+" + digits
    # agar foydalanuvchi allaqachon +998... yozgan bo‘lsa
    if (raw or "").strip().startswith("+"):
        return (raw or "").strip()
    return (raw or "").strip()


def format_phones(phones) -> str:
    if isinstance(phones, str):
        phones = [phones]
    phones = [normalize_uz_phone(p) for p in phones if (p or "").strip()]
    return ", ".join(phones) if phones else "Телефон кўрсатилмаган"


# ================== DATA ==================
# Har bir bo‘lim: {"title": "...", "items":[{"name":"..","phone":[...]}]}
# MFY: {"title":"..", "mahallas": {"Mahalla":[items...] } }

DATA = {
    "hokimlik": {
        "title": "🏛 Tuman hokimligi",
        "items": [
            {"name": "Биринчи ўринбосар", "phone": ["97-272-77-22"]},
            {"name": "Қурилиш бўйича ўринбосар", "phone": ["88-992-10-00"]},
            {"name": "Инвестиция бўйича ўринбосар", "phone": ["94-566-78-18"]},
            {"name": "Қишлоқ хўжалиги бўйича ўринбосар", "phone": ["93-416-78-00"]},
            {"name": "Ёшлар бўйича ўринбосар", "phone": ["90-624-11-13"]},
            {"name": "Хотин-қизлар бўлими", "phone": ["94-024-05-55"]},
            {"name": "Кадрлар бўлими", "phone": ["94-432-77-07"]},
            {"name": "Диний ишлар бўйича бош мутахассис", "phone": ["93-631-29-09"]},
        ],
    },

    "tashkilotlar": {
        "title": "🏢 Tuman tashkilotlari",
        "items": [
            {"name": "Туман МИБ", "phone": ["97-338-21-21"]},
            {"name": "Туман Адлия бўлими", "phone": ["90-384-77-71"]},
            {"name": "Фавқулодда вазиятлар", "phone": ["97-983-40-10"]},
            {"name": "Туман мудофаа", "phone": ["95-109-68-18"]},
            {"name": "Маҳаллалар уюшмаси", "phone": ["94-437-62-72"]},
            {"name": "Камбағаллик ва Бандлик бўлими", "phone": ["88-871-21-21"]},
            {"name": "Ижтимоий ҳимоя миллий агентлиги", "phone": ["93-241-81-81"]},
            {"name": "Туман молия бўлими", "phone": ["93-210-55-55"]},
            {"name": "Ғазначилик бўлинмаси", "phone": ["99-435-05-44"]},
            {"name": "Туман Статистика бўлими", "phone": ["91-288-61-28"]},
            {"name": "Пенсия жамғармаси", "phone": ["99-390-11-22"]},
            {"name": "Агробанк ОАТБ", "phone": ["99-476-70-00"]},
            {"name": "Халқбанки ДТБ", "phone": ["91-611-51-17"]},
            {"name": "Микрокредитбанк ОАТБ", "phone": ["90-385-55-99"]},
        ],
    },

    "Maktab": {
        "title": "🎓 Maktab",
        "items": [
            {"name": "1-мактаб", "phone": ["90-623-83-76"]},
            {"name": "2-мактаб", "phone": ["90-543-60-55"]},
            {"name": "3-мактаб", "phone": ["94-015-02-02"]},
            {"name": "4-мактаб", "phone": ["91-173-75-06"]},
            {"name": "5-мактаб", "phone": ["91-168-76-60"]},
            {"name": "6-мактаб", "phone": ["99-071-90-37"]},
            {"name": "7-мактаб", "phone": ["94-070-78-76"]},
            {"name": "8-мактаб", "phone": ["97-993-94-35"]},
            {"name": "9-мактаб", "phone": ["94-269-70-15"]},
            {"name": "10-мактаб", "phone": ["90-547-72-16"]},
            {"name": "11-мактаб", "phone": ["91-289-14-62"]},
            {"name": "12-мактаб", "phone": ["94-804-49-89"]},
            {"name": "13-мактаб", "phone": ["94-433-45-03"]},
            {"name": "14-мактаб", "phone": ["93-222-58-48"]},
            {"name": "15-мактаб", "phone": ["90-762-52-25"]},
            {"name": "16-мактаб", "phone": ["99-027-11-64"]},
            {"name": "17-мактаб", "phone": ["50-017-70-14"]},
            {"name": "18-мактаб", "phone": ["99-907-80-84"]},
            {"name": "19-мактаб", "phone": ["93-222-58-48"]},
            {"name": "20-мактаб", "phone": ["95-072-13-72"]},
            {"name": "21-мактаб", "phone": ["91-167-02-22"]},
            {"name": "22-мактаб", "phone": ["93-068-17-31"]},
            {"name": "23-мактаб", "phone": ["88-838-55-58"]},
            {"name": "24-мактаб", "phone": ["94-978-28-71"]},
            {"name": "25-мактаб", "phone": ["97-999-35-35"]},
            {"name": "26-мактаб", "phone": ["93-222-58-48"]},
            {"name": "27-мактаб", "phone": ["93-694-59-51"]},
            {"name": "28-мактаб", "phone": ["93-242-87-62"]},
            {"name": "29-мактаб", "phone": ["93-063-00-88"]},
            {"name": "30-мактаб", "phone": ["91-290-39-49"]},
            {"name": "31-мактаб", "phone": ["99-107-57-50"]},
            {"name": "32-мактаб", "phone": ["90-143-46-42"]},
            {"name": "33-мактаб", "phone": ["91-168-67-68"]},
            {"name": "34-мактаб", "phone": ["94-565-59-69"]},
            {"name": "35-мактаб", "phone": ["95-818-35-55"]},
            {"name": "36-мактаб", "phone": ["95-477-33-36"]},
            {"name": "37-мактаб", "phone": ["94-067-00-67"]},
            {"name": "38-мактаб", "phone": ["94-657-17-91"]},
            {"name": "39-мактаб", "phone": ["93-756-57-67"]},
            {"name": "40-мактаб", "phone": ["99-903-25-56"]},
            {"name": "41-мактаб", "phone": ["91-173-45-99"]},
            {"name": "42-мактаб", "phone": ["93-706-04-62"]},
            {"name": "43-мактаб", "phone": ["95-801-00-43"]},
            {"name": "44-мактаб", "phone": ["88-165-03-05"]},
            {"name": "45-мактаб", "phone": ["91-611-90-67"]},
            {"name": "46-мактаб", "phone": ["93-062-69-44"]},
            {"name": "47-мактаб", "phone": ["99-724-79-00"]},
            {"name": "48-мактаб", "phone": ["97-164-57-55"]},
            {"name": "49-мактаб", "phone": ["99-362-27-68"]},
            {"name": "50-мактаб", "phone": ["99-512-91-04"]},
            {"name": "51-мактаб", "phone": ["99-169-01-94"]},

            {"name": "1 ДИУМ", "phone": ["94-758-83-07"]},
            {"name": "17 ДИМ", "phone": ["94-314-60-66"]},
            {"name": "49 ДИМ", "phone": ["90-624-46-80"]},
            {"name": "62 ДИУМ", "phone": ["99-055-67-85"]},
            {"name": "73 ДИУМ", "phone": ["91-489-55-21"]},
        ],
    },

    "bogcha": {
        "title": "🏫 Bog'cha muassasalari",
        "items": [
            {"name": "1-Боғча", "phone": ["95-028-34-37"]},
            {"name": "2-Боғча", "phone": ["99-903-00-74"]},
            {"name": "3-Боғча", "phone": ["91-610-32-18"]},
            {"name": "4-Боғча", "phone": ["90-144-78-00"]},
            {"name": "5-Боғча", "phone": ["94-702-69-79"]},
            {"name": "6-Боғча", "phone": ["99-847-07-80"]},
            {"name": "7-Боғча", "phone": ["91-605-86-34"]},
            {"name": "8-Боғча", "phone": ["91-620-00-05"]},
            {"name": "9-Боғча", "phone": ["88-060-66-02"]},
            {"name": "10-Боғча", "phone": ["90-382-03-38"]},
            {"name": "11-Боғча", "phone": ["88-650-90-93"]},
            {"name": "12-Боғча", "phone": ["97-978-62-62"]},
            {"name": "13-Боғча", "phone": ["91-172-72-00"]},
            {"name": "14-Боғча", "phone": ["97-974-77-88"]},
            {"name": "15-Боғча", "phone": ["90-540-28-13"]},
            {"name": "16-Боғча", "phone": ["90-767-54-54"]},
            {"name": "17-Боғча", "phone": ["99-230-01-75"]},
            {"name": "18-Боғча", "phone": ["93-259-47-72"]},
            {"name": "19-Боғча", "phone": ["93-632-47-69"]},
            {"name": "20-Боғча", "phone": ["90-382-40-28"]},
            {"name": "21-Боғча", "phone": ["97-835-55-21"]},
            {"name": "22-Боғча", "phone": ["91-602-54-43"]},
            {"name": "23-Боғча", "phone": ["97-473-22-82"]},
            {"name": "24-Боғча", "phone": ["97-135-71-55"]},
            {"name": "25-Боғча", "phone": ["94-095-12-09"]},
            {"name": "26-Боғча", "phone": ["90-146-00-81"]},
            {"name": "27-Боғча", "phone": ["88-998-86-87"]},
            {"name": "28-Боғча", "phone": ["50-007-20-65"]},
            {"name": "29-Боғча", "phone": ["99-993-67-03"]},
            {"name": "30-Боғча", "phone": ["90-542-86-20"]},
            {"name": "31-Боғча", "phone": ["90-573-70-16"]},
            {"name": "32-Боғча", "phone": ["99-016-00-39"]},
            {"name": "33-Боғча", "phone": ["93-061-03-34"]},
            {"name": "34-Боғча", "phone": ["99-489-21-00"]},
        ],
    },

    "mfy": {
               "title": "🏘 MFYlar",
        "mahallas": {
                      "Жалақудуқ МФЙ": [
            {"name": "МФЙ раиси", "phone": ["90-210-68-12"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["90-525-13-94"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["93-789-00-89"]},
            {"name": "Ижтимоий ходим", "phone": ["90-547-93-17"]},
            {"name": "Ёшлар етакчиси", "phone": ["90-145-87-57"]},
        ],
        "Дўнгқишлоқ МФЙ": [
            {"name": "МФЙ раиси", "phone": ["93-925-44-75"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["99-007-28-04"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["91-602-88-71"]},
            {"name": "Ижтимоий ходим", "phone": ["88-926-01-13"]},
            {"name": "Ёшлар етакчиси", "phone": []},
        ],
        "Бўстон МФЙ": [
            {"name": "МФЙ раиси", "phone": ["99-303-02-76"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["90-525-13-94"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["99-533-11-14"]},
            {"name": "Ижтимоий ходим", "phone": ["94-810-88-87"]},
            {"name": "Ёшлар етакчиси", "phone": ["93-945-07-28"]},
        ],
        "Янгисор МФЙ": [
            {"name": "МФЙ раиси", "phone": ["99-924-41-05"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["99-726-55-08"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["93-443-66-99"]},
            {"name": "Ижтимоий ходим", "phone": ["99-981-11-14"]},
            {"name": "Ёшлар етакчиси", "phone": ["99-610-19-95"]},
        ],
        "Ўрғу МФЙ": [
            {"name": "МФЙ раиси", "phone": ["99-438-64-55"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["90-141-94-74"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["93-191-08-86"]},
            {"name": "Ижтимоий ходим", "phone": ["94-312-11-10"]},
            {"name": "Ёшлар етакчиси", "phone": ["99-047-00-52"]},
        ],
        "Қорағул МФЙ": [
            {"name": "МФЙ раиси", "phone": ["94-835-02-86"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["99-007-28-04"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["94-438-13-09"]},
            {"name": "Ижтимоий ходим", "phone": ["99-433-20-83"]},
            {"name": "Ёшлар етакчиси", "phone": ["99-086-18-17"]},
        ],
        "Достонобод МФЙ": [
            {"name": "МФЙ раиси", "phone": ["99-309-63-52"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["93-322-10-44"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["77-370-20-30"]},
            {"name": "Ижтимоий ходим", "phone": ["33-838-01-03"]},
            {"name": "Ёшлар етакчиси", "phone": ["94-386-77-15"]},
        ],
        "Катта полвон МФЙ": [
            {"name": "МФЙ раиси", "phone": ["94-565-10-72"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["93-272-26-67"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["99-987-11-74"]},
            {"name": "Ижтимоий ходим", "phone": ["93-273-47-07"]},
            {"name": "Ёшлар етакчиси", "phone": ["50-303-43-60"]},
        ],
        "Тўрачеки МФЙ": [
            {"name": "МФЙ раиси", "phone": ["93-425-70-50"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["93-690-49-19"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["93-385-54-43"]},
            {"name": "Ижтимоий ходим", "phone": ["88-164-41-11"]},
            {"name": "Ёшлар етакчиси", "phone": ["93-150-67-77"]},
        ],
        "Ақча МФЙ": [
            {"name": "МФЙ раиси", "phone": ["97-346-86-26"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["90-147-59-70"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["94-837-28-38"]},
            {"name": "Ижтимоий ходим", "phone": ["90-769-70-76"]},
            {"name": "Ёшлар етакчиси", "phone": ["99-051-03-04"]},
        ],
        "Хамзаобод МФЙ": [
            {"name": "МФЙ раиси", "phone": ["93-061-00-55"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["93-690-49-19"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["99-037-41-10"]},
            {"name": "Ижтимоий ходим", "phone": ["93-483-31-22"]},
            {"name": "Ёшлар етакчиси", "phone": ["97-988-08-97"]},
        ],
        "Қиличмозор МФЙ": [
            {"name": "МФЙ раиси", "phone": ["95-080-94-93"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["90-147-59-70"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["88-975-70-71"]},
            {"name": "Ижтимоий ходим", "phone": ["90-767-64-64"]},
            {"name": "Ёшлар етакчиси", "phone": ["77-007-70-95"]},
        ],
        "Капа МФЙ": [
            {"name": "МФЙ раиси", "phone": ["93-426-10-31"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["93-794-23-74"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["93-247-40-75"]},
            {"name": "Ижтимоий ходим", "phone": ["97-996-35-45"]},
            {"name": "Ёшлар етакчиси", "phone": ["88-929-00-44"]},
        ],
        "Қораёнтоқ МФЙ": [
            {"name": "МФЙ раиси", "phone": ["93-442-46-76"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["94-273-76-67"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["94-381-00-90"]},
            {"name": "Ижтимоий ходим", "phone": ["91-500-75-83"]},
            {"name": "Ёшлар етакчиси", "phone": ["77-265-93-93"]},
        ],
        "Маданият МФЙ": [
            {"name": "МФЙ раиси", "phone": ["93-276-11-12"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["93-243-50-96"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["93-785-98-95"]},
            {"name": "Ижтимоий ходим", "phone": ["97-905-21-21"]},
            {"name": "Ёшлар етакчиси", "phone": ["94-298-71-11"]},
        ],
        "Намуна МФЙ": [
            {"name": "МФЙ раиси", "phone": ["90-549-75-94"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["93-518-27-47"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["91-291-61-99"]},
            {"name": "Ижтимоий ходим", "phone": ["94-110-09-05"]},
            {"name": "Ёшлар етакчиси", "phone": ["90-311-11-95"]},
        ],
        "Бойчеки МФЙ": [
            {"name": "МФЙ раиси", "phone": ["91-601-96-58", "91-606-59-52"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["90-141-94-74"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["88-997-63-33"]},
            {"name": "Ижтимоий ходим", "phone": ["99-433-84-24"]},
            {"name": "Ёшлар етакчиси", "phone": ["33-610-10-09"]},
        ],
        "Бештол МФЙ": [
            {"name": "МФЙ раиси", "phone": ["91-600-22-38"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["91-605-66-07"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["97-472-76-76"]},
            {"name": "Ижтимоий ходим", "phone": ["88-008-68-42"]},
            {"name": "Ёшлар етакчиси", "phone": ["94-298-71-11"]},
        ],
        "Хамза МФЙ": [
            {"name": "МФЙ раиси", "phone": ["97-836-65-65"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["97-324-19-68"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["97-580-08-09"]},
            {"name": "Ижтимоий ходим", "phone": ["99-327-74-94"]},
            {"name": "Ёшлар етакчиси", "phone": ["93-425-95-66"]},
        ],
        "Гулистон МФЙ (бештол)": [
            {"name": "МФЙ раиси", "phone": ["97-273-03-55"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["97-992-26-50"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["90-140-56-87"]},
            {"name": "Ижтимоий ходим", "phone": ["88-834-21-04"]},
            {"name": "Ёшлар етакчиси", "phone": ["93-945-07-28"]},
        ],
        "Қўштерак МФЙ": [
            {"name": "МФЙ раиси", "phone": ["88-161-61-51"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["97-324-19-68"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["97-999-39-94"]},
            {"name": "Ижтимоий ходим", "phone": ["97-993-66-23"]},
            {"name": "Ёшлар етакчиси", "phone": ["90-258-54-54"]},
        ],
        "Ғалаба МФЙ": [
            {"name": "МФЙ раиси", "phone": ["88-832-70-73"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["90-200-03-38"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["90-767-95-00"]},
            {"name": "Ижтимоий ходим", "phone": ["91-479-91-01"]},
            {"name": "Ёшлар етакчиси", "phone": []},
        ],
        "Ёрқишлоқ МФЙ": [
            {"name": "МФЙ раиси", "phone": ["90-382-58-78"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["90-149-92-21"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["90-548-77-00"]},
            {"name": "Ижтимоий ходим", "phone": ["88-987-09-28"]},
            {"name": "Ёшлар етакчиси", "phone": ["99-513-46-97"]},
        ],
        "Қутлуғ МФЙ": [
            {"name": "МФЙ раиси", "phone": ["93-540-65-61"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["91-616-24-55"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["90-380-06-46"]},
            {"name": "Ижтимоий ходим", "phone": ["91-600-20-72"]},
            {"name": "Ёшлар етакчиси", "phone": ["99-909-19-96"]},
        ],
        "Кашкар МФЙ": [
            {"name": "МФЙ раиси", "phone": ["90-170-05-30"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["91-616-24-55"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["94-979-01-09"]},
            {"name": "Ижтимоий ходим", "phone": ["91-172-37-37"]},
            {"name": "Ёшлар етакчиси", "phone": ["90-767-29-49"]},
        ],
        "Тошховуз МФЙ": [
            {"name": "МФЙ раиси", "phone": ["90-384-44-33"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["91-605-66-07"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["90-767-26-62"]},
            {"name": "Ижтимоий ходим", "phone": ["93-150-38-97"]},
            {"name": "Ёшлар етакчиси", "phone": ["93-447-04-97"]},
        ],
        "Янги кўрпа МФЙ": [
            {"name": "МФЙ раиси", "phone": ["91-172-12-78"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["90-149-92-21"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["99-006-40-85"]},
            {"name": "Ижтимоий ходим", "phone": ["91-065-54-67"]},
            {"name": "Ёшлар етакчиси", "phone": ["97-833-88-55"]},
        ],
        "Хасанобод МФЙ": [
            {"name": "МФЙ раиси", "phone": ["93-052-43-57"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["99-302-17-50"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["93-219-38-33"]},
            {"name": "Ижтимоий ходим", "phone": ["93-495-45-27"]},
            {"name": "Ёшлар етакчиси", "phone": ["94-438-20-24"]},
        ],
        "Шархончеки МФЙ": [
            {"name": "МФЙ раиси", "phone": ["99-847-39-49"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["90-545-99-17"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["90-254-70-20"]},
            {"name": "Ижтимоий ходим", "phone": ["90-771-95-75"]},
            {"name": "Ёшлар етакчиси", "phone": ["91-778-88-89"]},
        ],
        "Бешкарам МФЙ": [
            {"name": "МФЙ раиси", "phone": ["93-739-77-92"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["93-642-03-70"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["93-821-33-33"]},
            {"name": "Ижтимоiy ходим", "phone": ["93-472-10-05"]},
            {"name": "Ёшлар етакчиси", "phone": ["77-265-93-93"]},
        ],
        "Ғозичеки МФЙ": [
            {"name": "МФЙ раиси", "phone": ["91-610-26-74"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["99-302-17-50"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["97-995-50-50"]},
            {"name": "Ижтимоий ходим", "phone": ["93-428-74-57"]},
            {"name": "Ёшлар етакчиси", "phone": ["94-386-77-15"]},
        ],
        "Кесак МФЙ": [
            {"name": "МФЙ раиси", "phone": ["93-218-18-11"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["93-642-03-70"]},
            {"name": "Ҳокim ёрдамчиси", "phone": ["99-220-22-23"]},
            {"name": "Ижтимоий ходим", "phone": ["90-200-96-90"]},
            {"name": "Ёшлар етакчиси", "phone": ["97-987-42-43"]},
        ],
        "Гулистон МФЙ (шаҳар)": [
            {"name": "МФЙ раиси", "phone": ["90-146-33-97"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["91-615-87-68"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["50-505-04-84"]},
            {"name": "Ижтимоий ходим", "phone": ["94-616-89-01"]},
            {"name": "Ёшлар етакчиси", "phone": ["33-610-10-09"]},
        ],
        "Қадақсин МФЙ": [
            {"name": "МФЙ раиси", "phone": ["91-613-47-07"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["90-545-99-17"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["90-548-98-78"]},
            {"name": "Ижтимоий ходим", "phone": ["90-169-36-35"]},
            {"name": "Ёшlar етакчиси", "phone": ["90-541-14-30"]},
        ],
        "Бозорбоши МФЙ": [
            {"name": "МФЙ раиси", "phone": ["99-323-63-00"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["91-615-87-68"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["91-492-33-55"]},
            {"name": "Ижтимоий ходim", "phone": ["94-917-09-69"]},
            {"name": "Ёшлар етакчиси", "phone": ["93-150-67-77"]},
        ],
        "Сўфиқишлоқ МФЙ": [
            {"name": "МФЙ раиси", "phone": ["90-622-51-15"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["91-499-27-95"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["99-917-30-47"]},
            {"name": "Ижтимоий ходим", "phone": ["90-549-64-44"]},
            {"name": "Ёшлар етакчиси", "phone": ["99-006-66-57"]},
        ],
        "А.Рахмонов МФЙ": [
            {"name": "МФЙ раиси", "phone": ["94-328-02-26"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["97-169-24-69"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["99-300-71-33"]},
            {"name": "Ижтимоий ходим", "phone": ["94-315-66-60"]},
            {"name": "Ёшlar етакчиси", "phone": []},
        ],
        "Бузрукхонтўра МФЙ": [
            {"name": "МФЙ раиси", "phone": ["91-498-20-74"]},
            {"name": "Хотин-қизlar фаоли", "phone": ["90-494-55-00"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["99-478-15-48"]},
            {"name": "Ижтимоий ходim", "phone": ["93-890-90-98"]},
            {"name": "Ёшlar етakчиси", "phone": ["77-007-70-95"]},
        ],
        "Кўкалам МФЙ": [
            {"name": "МФЙ раиси", "phone": ["91-480-62-13"]},
            {"name": "Хотин-қизlar фаoli", "phone": ["90-542-88-54"]},
            {"name": "Ҳокim ёрдамчиси", "phone": ["99-230-00-30"]},
            {"name": "Ижтимоий ходim", "phone": ["93-859-70-03"]},
            {"name": "Ёшlar етakчиси", "phone": ["93-577-17-26"]},
        ],
        "Олмазор МФЙ": [
            {"name": "МФЙ раиси", "phone": ["99-366-16-06"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["99-301-78-31"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["90-534-17-07"]},
            {"name": "Ижтимоiy ходim", "phone": ["94-514-94-01"]},
            {"name": "Ёшлар етakчиси", "phone": ["97-103-00-74"]},
        ],
        "Иттифоқ МФЙ (Ойим)": [
            {"name": "МФЙ раиси", "phone": ["91-168-37-66"]},
            {"name": "Хотин-қизlar фаoli", "phone": ["97-169-24-69"]},
            {"name": "Ҳокim ёрдамчиси", "phone": ["97-980-81-17"]},
            {"name": "Ижтимоий ходim", "phone": ["91-612-76-73"]},
            {"name": "Ёшlar етakчиси", "phone": ["77-080-17-11"]},
        ],
        "Делварзин МФЙ": [
            {"name": "МФЙ раиси", "phone": ["99-982-89-01"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["90-542-88-54"]},
            {"name": "Ҳоким ёрдамчиси", "phone": ["93-706-11-34"]},
            {"name": "Ижтимоий ходim", "phone": ["99-473-32-57"]},
            {"name": "Ёшlar етakчиси", "phone": ["99-610-19-95"]},
        ],
        "Тошлоқ МФЙ": [
            {"name": "МФЙ раиси", "phone": ["91-487-80-07"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["93-160-22-69"]},
            {"name": "Ҳокim ёрдамчиси", "phone": ["95-178-19-91"]},
            {"name": "Ижтимоiy ходim", "phone": ["77-155-59-99"]},
            {"name": "Ёшlar етakчиси", "phone": []},
        ],
        "Ўзбекистон МФЙ": [
            {"name": "МФЙ раиси", "phone": ["91-482-23-32"]},
            {"name": "Хотин-қизлар фаоли", "phone": ["93-160-22-69"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["99-436-65-61"]},
            {"name": "Ижтимоiy ходim", "phone": ["95-013-33-86"]},
            {"name": "Ёшlar етakчиси", "phone": ["91-477-56-80"]},
        ],
        "Ғайрат МФЙ": [
            {"name": "МФЙ раиси", "phone": ["97-990-70-02"]},
            {"name": "Хотин-қизlar фаoli", "phone": ["91-064-45-25"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["97-339-14-76"]},
            {"name": "Ижтимоiy ходim", "phone": ["90-253-00-76"]},
            {"name": "Ёшlar етakчиси", "phone": ["99-086-18-17"]},
        ],
        "Деҳқонобод МФЙ": [
            {"name": "МФЙ раиси", "phone": ["94-664-65-70"]},
            {"name": "Хотин-қизлар фаoli", "phone": ["94-106-88-82"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["94-388-92-98"]},
            {"name": "Ижтимоiy ходim", "phone": ["50-574-76-86"]},
            {"name": "Ёшlar етakчиси", "phone": ["90-311-11-95"]},
        ],
        "Ҳақиқат МФЙ": [
            {"name": "МФЙ раиси", "phone": ["93-255-12-76"]},
            {"name": "Хотин-қизлар фаoli", "phone": ["94-106-88-82"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["94-106-04-47"]},
            {"name": "Ижтимоiy ходim", "phone": ["94-433-19-15"]},
            {"name": "Ёшlar етakчиси", "phone": ["50-007-49-26"]},
        ],
        "Узун кўча МФЙ": [
            {"name": "МФЙ раиси", "phone": ["90-541-82-38"]},
            {"name": "Хотин-қизlar фаoli", "phone": ["91-064-45-25"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["88-221-80-08"]},
            {"name": "Ижтимоiy ходim", "phone": ["94-433-86-32"]},
            {"name": "Ёшlar етakчиси", "phone": ["93-772-95-35"]},
        ],
        "Қўртқи МФЙ": [
            {"name": "МФЙ раиси", "phone": ["99-475-20-65"]},
            {"name": "Хотин-қизlar фаoli", "phone": ["93-259-82-28"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["99-885-11-06"]},
            {"name": "Ижтимоiy ходim", "phone": ["77-443-50-59"]},
            {"name": "Ёшlar етakчиси", "phone": ["99-011-96-15"]},
        ],
        "Абдуллабий МФЙ": [
            {"name": "МФЙ раиси", "phone": ["93-212-79-97"]},
            {"name": "Хотин-қизlar фаoli", "phone": ["99-910-41-05"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["70-013-00-14"]},
            {"name": "Ижтимоiy ходim", "phone": ["93-134-41-71"]},
            {"name": "Ёшlar етakчиси", "phone": ["97-988-08-97"]},
        ],
        "Охунбобоев МФЙ": [
            {"name": "МФЙ раиси", "phone": ["91-173-75-69"]},
            {"name": "Хотин-қизлар фаoli", "phone": ["90-583-60-48"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["93-631-95-05"]},
            {"name": "Ижтимоiy ходim", "phone": ["91-497-19-99"]},
            {"name": "Ёшlar етakчиси", "phone": ["93-106-87-84"]},
        ],
        "Ибрат МФЙ": [
            {"name": "МФЙ раиси", "phone": ["99-313-02-83"]},
            {"name": "Хотин-қизlar фаoli", "phone": ["93-107-64-07"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["90-141-13-96"]},
            {"name": "Ижтимоiy ходim", "phone": ["97-773-51-51"]},
            {"name": "Ёшlar етakчиси", "phone": ["91-612-55-77"]},
        ],
        "Қаламбек МФЙ": [
            {"name": "МФЙ раиси", "phone": ["90-927-30-78"]},
            {"name": "Хотин-қизlar фаoli", "phone": ["99-910-41-05"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["77-008-00-36"]},
            {"name": "Ижтимоiy ходim", "phone": ["88-301-24-83"]},
            {"name": "Ёшlar етakчиси", "phone": ["91-477-56-80"]},
        ],
        "Кўтарма МФЙ": [
            {"name": "МФЙ раиси", "phone": ["93-788-83-67"]},
            {"name": "Хотин-қизlar фаoli", "phone": ["93-497-87-52"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["94-389-95-75"]},
            {"name": "Ижтимоiy ходim", "phone": ["93-700-41-11"]},
            {"name": "Ёшlar етakчиси", "phone": ["94-554-06-60"]},
        ],
        "Дўстлик МФЙ": [
            {"name": "МФЙ раиси", "phone": ["97-472-42-64"]},
            {"name": "Хотин-қизlar фаoli", "phone": ["93-107-64-07"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["94-430-62-02"]},
            {"name": "Ижтимоiy ходim", "phone": ["77-443-50-91"]},
            {"name": "Ёшlar етakчиси", "phone": ["88-161-23-93"]},
        ],
        "Бирлашган МФЙ": [
            {"name": "МФЙ раиси", "phone": ["91-610-21-45"]},
            {"name": "Хотин-қизlar фаoli", "phone": ["90-257-16-64"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["88-473-30-30"]},
            {"name": "Ижтимоiy ходim", "phone": ["91-172-37-38"]},
            {"name": "Ёшlar етakчиси", "phone": ["88-929-00-44"]},
        ],
        "Нефтчилар МФЙ": [
            {"name": "МФЙ раиси", "phone": ["91-493-55-62"]},
            {"name": "Хотин-қизlar фаoli", "phone": ["90-257-16-64"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["93-245-24-67"]},
            {"name": "Ижтимоiy ходim", "phone": ["99-110-12-27"]},
            {"name": "Ёшlar етakчиси", "phone": ["91-608-90-89"]},
        ],
        "Янги Ўзбекистон МФЙ": [
            {"name": "МФЙ раиси", "phone": ["94-051-10-01"]},
            {"name": "Хотин-қизlar фаoli", "phone": ["90-528-37-59"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["90-146-00-73"]},
            {"name": "Ижтимоiy ходim", "phone": ["91-615-07-09"]},
            {"name": "Ёшlar етakчиси", "phone": ["94-438-98-98"]},
        ],
        "Янги чек МФЙ": [
            {"name": "МФЙ раиси", "phone": ["91-487-19-76"]},
            {"name": "Хотин-қизlar фаoli", "phone": ["93-406-70-77"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["94-825-00-11"]},
            {"name": "Ижтимоiy ходim", "phone": ["88-991-79-79"]},
            {"name": "Ёшlar етakчиси", "phone": ["97-999-90-15"]},
        ],
        "Туялас МФЙ": [
            {"name": "МФЙ раиси", "phone": ["97-998-77-29"]},
            {"name": "Хотин-қизlar фаoli", "phone": ["91-109-17-99"]},
            {"name": "Ҳokim ёрдамчиси", "phone": ["91-496-03-03"]},
            {"name": "Ижтимоiy ходim", "phone": ["97-989-30-00"]},
            {"name": "Ёшlar етakчиси", "phone": ["93-473-01-60"]}, 
        ],
            # qolgan MFYlaringizni shu yerga xuddi shu formatda davom ettirasiz...
        },
    },
}

# ================== HELPERS ==================
def kb_rows_from_texts(texts: list[str], per_row: int = 2) -> list[list[KeyboardButton]]:
    rows, row = [], []
    for t in texts:
        row.append(KeyboardButton(t))
        if len(row) == per_row:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return rows


def main_menu_kb() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton("🏛 Tuman hokimligi"), KeyboardButton("🏢 Tuman tashkilotlari")],
        [KeyboardButton("🎓 Maktab"), KeyboardButton("🏫 Bog'cha")],
        [KeyboardButton("🏘 MFYlar")],
        [KeyboardButton("📨 Murojaat yo'llash")],
        [KeyboardButton("ℹ️ Yo'riqnoma")],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=False)


def list_items_kb(items: list[dict]) -> ReplyKeyboardMarkup:
    names = [it["name"] for it in items]
    rows = kb_rows_from_texts(names, per_row=2)
    rows.append([KeyboardButton("🔙 Orqaga")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=False)


def list_mahalla_kb(mahalla_names: list[str]) -> ReplyKeyboardMarkup:
    rows = kb_rows_from_texts(mahalla_names, per_row=2)
    rows.append([KeyboardButton("🔙 Orqaga")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=False)


# ================== STATE ==================
KEY_LEVEL = "level"
KEY_MFY_NAME = "mfy_name"

LV_MAIN = "main"
LV_HOK = "hokimlik"
LV_TASH = "tashkilotlar"
LV_TALIM = "talim"
LV_BOGCHA = "bogcha"
LV_MFY_LIST = "mfy_list"
LV_MFY_ROLES = "mfy_roles"
LV_MUROJAAT = "murojaat"


# ================== HANDLERS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data[KEY_LEVEL] = LV_MAIN
    context.user_data.pop(KEY_MFY_NAME, None)
    await update.message.reply_text("Ассалому алайкум!\nМенюдан танланг 👇", reply_markup=main_menu_kb())


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()
    lvl = context.user_data.get(KEY_LEVEL, LV_MAIN)
    logger.info("TEXT: %s | LVL: %s", txt, lvl)

    # ====== GLOBAL: Orqaga ======
    if txt == "🔙 Orqaga":
        if lvl in (LV_HOK, LV_TASH, LV_TALIM, LV_BOGCHA, LV_MFY_LIST):
            context.user_data[KEY_LEVEL] = LV_MAIN
            context.user_data.pop(KEY_MFY_NAME, None)
            await update.message.reply_text("Бош меню 👇", reply_markup=main_menu_kb())
            return

        if lvl == LV_MFY_ROLES:
            context.user_data[KEY_LEVEL] = LV_MFY_LIST
            context.user_data.pop(KEY_MFY_NAME, None)
            mahallas = list(DATA["mfy"]["mahallas"].keys())
            await update.message.reply_text("MFYлар рўйхати 👇", reply_markup=list_mahalla_kb(mahallas))
            return

        context.user_data[KEY_LEVEL] = LV_MAIN
        await update.message.reply_text("Бош меню 👇", reply_markup=main_menu_kb())
        return

    # ====== MAIN MENU ======
    if txt == "🏛 Tuman hokimligi":
        context.user_data[KEY_LEVEL] = LV_HOK
        await update.message.reply_text("Туман ҳокимлиги бўйича рўйхат 👇", reply_markup=list_items_kb(DATA["hokimlik"]["items"]))
        return

    if txt == "🏢 Tuman tashkilotlari":
        context.user_data[KEY_LEVEL] = LV_TASH
        await update.message.reply_text("Туман ташкилотлари рўйхати 👇", reply_markup=list_items_kb(DATA["tashkilotlar"]["items"]))
        return

    if txt == "🎓 Maktab":
        context.user_data[KEY_LEVEL] = LV_TALIM
        await update.message.reply_text("Maktab muassasalari рўйхати 👇", reply_markup=list_items_kb(DATA["Maktab"]["items"]))
        return

    if txt == "🏫 Bog'cha":
        context.user_data[KEY_LEVEL] = LV_BOGCHA
        await update.message.reply_text("Bog'cha muassasalari рўйхати 👇", reply_markup=list_items_kb(DATA["bogcha"]["items"]))
        return

    if txt == "🏘 MFYlar":
        context.user_data[KEY_LEVEL] = LV_MFY_LIST
        mahallas = list(DATA["mfy"]["mahallas"].keys())
        await update.message.reply_text("MFYлар рўйхати 👇", reply_markup=list_mahalla_kb(mahallas))
        return

    if txt == "📨 Murojaat yo'llash":
        context.user_data[KEY_LEVEL] = LV_MUROJAAT
        cancel_kb = ReplyKeyboardMarkup([[KeyboardButton("🔙 Orqaga")]], resize_keyboard=True)
        await update.message.reply_text(
            "📝 Мурожаат матнини ёзинг.\nXabaringiz guruhga yuboriladi:",
            reply_markup=cancel_kb,
        )
        return

    if txt == "ℹ️ Yo'riqnoma":
        await update.message.reply_text(
            "Йўриқнома:\n"
            "1) Бўлимни танланг\n"
            "2) Номни босинг\n"
            "3) Телефон рақами чиқади\n\n"
            "MFYда: аввал Mahalla → кейин Lavozim\n"
            "📨 Murojaat yo'llash — guruhga xabar yuborish",
            reply_markup=main_menu_kb(),
        )
        return

    # ====== MUROJAAT ======
    if lvl == LV_MUROJAAT:
        group_id = os.getenv("MUROJAAT_GROUP_ID", "").strip()
        user = update.effective_user
        full_name = user.full_name if user else "Noma'lum"
        username = f"@{user.username}" if (user and user.username) else "username yo'q"
        msg = (
            f"📨 Yangi murojaat:\n"
            f"👤 {full_name} ({username})\n"
            f"🆔 ID: {user.id if user else '?'}\n\n"
            f"💬 {txt}"
        )
        if group_id:
            try:
                await context.bot.send_message(chat_id=int(group_id), text=msg)
                await update.message.reply_text(
                    "✅ Мурожаатингиз юборилди! Тез орада жавоб берамиз.",
                    reply_markup=main_menu_kb(),
                )
            except Exception as e:
                logger.error("Guruhga yuborishda xato: %s", e)
                await update.message.reply_text(
                    "❌ Xatolik yuz berdi. Keyinroq urinib ko'ring.",
                    reply_markup=main_menu_kb(),
                )
        else:
            await update.message.reply_text(
                "⚠️ MUROJAAT_GROUP_ID sozlanmagan. .env faylga qo'shing.",
                reply_markup=main_menu_kb(),
            )
        context.user_data[KEY_LEVEL] = LV_MAIN
        return

    # ====== LISTS (HOKIMLIK/TASHKILOT/TALIM/BOGCHA) ======
    if lvl in (LV_HOK, LV_TASH, LV_TALIM, LV_BOGCHA):
        key = {
            LV_HOK: "hokimlik",
            LV_TASH: "tashkilotlar",
            LV_TALIM: "Maktab",
            LV_BOGCHA: "bogcha",
        }[lvl]

        items = DATA[key]["items"]
        item = next((x for x in items if x["name"] == txt), None)
        if item:
            icon = {
                "hokimlik": "🏛",
                "tashkilotlar": "🏢",
                "Maktab": "🎓",
                "bogcha": "🏫",
            }[key]
            await update.message.reply_text(
                f"{icon} {item['name']}\n📞 Телефон: {format_phones(item['phone'])}",
                reply_markup=list_items_kb(items),
            )
            return

    # ====== MFY LIST ======
    if lvl == LV_MFY_LIST and txt in DATA["mfy"]["mahallas"]:
        context.user_data[KEY_LEVEL] = LV_MFY_ROLES
        context.user_data[KEY_MFY_NAME] = txt
        roles = DATA["mfy"]["mahallas"][txt]
        await update.message.reply_text(f"🏘 {txt}\nЛавозимни танланг 👇", reply_markup=list_items_kb(roles))
        return

    # ====== MFY ROLES ======
    if lvl == LV_MFY_ROLES:
        mfy_name = context.user_data.get(KEY_MFY_NAME)
        if mfy_name and mfy_name in DATA["mfy"]["mahallas"]:
            roles = DATA["mfy"]["mahallas"][mfy_name]
            item = next((x for x in roles if x["name"] == txt), None)
            if item:
                await update.message.reply_text(
                    f"🏘 {mfy_name}\n👤 {item['name']}\n📞 Телефон: {format_phones(item['phone'])}",
                    reply_markup=list_items_kb(roles),
                )
                return

    await update.message.reply_text("Менюдан танланг 👇", reply_markup=main_menu_kb())


# ================== RUN ==================
def run():
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN topilmadi. .env faylga BOT_TOKEN=... qilib yozing!")

    webhook_url = os.getenv("WEBHOOK_URL", "").strip()
    port = int(os.getenv("PORT", "8443"))

    socket.setdefaulttimeout(30)

    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0,
        http_version="1.1",
    )

    app = Application.builder().token(token).request(request).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    if webhook_url:
        # ====== WEBHOOK REJIMI (server uchun) ======
        logger.info("Webhook rejimida ishga tushdi: %s", webhook_url)
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=token,
            webhook_url=f"{webhook_url}/{token}",
            drop_pending_updates=True,
        )
    else:
        # ====== POLLING REJIMI (local test uchun) ======
        logger.info("Polling rejimida ishga tushdi ✅")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run()
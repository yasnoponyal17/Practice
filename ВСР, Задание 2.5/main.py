import asyncio
import logging
import sys
import os
import random
import sqlite3
from datetime import datetime, UTC
from dataclasses import dataclass
import calendar
from typing import Any, Self
from enum import Enum

from dateutil.relativedelta import relativedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, ReplyKeyboardRemove, BotCommand, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from pyowm.config import DEFAULT_CONFIG as OWM_DEFAULT_CONFIG
from pyowm import OWM
from pyowm.weatherapi25.weather import Weather
from pyowm.weatherapi25.location import Location
from pyowm.commons.exceptions import NotFoundError as OwmNotFoundError

with open("./telegram_token.txt", "r") as f:
    TELEGRAM_TOKEN = f.read()
    
with open("./owm_token.txt", "r") as f:
    OWM_TOKEN = f.read()

OWM_CONFIG = OWM_DEFAULT_CONFIG | {
    'language': 'ru'
}

COUNTRY_CODE_TO_COUNTRY_NAME = {
    'AF': 'Афганистан',
    'AL': 'Албания',
    'DZ': 'Алжир',
    'AS': 'Американское Самоа',
    'AD': 'Андорра',
    'AO': 'Ангола',
    'AI': 'Ангилья',
    'AQ': 'Антарктика',
    'AG': 'Антигуа и Барбуда',
    'AR': 'Аргентина',
    'AM': 'Армения',
    'AW': 'Аруба',
    'AU': 'Австралия',
    'AT': 'Австрия',
    'AZ': 'Азербайджан',
    'BS': 'Багамы',
    'BH': 'Бахрейн',
    'BD': 'Бангладешь',
    'BB': 'Барбадос',
    'BY': 'Беларусь',
    'BE': 'Бельгия',
    'BZ': 'Белиз',
    'BJ': 'Бенин',
    'BM': 'Бермуды',
    'BT': 'Бутан',
    'BO': 'Bolivia',
    'BQ': 'Бонэйр',
    'BA': 'Босния и Герцеговина',
    'BW': 'Ботсвана',
    'BV': 'Остров Буве',
    'BR': 'Бразилия',
    'IO': 'Британская территория в Индийском океане',
    'BN': 'Бруней',
    'BG': 'Болгария',
    'BF': 'Буркина-Фасо',
    'BI': 'Бурунди',
    'KH': 'Камбоджа',
    'CM': 'Камерун',
    'CA': 'Канада',
    'CV': 'Кабо-Верде',
    'KY': 'Острова Кайман',
    'CF': 'ЦАР',
    'TD': 'Чад',
    'CL': 'Чили',
    'CN': 'Китай',
    'CX': 'Остров Рождества',
    'CC': 'Кокосовые острова',
    'CO': 'Колумбия',
    'KM': 'Коморы',
    'CG': 'Конго',
    'CD': 'Демократическая республика Конго',
    'CK': 'Острова Кука',
    'CR': 'Коста-Рика',
    'HR': 'Хорватия',
    'CU': 'Куба',
    'CW': 'Кюрасао',
    'CY': 'Кипр',
    'CZ': 'Чехия',
    'CI': "Кот-д'Ивуар",
    'DK': 'Дания',
    'DJ': 'Джибути',
    'DM': 'Доминика',
    'DO': 'Доминиканская Республика',
    'EC': 'Эквадор',
    'EG': 'Египт',
    'SV': 'Сальвадор',
    'GQ': 'Equatorial Guinea',
    'ER': 'Eritrea',
    'EE': 'Эстония',
    'ET': 'Эфиопия',
    'FK': 'Фолклендские острова',
    'FO': 'Фарерские острова',
    'FJ': 'Фиджи',
    'FI': 'Финляндия',
    'FR': 'Франция',
    'GF': 'Французская Гвиана',
    'PF': 'Французская Полинезия',
    'TF': 'Французские Южные и Антарктические Территории',
    'GA': 'Габон',
    'GM': 'Гамбия',
    'GE': 'Грузия',
    'DE': 'Германия',
    'GH': 'Гана',
    'GI': 'Гибралтар',
    'GR': 'Греция',
    'GL': 'Гренландия',
    'GD': 'Гренада',
    'GP': 'Гваделупа',
    'GU': 'Гуам',
    'GT': 'Гватемала',
    'GG': 'Гернси',
    'GN': 'Гвинея',
    'GW': 'Гвинея-Бисау',
    'GY': 'Гайана',
    'HT': 'Гаити',
    'HM': 'Остров Херд и остров Макдональд',
    'VA': 'Папский Престол (Государство-город Ватикан)',
    'HN': 'Гандурас',
    'HK': 'Гонк Конг',
    'HU': 'Венгрия',
    'IS': 'Исландия',
    'IN': 'Индия',
    'ID': 'Индонезия',
    'IR': 'Иран',
    'IQ': 'Ирак',
    'IE': 'Ирландия',
    'IM': 'остров Мэн',
    'IL': 'Израиль',
    'IT': 'Италия',
    'JM': 'Ямайка',
    'JP': 'Япония',
    'JE': 'Джерси',
    'JO': 'Иордания',
    'KZ': 'Казахстан',
    'KE': 'Кения',
    'KI': 'Кирибати',
    'KP': "КНДР",
    'KR': 'Корея',
    'KW': 'Кувейт',
    'KG': 'Кыргызстан',
    'LA': "Лаос",
    'LV': 'Латвия',
    'LB': 'Ливан',
    'LS': 'Лесото',
    'LR': 'Либерия',
    'LY': 'Ливия',
    'LI': 'Лихтенштейн',
    'LT': 'Литва',
    'LU': 'Люксембург',
    'MO': 'Макао',
    'MK': 'Македония',
    'MG': 'Мадагаскар',
    'MW': 'Малави',
    'MY': 'Малайзия',
    'MV': 'Мальдивы',
    'ML': 'Мали',
    'MT': 'Мальта',
    'MH': 'Маршалловы острова',
    'MQ': 'Мартиника',
    'MR': 'Мавритания',
    'MU': 'Маврикий',
    'YT': 'Майотта',
    'MX': 'Мексика',
    'FM': 'Микронезия',
    'MD': 'Молдова',
    'MC': 'Монако',
    'MN': 'Монголия',
    'ME': 'Черногория',
    'MS': 'Montserrat',
    'MA': 'Морокко',
    'MZ': 'Мозамбик',
    'MM': 'Мьянма (Бирма)',
    'NA': 'Намибия',
    'NR': 'Науру',
    'NP': 'Непал',
    'NL': 'Нидерланды',
    'NC': 'Новая Каледония',
    'NZ': 'Новая Зеландия',
    'NI': 'Никарагуа',
    'NE': 'Нигер',
    'NG': 'Нигерия',
    'NU': 'Ниуэ',
    'NF': 'Острова Норфолк',
    'MP': 'Северные Марианские острова',
    'NO': 'Норвегия',
    'OM': 'Оман',
    'PK': 'Пакистан',
    'PW': 'Палау',
    'PS': 'Палестина',
    'PA': 'Панама',
    'PG': 'Папуа Новая Гвинея',
    'PY': 'Парагвай',
    'PE': 'Перу',
    'PH': 'Филипины',
    'PN': 'острова Питкэрн',
    'PL': 'Польша',
    'PT': 'Португалия',
    'PR': 'Пуэрто-Рико',
    'QA': 'Катар',
    'RO': 'Румыния',
    'RU': 'Российская Федерация',
    'RW': 'Руанда',
    'RE': 'Реюньон',
    'BL': 'Сан-Бартелеми',
    'SH': 'остров Святой Елены',
    'KN': 'Сент-Китс и Невис',
    'LC': 'Сент-Люсия',
    'MF': 'Сен-Мертен',
    'PM': 'Сен-Пьер и Микелон',
    'VC': 'Сент-Винсент и Гренадины',
    'WS': 'Самоа',
    'SM': 'Сан-Марино',
    'ST': 'Сан-Томе и Принсипи',
    'SA': 'Саудовская Арабия',
    'SN': 'Сенегал',
    'RS': 'Сербия',
    'SC': 'Сейшеллы',
    'SL': 'Сьерра-Леоне',
    'SG': 'Сингапур',
    'SX': 'Синт-Мартен',
    'SK': 'Словакия',
    'SI': 'Словения',
    'SB': 'Соломоновы острова',
    'SO': 'Сомали',
    'ZA': 'Южная Африка',
    'GS': 'Южная Георгия и Южные Сандвичевы острова',
    'SS': 'Южный Судан',
    'ES': 'Испания',
    'LK': 'Шри Ланка',
    'SD': 'Судан',
    'SR': 'Суринам',
    'SJ': 'Шпицберген и Ян-Майен',
    'SZ': 'Эсватини',
    'SE': 'Швеция',
    'CH': 'Швейцария',
    'SY': 'Сирия',
    'TW': 'Тайвань',
    'TJ': 'Таджикистан',
    'TZ': 'Танзания',
    'TH': 'Тайланд',
    'TL': 'Восточный Тимор',
    'TG': 'Того',
    'TK': 'Токелау',
    'TO': 'Тонга',
    'TT': 'Тринидад и Тобаго',
    'TN': 'Тунис',
    'TR': 'Турция',
    'TM': 'Туркменистан',
    'TC': 'Острова Теркс и Кайкос',
    'TV': 'Тувалу',
    'UG': 'Уганда',
    'UA': 'Украина',
    'AE': 'ОАЭ',
    'GB': 'Великобритания',
    'US': 'США',
    'UM': 'Внешние малые о-ва (США)',
    'UY': 'Уругвай',
    'UZ': 'Узбекистан',
    'VU': 'Ванауту',
    'VE': 'Венесуэла',
    'VN': 'Вьетнам',
    'VG': 'Британские Виргинские острова',
    'VI': 'Американские Виргинские острова',
    'WF': 'острова Уоллис и Футуна',
    'EH': 'Западная Сахара',
    'YE': 'Йемен',
    'ZM': 'Замбия',
    'ZW': 'Зимбабве',
    "AX": "Аландские острова",
}

COUNTRY_CODE_TO_FLAG = {
    'AF': '🇦🇫',
    'AL': '🇦🇱',
    'DZ': '🇩🇿',
    'AS': '🇦🇸',
    'AD': '🇦🇩',
    'AO': '🇦🇴',
    'AI': '🇦🇮',
    'AQ': '🇦🇶',
    'AG': '🇦🇬',
    'AR': '🇦🇷',
    'AM': '🇦🇲',
    'AW': '🇦🇼',
    'AU': '🇦🇺',
    'AT': '🇦🇹',
    'AZ': '🇦🇿',
    'BS': '🇧🇸',
    'BH': '🇧🇭',
    'BD': '🇧🇩',
    'BB': '🇧🇧',
    'BY': '🇧🇾',
    'BE': '🇧🇪',
    'BZ': '🇧🇿',
    'BJ': '🇧🇯',
    'BM': '🇧🇲',
    'BT': '🇧🇹',
    'BO': '🇧🇴',
    'BQ': '🇧🇶',
    'BA': '🇧🇦',
    'BW': '🇧🇼',
    'BV': '🇧🇻',
    'BR': '🇧🇷',
    'IO': '🇮🇴',
    'BN': '🇧🇳',
    'BG': '🇧🇬',
    'BF': '🇧🇫',
    'BI': '🇧🇮',
    'KH': '🇰🇭',
    'CM': '🇨🇲',
    'CA': '🇨🇦',
    'CV': '🇨🇻',
    'KY': '🇰🇾',
    'CF': '🇨🇫',
    'TD': '🇹🇩',
    'CL': '🇨🇱',
    'CN': '🇨🇳',
    'CX': '🇨🇽',
    'CC': '🇨🇨',
    'CO': '🇨🇴',
    'KM': '🇰🇲',
    'CG': '🇨🇬',
    'CD': '🇨🇩',
    'CK': '🇨🇰',
    'CR': '🇨🇷',
    'HR': '🇭🇷',
    'CU': '🇨🇺',
    'CW': '🇨🇼',
    'CY': '🇨🇾',
    'CZ': '🇨🇿',
    'CI': '🇨🇮',
    'DK': '🇩🇰',
    'DJ': '🇩🇯',
    'DM': '🇩🇲',
    'DO': '🇩🇴',
    'EC': '🇪🇨',
    'EG': '🇪🇬',
    'SV': '🇸🇻',
    'GQ': '🇬🇶',
    'ER': '🇪🇷',
    'EE': '🇪🇪',
    'ET': '🇪🇹',
    'FK': '🇫🇰',
    'FO': '🇫🇴',
    'FJ': '🇫🇯',
    'FI': '🇫🇮',
    'FR': '🇫🇷',
    'GF': '🇬🇫',
    'PF': '🇵🇫',
    'TF': '🇹🇫',
    'GA': '🇬🇦',
    'GM': '🇬🇲',
    'GE': '🇬🇪',
    'DE': '🇩🇪',
    'GH': '🇬🇭',
    'GI': '🇬🇮',
    'GR': '🇬🇷',
    'GL': '🇬🇱',
    'GD': '🇬🇩',
    'GP': '🇬🇵',
    'GU': '🇬🇺',
    'GT': '🇬🇹',
    'GG': '🇬🇬',
    'GN': '🇬🇳',
    'GW': '🇬🇼',
    'GY': '🇬🇾',
    'HT': '🇭🇹',
    'HM': '🇭🇲',
    'VA': '🇻🇦',
    'HN': '🇭🇳',
    'HK': '🇭🇰',
    'HU': '🇭🇺',
    'IS': '🇮🇸',
    'IN': '🇮🇳',
    'ID': '🇮🇩',
    'IR': '🇮🇷',
    'IQ': '🇮🇶',
    'IE': '🇮🇪',
    'IM': '🇮🇲',
    'IL': '🇮🇱',
    'IT': '🇮🇹',
    'JM': '🇯🇲',
    'JP': '🇯🇵',
    'JE': '🇯🇪',
    'JO': '🇯🇴',
    'KZ': '🇰🇿',
    'KE': '🇰🇪',
    'KI': '🇰🇮',
    'KP': '🇰🇵',
    'KR': '🇰🇷',
    'KW': '🇰🇼',
    'KG': '🇰🇬',
    'LA': '🇱🇦',
    'LV': '🇱🇻',
    'LB': '🇱🇧',
    'LS': '🇱🇸',
    'LR': '🇱🇷',
    'LY': '🇱🇾',
    'LI': '🇱🇮',
    'LT': '🇱🇹',
    'LU': '🇱🇺',
    'MO': '🇲🇴',
    'MK': '🇲🇰',
    'MG': '🇲🇬',
    'MW': '🇲🇼',
    'MY': '🇲🇾',
    'MV': '🇲🇻',
    'ML': '🇲🇱',
    'MT': '🇲🇹',
    'MH': '🇲🇭',
    'MQ': '🇲🇶',
    'MR': '🇲🇷',
    'MU': '🇲🇺',
    'YT': '🇾🇹',
    'MX': '🇲🇽',
    'FM': '🇫🇲',
    'MD': '🇲🇩',
    'MC': '🇲🇨',
    'MN': '🇲🇳',
    'ME': '🇲🇪',
    'MS': '🇲🇸',
    'MA': '🇲🇦',
    'MZ': '🇲🇿',
    'MM': '🇲🇲',
    'NA': '🇳🇦',
    'NR': '🇳🇷',
    'NP': '🇳🇵',
    'NL': '🇳🇱',
    'NC': '🇳🇨',
    'NZ': '🇳🇿',
    'NI': '🇳🇮',
    'NE': '🇳🇪',
    'NG': '🇳🇬',
    'NU': '🇳🇺',
    'NF': '🇳🇫',
    'MP': '🇲🇵',
    'NO': '🇳🇴',
    'OM': '🇴🇲',
    'PK': '🇵🇰',
    'PW': '🇵🇼',
    'PS': '🇵🇸',
    'PA': '🇵🇦',
    'PG': '🇵🇬',
    'PY': '🇵🇾',
    'PE': '🇵🇪',
    'PH': '🇵🇭',
    'PN': '🇵🇳',
    'PL': '🇵🇱',
    'PT': '🇵🇹',
    'PR': '🇵🇷',
    'QA': '🇶🇦',
    'RO': '🇷🇴',
    'RU': '🇷🇺',
    'RW': '🇷🇼',
    'RE': '🇷🇪',
    'BL': '🇧🇱',
    'SH': '🇸🇭',
    'KN': '🇰🇳',
    'LC': '🇱🇨',
    'MF': '🇲🇫',
    'PM': '🇵🇲',
    'VC': '🇻🇨',
    'WS': '🇼🇸',
    'SM': '🇸🇲',
    'ST': '🇸🇹',
    'SA': '🇸🇦',
    'SN': '🇸🇳',
    'RS': '🇷🇸',
    'SC': '🇸🇨',
    'SL': '🇸🇱',
    'SG': '🇸🇬',
    'SX': '🇸🇽',
    'SK': '🇸🇰',
    'SI': '🇸🇮',
    'SB': '🇸🇧',
    'SO': '🇸🇴',
    'ZA': '🇿🇦',
    'GS': '🇬🇸',
    'SS': '🇸🇸',
    'ES': '🇪🇸',
    'LK': '🇱🇰',
    'SD': '🇸🇩',
    'SR': '🇸🇷',
    'SJ': '🇸🇯',
    'SZ': '🇸🇿',
    'SE': '🇸🇪',
    'CH': '🇨🇭',
    'SY': '🇸🇾',
    'TW': '🇹🇼',
    'TJ': '🇹🇯',
    'TZ': '🇹🇿',
    'TH': '🇹🇭',
    'TL': '🇹🇱',
    'TG': '🇹🇬',
    'TK': '🇹🇰',
    'TO': '🇹🇴',
    'TT': '🇹🇹',
    'TN': '🇹🇳',
    'TR': '🇹🇷',
    'TM': '🇹🇲',
    'TC': '🇹🇨',
    'TV': '🇹🇻',
    'UG': '🇺🇬',
    'UA': '🇺🇦',
    'AE': '🇦🇪',
    'GB': '🇬🇧',
    'US': '🇺🇸',
    'UM': '🇺🇲',
    'UY': '🇺🇾',
    'UZ': '🇺🇿',
    'VU': '🇻🇺',
    'VE': '🇻🇪',
    'VN': '🇻🇳',
    'VG': '🇻🇬',
    'VI': '🇻🇮',
    'WF': '🇼🇫',
    'EH': '🇪🇭',
    'YE': '🇾🇪',
    'ZM': '🇿🇲',
    'ZW': '🇿🇼',
    "AX": '🇦🇽',
}

@dataclass
class Reminder:
    id: int
    date: int
    text: str
    active: bool = True

class NewReminderState(StatesGroup):
    text = State()
    date = State()

class TimeUnit(Enum):
    YEAR = 1
    MONTH = 2
    DAY = 3
    HOUR = 4
    MINUTE = 5
    SECOND = 6

class ReminderAction(str, Enum):
    DELETE_COMPLETED = "delete_completed"

class ReminderCallback(CallbackData, prefix="reminder"):
    action: ReminderAction

REMINDERS: dict[int, list[Reminder]] = {}

WEATHER_COMMAND = BotCommand(command="weather", description="Получить прогноз погоды")
RPS_COMMAND = BotCommand(command="rps", description="Сыграть в камень, ножницы, бумага")
REMINDERS_COMMAND = BotCommand(command="reminders", description="Получить список всех напоминаний")
REMINDER_COMMAND = BotCommand(command="reminder", description="Создать напоминание")
CANCEL_COMMAND = BotCommand(command="cancel", description="Отменить текущее действие")

ALL_COMMANDS = [
    WEATHER_COMMAND,
    RPS_COMMAND,
    REMINDERS_COMMAND,
    REMINDER_COMMAND,
    CANCEL_COMMAND
]

START_MESSAGE = """
Здравствуйте!

Я бот, созданный при выполнении задания ВСР 2.5 по учебной практике 1 курса в РГПУ им. Герцена.

Мои возможности:
    - Показывать текущую погоду в любом городе мира с помощью команды /weather
    - Играть в камень, ножницы, бумага с помощью команды /rps
    - Создавать напоминания с помощью команды /reminder
    
Остальные команды:
    /cancel - Отменить текущее действие (Например создание напоминания)
    /reminders - Показать список всех напоминаний
"""

owm = OWM(OWM_TOKEN, config=OWM_CONFIG)
mgr = owm.weather_manager()

bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode="html"))
dp = Dispatcher()
reminder_router = Router()

def get_word_case(count: int, words: list[str]) -> str:
    ONE = 0
    FEW = 1
    OTHER = 2
    
    if (count % 10 == 1) and not (count % 100 == 11):
        return words[ONE]
    
    if (count % 100) > 11 and (count % 100) <= 15:
        return words[OTHER]
    
    if (count % 10 >= 2) and (count % 10 <= 4):
        return words[FEW]
    
    return words[OTHER]

def create_reminders_db(chat_id: int) -> None:
    database_file = f"./databases/{chat_id}.db"
    
    if os.path.exists(database_file):
        os.remove(database_file)
    
    with sqlite3.connect(database_file) as conn:
        conn.execute("CREATE TABLE Reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, expires_in INTEGER, content TEXT)")

def add_reminder(chat_id: int, text: str, date: int) -> None:
    database_file = f"./databases/{chat_id}.db"
    
    with sqlite3.connect(database_file) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO Reminders (expires_in, content) VALUES (?, ?)", (date, text))
        
        if not chat_id in REMINDERS:
            REMINDERS[chat_id] = []
        
        REMINDERS[chat_id].append(Reminder(cur.lastrowid, date, text))

def get_reminders(chat_id: int) -> list[Reminder]:
    database_file = f"./databases/{chat_id}.db"
    
    now = datetime.now()
    timestamp = calendar.timegm(now.timetuple())
    
    result = None
    with sqlite3.connect(database_file) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Reminders")
        result = cur.fetchall()
        
    def row_to_reminder(row: list[Any]) -> Reminder:
        id = int(row[0])
        date = int(row[1])
        text = str(row[2])
        active = timestamp < date
        
        return Reminder(id, date, text, active)
    
    return list(map(row_to_reminder, result))

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await asyncio.to_thread(create_reminders_db, message.chat.id)
    await message.answer(START_MESSAGE)

@dp.message(Command(WEATHER_COMMAND))
async def command_weather_handler(message: Message, command: CommandObject) -> None:
    if command.args is None or command.args.isspace():
        await message.answer("Вы не указали город.\nПример использования: /weather Санкт-Петербург")
        return
    
    try:
        observation = mgr.weather_at_place(command.args)
    except OwmNotFoundError:
        await message.answer("Город не найден :(")
        return
    
    w: Weather = observation.weather
    l: Location = observation.location
    
    detailed_status: str = w.detailed_status
    country_name = COUNTRY_CODE_TO_COUNTRY_NAME[l.country]
    temperature = w.temperature(unit="celsius")
    temp = int(round(temperature["temp"]))
    temp_max = int(round(temperature["temp_max"]))
    temp_min = int(round(temperature["temp_min"]))
    feels_like = int(round(temperature["feels_like"]))
    humidity = w.humidity
    
    wind = w.wind()
    wind_speed = wind["speed"]
    
    flag = COUNTRY_CODE_TO_FLAG[l.country]
    
    await message.answer(f"Место: <b>{l.name}, {country_name} {flag}</b>\nПогода: <b>{detailed_status.capitalize()}</b>\nТемпература: <b>{temp} °C</b>\nМакс. температура: <b>{temp_max} °C</b>\nМин. температура: <b>{temp_min} °C</b>\nОщущается как: <b>{feels_like} °C</b>\nВлажность: <b>{humidity}%</b>\nВетер: <b>{wind_speed} м/c</b>")

def get_current_reminders_text(reminders: list[Reminder]) -> str | None:
    if len(reminders) == 0:
        return None
    
    text = "Список напоминаний:\n"
    for i, reminder in enumerate(reminders, start=1):
        date = datetime.fromtimestamp(reminder.date, UTC).strftime("%H:%M, %d/%m/%Y")
        status = '\u231B' if reminder.active else '\u2705'
        text += f"{i}. {status} [{date}] {reminder.text}\n\n"
    return text

@dp.message(Command(REMINDERS_COMMAND))
async def command_reminders_handler(message: Message) -> None:
    reminders = await asyncio.to_thread(get_reminders, message.chat.id)
    if len(reminders) == 0:
        await message.answer("У вас нет напоминаний.")
        return
    
    text = get_current_reminders_text(reminders)
    
    completed_present = any(not reminder.active for reminder in reminders)
    
    reply_markup = None
    if completed_present:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Удалить завершённые напоминания", callback_data=ReminderCallback(action=ReminderAction.DELETE_COMPLETED).pack())
        reply_markup = keyboard.as_markup()
    
    await message.answer(text, reply_markup=reply_markup)

def delete_completed_reminders(chat_id: int) -> int:
    database_file = f"./databases/{chat_id}.db"
    
    reminders = REMINDERS[chat_id]
    
    deleted_count = 0
    
    with sqlite3.connect(database_file) as conn:
        for i in reversed(range(len(reminders))):
            reminder = reminders[i]
            if reminder.active: continue
            del reminders[i]
            
            conn.execute("DELETE FROM Reminders WHERE id = ?", (reminder.id,))
            deleted_count += 1
            
        conn.commit()
        
    return deleted_count
        

@dp.callback_query(ReminderCallback.filter(F.action == ReminderAction.DELETE_COMPLETED))
async def handle_delete_completed_reminders(query: CallbackQuery, callback_data: ReminderCallback, bot: Bot) -> None:
    action = callback_data.action
    
    chat_id = query.from_user.id
    
    if action == ReminderAction.DELETE_COMPLETED:
        reminders = REMINDERS[chat_id]
        
        if len(reminders) > 0:
            deleted_count = await asyncio.to_thread(delete_completed_reminders, chat_id)
            
            word = get_word_case(deleted_count, ("неактивное напоминание", "неактивных напоминания", "неактивных напоминаний"))
            
            new_text = f"Вы успешно удалили {deleted_count} {word}.\n"
            
            reminders_text = get_current_reminders_text(reminders)
            
            new_text += reminders_text if reminders_text else "На данный момент у вас нет напоминаний."
            
            await query.message.delete_reply_markup()
            await query.message.edit_text(new_text)
        else:
            await query.message.answer(f"У вас пока нет завершённых напоминаний.")
    
    await query.answer()

@reminder_router.message(Command(CANCEL_COMMAND))
@reminder_router.message(F.text.casefold() == "cancel")
async def new_reminder_cancel(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять.", reply_markup=ReplyKeyboardRemove())
        return
    
    await state.clear()
    await message.answer("Создание напоминания отменено.", reply_markup=ReplyKeyboardRemove())

@reminder_router.message(Command(REMINDER_COMMAND))
async def command_new_reminder_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
    
    await state.set_state(NewReminderState.text)
    await message.answer("Введите текст напоминания", reply_markup=ReplyKeyboardRemove())
    
@reminder_router.message(NewReminderState.text)
async def new_reminder_text(message: Message, state: FSMContext) -> None:
    await state.update_data(text=message.text)
    await state.set_state(NewReminderState.date)
    await message.answer("Теперь введите время и дату напоминания в формате: <b>ЧЧ:ММ ДД/ММ/ГГГГ</b>\n\nПримечание:\n<i>Дата не обязательна, по умолчанию - текущий день</i>")

@reminder_router.message(NewReminderState.date)
async def new_reminder_date(message: Message, state: FSMContext) -> None:
    example_date = "10:20 23/12/2025"
    
    date_time = message.text.split(" ")
    if len(date_time) == 0:
        await message.answer(f"Вы указали время и дату неправильно.\nПример: <b>{example_date}</b>")
        return
    
    t = date_time[0].split(":")
    if len(t) != 2:
        await message.answer(f"Вы указали время неправильно.\nПример: <b>{example_date}</b>")
        return
    
    try:
        hours = int(t[0])
    except ValueError:
        await message.answer(f"Вы указали время неправильно.\nПример: <b>{example_date}</b>")
        return
    
    if hours >= 24:
        await message.answer(f"Час должен быть меньше 24.\nПример: <b>{example_date}</b>")
        return
    
    if hours < 0:
        await message.answer(f"Час должен быть больше или равен нулю.\nПример: <b>{example_date}</b>")
        return
    
    try:
        minutes = int(t[1])
    except ValueError:
        await message.answer(f"Вы указали время неправильно.\nПример: <b>{example_date}</b>")
        return
    
    if minutes >= 60:
        await message.answer(f"Минуты должны быть меньше 60.\nПример: <b>{example_date}</b>")
        return
    
    if minutes < 0:
        await message.answer(f"Минуты должны быть больше или равны нулю.\nПример: <b>{example_date}</b>")
        return
    
    today = datetime.today()
    
    day = today.day
    month = today.month
    year = today.year
    
    if len(date_time) > 1:
        d = date_time[1].split('/')
        if len(d) != 3:
            await message.answer(f"Вы указали дату неправильно.\nПример: <b>{example_date}</b>")
            return

        try:
            day = int(d[0])
        except ValueError:
            await message.answer(f"Вы указали дату неправильно.\nПример: <b>{example_date}</b>")
            return
        
        if day < 0:
            await message.answer(f"День не может быть меньше <b>нуля</b>.\nПример: <b>{example_date}</b>")
            return
        
        try:
            month = int(d[1])
        except ValueError:
            await message.answer(f"Вы указали дату неправильно.\nПример: <b>{example_date}</b>")
            return
        
        if not 1 <= month <= 12:
            await message.answer(f"Месяц должен быть в диапазоне от <b>1</b> до <b>12</b>.\nПример: <b>{example_date}</b>")
            return
        
        try:
            year = int(d[2])
        except ValueError:
            await message.answer(f"Вы указали дату неправильно.\nПример: <b>{example_date}</b>")
            return
        
        _, max_days = calendar.monthrange(year, month)
        
        if day > max_days:
            await message.answer(f"Последний день месяца - <b>{max_days}</b>, а не <b>{day}</b>.\nПример: <b>{example_date}</b>")
            return
        
    now = datetime.now()
    now_timestamp = calendar.timegm(now.timetuple())
        
    date = datetime(year, month, day, hours, minutes)
    timestamp = calendar.timegm(date.timetuple())
    
    if timestamp < now_timestamp:
        await message.answer(f"Создание напоминания на прошедшую дату бессмыслено. Введите другую дату.")
        return
    
    data = await state.update_data(date=timestamp)
    
    await asyncio.to_thread(add_reminder, message.chat.id, data['text'], data['date'])

    diff_date = relativedelta(date, now)
    
    time_values = (
        (diff_date.years, TimeUnit.YEAR),
        (diff_date.months, TimeUnit.MONTH),
        (diff_date.days, TimeUnit.DAY),
        (diff_date.hours, TimeUnit.HOUR),
        (diff_date.minutes, TimeUnit.MINUTE),
        (diff_date.seconds, TimeUnit.SECOND)
    )
    
    add_comma = False
    notifies_in = ""
    for value, unit in time_values:
        if unit != TimeUnit.SECOND and value <= 0: continue
        
        if add_comma: notifies_in += ", "
        add_comma = True
        notifies_in += f"{value} "
        cases: tuple[str, str, str] = None
        match unit:
            case TimeUnit.YEAR: cases = ("год", "года", "лет")
            case TimeUnit.MONTH: cases = ("месяц", "месяца", "месяцев")
            case TimeUnit.DAY: cases = ("день", "дня", "дней")
            case TimeUnit.HOUR: cases = ("час", "часа", "часов")
            case TimeUnit.MINUTE: cases = ("минуту", "минуты", "минут")
            case TimeUnit.SECOND: cases = ("секунду", "секунды", "секунд")
        notifies_in += get_word_case(value, cases)
    notifies_in += '.'
    
    await message.answer(f"Напоминание успешно создано! Я напомню вам об этом через <b>{notifies_in}</b>")

    await state.clear()

async def check_reminders_expiration() -> None:
    now = datetime.now()
    timestamp = calendar.timegm(now.timetuple())
    
    for chat_id, reminders in REMINDERS.items():
        for reminder in reminders:
            if reminder.active and timestamp > reminder.date:
                reminder.active = False
                
                date = datetime.fromtimestamp(reminder.date, UTC).strftime("%H:%M, %d/%m/%Y")
                await bot.send_message(chat_id, f"Напоминание:\n\n{reminder.text}\n\n{date}")

class RpsVariant(Enum):
    ROCK = 1
    PAPER = 2
    SCISSORS = 3
    
    def from_name(name: str) -> Self | None:
        match name:
            case "камень": return RpsVariant.ROCK
            case "бумага": return RpsVariant.PAPER
            case "ножницы": return RpsVariant.SCISSORS
            case _: return None
    
    @property
    def name(self) -> str:
        match self:
            case RpsVariant.ROCK: return "камень"
            case RpsVariant.PAPER: return "бумага"
            case RpsVariant.SCISSORS: return "ножницы"
            
    @property
    def name_acusative(self) -> str:
        match self:
            case RpsVariant.ROCK: return "камень"
            case RpsVariant.PAPER: return "бумагу"
            case RpsVariant.SCISSORS: return "ножницы"

RPS_VARIANTS = [RpsVariant.ROCK, RpsVariant.PAPER, RpsVariant.SCISSORS]

RPS_MAP = {
    RpsVariant.ROCK: RpsVariant.SCISSORS,
    RpsVariant.PAPER: RpsVariant.ROCK,
    RpsVariant.SCISSORS: RpsVariant.PAPER
}

@dp.message(Command(RPS_COMMAND))
async def command_rps_handler(message: Message, command: CommandObject) -> None:
    if not command.args or command.args.isspace():
        await message.answer("Вы не выбрали предмет.\nПример использования: /rps камень")
        return
    
    user_variant = RpsVariant.from_name(command.args.lower())
    
    if user_variant is None:
        await message.answer(f"Такого варианта нет.\nВозможные варианты: {RpsVariant.ROCK.name}, {RpsVariant.SCISSORS.name}, {RpsVariant.PAPER.name}.")
        return
    
    variant = random.choice(RPS_VARIANTS)
    
    if RPS_MAP.get(user_variant) == variant:
        await message.answer(f"Вы выиграли! Я выбрал <b>{variant.name_acusative}</b>.")
    elif RPS_MAP.get(variant) == user_variant:
        await message.answer(f"Вы проиграли! Я выбрал <b>{variant.name_acusative}</b>.")
    else:
        await message.answer(f"Ничья! Я выбрал <b>{variant.name_acusative}</b>.")

def load_all_reminders() -> None:
    now = datetime.now()
    timestamp = calendar.timegm(now.timetuple())
    
    for address, _, files in os.walk("./databases/"):
        for name in files:
            chat_id = int(name[:-3])
            path = os.path.join(address, name)
            
            result = None
            with sqlite3.connect(path) as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM Reminders")
                result = cur.fetchall()
                
                reminders: list[Reminder] = []
                for id, date, text in result:
                    active = timestamp < date
                    reminders.append(Reminder(id, date, text, active=active))
                REMINDERS[chat_id] = reminders

async def main() -> None:
    await bot.set_my_commands(commands=ALL_COMMANDS)
    
    dp.include_router(reminder_router)
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_reminders_expiration, IntervalTrigger(seconds=10))
    scheduler.start()
    
    logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
    
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    load_all_reminders()
    asyncio.run(main())
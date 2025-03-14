import random
import json
import os
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# Вставьте ваш API-токен от @BotFather
API_TOKEN = '7909518801:AAGPuCgtmBXCaqg3usJmUAYEKNVAwDGx10c'

# Инициализация бота
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния для создания пресетов
class PresetForm(StatesGroup):
    name = State()
    dice = State()

# Файл для хранения пресетов
PRESET_FILE = 'presets.json'

# Загрузка пресетов из файла
def load_presets():
    if os.path.exists(PRESET_FILE):
        with open(PRESET_FILE, 'r') as f:
            return json.load(f)
    return {}

# Сохранение пресетов в файл
def save_presets(presets):
    with open(PRESET_FILE, 'w') as f:
        json.dump(presets, f)

# Инициализация пресетов
presets = load_presets()

# Главное меню
def get_main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("Бросить кубики", callback_data="roll_dice"),
        InlineKeyboardButton("Создать пресет", callback_data="create_preset"),
        InlineKeyboardButton("Мои пресеты", callback_data="show_presets")
    ]
    keyboard.add(*buttons)
    return keyboard

# Меню кубиков
def get_dice_menu():
    keyboard = InlineKeyboardMarkup(row_width=3)
    dice_types = ["d6", "d8", "d10", "d12", "d20", "d100"]
    buttons = [InlineKeyboardButton(d, callback_data=f"roll_{d}") for d in dice_types]
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton("Назад", callback_data="back_to_main"))
    return keyboard

# Стартовая команда
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот для бросания кубиков. Выбери действие:", reply_markup=get_main_menu())

# Бросить кубики
@dp.callback_query_handler(lambda c: c.data == "roll_dice")
async def roll_dice_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("Выбери кубик:", reply_markup=get_dice_menu())

# Выполнение броска
@dp.callback_query_handler(lambda c: c.data.startswith("roll_d"))
async def roll_dice(callback: types.CallbackQuery):
    dice_type = callback.data.split("_")[1]
    sides = int(dice_type[1:])
    result = random.randint(1, sides)
    await callback.message.edit_text(f"Результат броска {dice_type}: **{result}**", reply_markup=get_dice_menu(), parse_mode="Markdown")

# Создание пресета
@dp.callback_query_handler(lambda c: c.data == "create_preset")
async def start_preset_creation(callback: types.CallbackQuery, state: FSMContext):
    await PresetForm.name.set()
    await callback.message.edit_text("Введи название пресета (например, 'Бластмастер'):")
    await callback.answer()

@dp.message_handler(state=PresetForm.name)
async def process_preset_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await PresetForm.next()
    await message.reply("Введи кубики (пример: '3d100 + 4d20'):")

@dp.message_handler(state=PresetForm.dice)
async def process_preset_dice(message: types.Message, state: FSMContext):
    data = await state.get_data()
    preset_name = data['name']
    dice_input = message.text.lower().replace(" ", "")
    
    try:
        dice_list = []
        for part in dice_input.split("+"):
            count, sides = part.split("d")
            sides = int(sides)
            if sides not in [6, 8, 10, 12, 20, 100]:
                raise ValueError
            dice_list.append([int(count), sides])  # Список для JSON
        presets[preset_name] = dice_list
        save_presets(presets)
        await message.reply(f"Пресет '{preset_name}' сохранён!", reply_markup=get_main_menu())
    except (ValueError, IndexError):
        await message.reply("Ошибка! Используй формат '3d100 + 4d20' и кубики: d6, d8, d10, d12, d20, d100")
    
    await state.finish()

# Показать пресеты
@dp.callback_query_handler(lambda c: c.data == "show_presets")
async def show_presets(callback: types.CallbackQuery):
    if not presets:
        await callback.message.edit_text("Пресетов пока нет.", reply_markup=get_main_menu())
        return
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for name in presets.keys():
        keyboard.add(InlineKeyboardButton(name, callback_data=f"roll_preset_{name}"))
    keyboard.add(InlineKeyboardButton("Назад", callback_data="back_to_main"))
    await callback.message.edit_text("Выбери пресет:", reply_markup=keyboard)

# Бросок пресета
@dp.callback_query_handler(lambda c: c.data.startswith("roll_preset_"))
async def roll_preset(callback: types.CallbackQuery):
    preset_name = callback.data.replace("roll_preset_", "")
    dice_list = presets[preset_name]
    
    result_text = f"Бросок '{preset_name}':\n"
    for count, sides in dice_list:
        rolls = [random.randint(1, sides) for _ in range(count)]
        result_text += f"{count}d{sides}: {rolls} (сумма: {sum(rolls)})\n"
    
    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад", callback_data="show_presets"))
    await callback.message.edit_text(result_text, reply_markup=keyboard)

# Назад в главное меню
@dp.callback_query_handler(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text("Выбери действие:", reply_markup=get_main_menu())

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# ========== ВСТАВЬТЕ ВАШ ТОКЕН СЮДА ==========
TOKEN = "8834411550:AAEz9AtfDtL549MH9DPL5I7vDWSvFB_65Uc"
# =============================================

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Клавиатуры
main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📋 Отчет по кабинету")],
    [KeyboardButton(text="🧹 Общий отчет")],
    [KeyboardButton(text="❌ Отмена")]
], resize_keyboard=True)

yes_no_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]
], resize_keyboard=True)

cabinet_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="3 к"), KeyboardButton(text="5 к"), KeyboardButton(text="7 к")],
    [KeyboardButton(text="4 к"), KeyboardButton(text="6 к"), KeyboardButton(text="Другой")]
], resize_keyboard=True)

cleaning_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🧽 Поверхности протерты")],
    [KeyboardButton(text="💧 Вода налита (полная бутылка)")],
    [KeyboardButton(text="📦 Всё убрано")],
    [KeyboardButton(text="🧪 Установка промыта")],
    [KeyboardButton(text="✅ Готово")]
], resize_keyboard=True)

location_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="В стерильное")],
    [KeyboardButton(text="В нестерильное")],
    [KeyboardButton(text="В ЦСО")]
], resize_keyboard=True)

late_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🧽 Быстро протер поверхности")],
    [KeyboardButton(text="🧪 Инструменты в раковину ЦСО (НЕ в раствор)")],
    [KeyboardButton(text="📸 Сфотографировал")],
    [KeyboardButton(text="👤 Тегнул следующего")],
    [KeyboardButton(text="✅ Готово")]
], resize_keyboard=True)

lotki_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Мало"), KeyboardButton(text="Нормально"), KeyboardButton(text="Много")]
], resize_keyboard=True)

water_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Хватит на утро"), KeyboardButton(text="Мало — запустить дистиллятор")]
], resize_keyboard=True)

# Состояния
class CabinetReport(StatesGroup):
    cabinet = State()
    problems = State()
    problems_text = State()
    cleaning_items = State()
    n_count = State()
    s_count = State()
    location = State()
    flash_mirror = State()
    flash_mirror_text = State()
    stock = State()
    late_check = State()
    late_items = State()

class GeneralReport(StatesGroup):
    n_total = State()
    n_in_autoclave = State()
    n_in_nonsterile = State()
    n_in_sterile = State()
    s_total = State()
    s_location = State()
    lotki = State()
    water = State()
    mirrors = State()
    autoclave = State()
    distiller = State()
    journals_cso = State()
    journals_xray = State()
    cso_order = State()
    cso_devices = State()
    filters = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я помогу оформить отчет после смены.\n\n"
        "📋 Отчет по кабинету — для каждого кабинета\n"
        "🧹 Общий отчет — для дежурного ассистента\n\n"
        "Выбери тип отчета:",
        reply_markup=main_kb
    )

@dp.message(Command("cancel"))
@dp.message(F.text == "❌ Отмена")
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отчет отменен. Нажми /start для нового отчета.", reply_markup=main_kb)

# Отчет по кабинету
@dp.message(F.text == "📋 Отчет по кабинету")
async def cabinet_start(message: types.Message, state: FSMContext):
    await state.set_state(CabinetReport.cabinet)
    await message.answer("🔢 Номер кабинета:", reply_markup=cabinet_kb)

@dp.message(CabinetReport.cabinet)
async def cabinet_number(message: types.Message, state: FSMContext):
    await state.update_data(cabinet=message.text)
    await state.set_state(CabinetReport.problems)
    await message.answer("🩺 Всё ли работает?", reply_markup=yes_no_kb)

@dp.message(CabinetReport.problems)
async def cabinet_problems(message: types.Message, state: FSMContext):
    if message.text == "✅ Да":
        await state.update_data(problems="✅ Всё работает")
        await state.set_state(CabinetReport.cleaning_items)
        await message.answer("🧽 Что сделано? (выберите, в конце '✅ Готово')", reply_markup=cleaning_kb)
    else:
        await state.update_data(problems="❌ Есть неисправности")
        await state.set_state(CabinetReport.problems_text)
        await message.answer("📝 Что не работает?", reply_markup=ReplyKeyboardRemove())

@dp.message(CabinetReport.problems_text)
async def cabinet_problems_text(message: types.Message, state: FSMContext):
    await state.update_data(problems=f"❌ {message.text}")
    await state.set_state(CabinetReport.cleaning_items)
    await message.answer("🧽 Что сделано?", reply_markup=cleaning_kb)

@dp.message(CabinetReport.cleaning_items)
async def cabinet_cleaning(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cleaning_list = data.get("cleaning_list", [])
    
    if message.text == "✅ Готово":
        if cleaning_list:
            cleaning_text = "\n".join([f"✅ {item}" for item in cleaning_list])
            await state.update_data(cleaning=cleaning_text)
            await state.set_state(CabinetReport.n_count)
            await message.answer("🔢 Сколько наконечников (н)?", reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer("⚠️ Выберите хотя бы один пункт")
        return
    
    if message.text not in cleaning_list:
        cleaning_list.append(message.text)
        await state.update_data(cleaning_list=cleaning_list)
    await message.answer(f"✅ Добавлено. Еще или '✅ Готово'", reply_markup=cleaning_kb)

@dp.message(CabinetReport.n_count)
async def cabinet_n_count(message: types.Message, state: FSMContext):
    await state.update_data(n_count=message.text)
    await state.set_state(CabinetReport.s_count)
    await message.answer("🔢 Сколько сопел (с)?")

@dp.message(CabinetReport.s_count)
async def cabinet_s_count(message: types.Message, state: FSMContext):
    await state.update_data(s_count=message.text)
    await state.set_state(CabinetReport.location)
    await message.answer("📦 Куда положили?", reply_markup=location_kb)

@dp.message(CabinetReport.location)
async def cabinet_location(message: types.Message, state: FSMContext):
    await state.update_data(location=message.text)
    await state.set_state(CabinetReport.flash_mirror)
    await message.answer("💾 Флешку и зеркало вернули?", reply_markup=yes_no_kb)

@dp.message(CabinetReport.flash_mirror)
async def cabinet_flash(message: types.Message, state: FSMContext):
    if message.text == "✅ Да":
        await state.update_data(flash_mirror="✅ Флешка и зеркало на месте")
        await state.set_state(CabinetReport.stock)
        await message.answer("📦 Что брали со склада?", reply_markup=ReplyKeyboardRemove())
    else:
        await state.set_state(CabinetReport.flash_mirror_text)
        await message.answer("📝 Что не вернули?", reply_markup=ReplyKeyboardRemove())

@dp.message(CabinetReport.flash_mirror_text)
async def cabinet_flash_text(message: types.Message, state: FSMContext):
    await state.update_data(flash_mirror=f"⚠️ {message.text}")
    await state.set_state(CabinetReport.stock)
    await message.answer("📦 Что брали со склада?")

@dp.message(CabinetReport.stock)
async def cabinet_stock(message: types.Message, state: FSMContext):
    await state.update_data(stock=message.text if message.text else "Ничего")
    
    now = datetime.now()
    if now.hour >= 22:
        await state.set_state(CabinetReport.late_check)
        await message.answer("⏰ После 22:00. Дополнительные действия:", reply_markup=late_kb)
    else:
        await show_cabinet_report(message, state)

@dp.message(CabinetReport.late_check)
async def cabinet_late_items(message: types.Message, state: FSMContext):
    data = await state.get_data()
    late_list = data.get("late_list", [])
    
    if message.text == "✅ Готово":
        if late_list:
            late_text = "\n".join([f"✅ {item}" for item in late_list])
            await state.update_data(late_items=f"\n⏰ Смена после 22:00\n{late_text}")
        else:
            await state.update_data(late_items="")
        await show_cabinet_report(message, state)
        return
    
    if message.text not in late_list:
        late_list.append(message.text)
        await state.update_data(late_list=late_list)
    await message.answer(f"✅ Добавлено. Еще или '✅ Готово'", reply_markup=late_kb)

async def show_cabinet_report(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    report = f"""
📋 **ОТЧЕТ ПО КАБИНЕТУ {data.get('cabinet')}**

{data.get('problems')}

{data.get('cleaning')}

**Наконечники и сопла:**
• {data.get('n_count')}н
• {data.get('s_count')}с
• Место: {data.get('location')}

{data.get('flash_mirror')}

**Со склада:** {data.get('stock')}
{data.get('late_items', '')}

✅ Отметился на ресепшене
"""
    await message.answer(report, reply_markup=main_kb)
    await state.clear()

# Общий отчет
@dp.message(F.text == "🧹 Общий отчет")
async def general_start(message: types.Message, state: FSMContext):
    await message.answer("🧹 Общий отчет. Введите количество наконечников (всего):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(GeneralReport.n_total)

@dp.message(GeneralReport.n_total)
async def gen_n(message: types.Message, state: FSMContext):
    await state.update_data(n_total=message.text)
    await state.set_state(GeneralReport.n_in_autoclave)
    await message.answer("Из них в автоклаве?")

@dp.message(GeneralReport.n_in_autoclave)
async def gen_a(message: types.Message, state: FSMContext):
    await state.update_data(n_in_autoclave=message.text)
    await state.set_state(GeneralReport.n_in_nonsterile)
    await message.answer("В нестерильном?")

@dp.message(GeneralReport.n_in_nonsterile)
async def gen_ns(message: types.Message, state: FSMContext):
    await state.update_data(n_in_nonsterile=message.text)
    await state.set_state(GeneralReport.n_in_sterile)
    await message.answer("В стерильном?")

@dp.message(GeneralReport.n_in_sterile)
async def gen_s(message: types.Message, state: FSMContext):
    await state.update_data(n_in_sterile=message.text)
    await state.set_state(GeneralReport.s_total)
    await message.answer("Сколько сопел (с) всего?")

@dp.message(GeneralReport.s_total)
async def gen_st(message: types.Message, state: FSMContext):
    await state.update_data(s_total=message.text)
    await state.set_state(GeneralReport.s_location)
    await message.answer("Где лежат сопла?", reply_markup=location_kb)

@dp.message(GeneralReport.s_location)
async def gen_sloc(message: types.Message, state: FSMContext):
    await state.update_data(s_location=message.text)
    await state.set_state(GeneralReport.lotki)
    await message.answer("Смотровых лотков:", reply_markup=lotki_kb)

@dp.message(GeneralReport.lotki)
async def gen_lotki(message: types.Message, state: FSMContext):
    await state.update_data(lotki=message.text)
    await state.set_state(GeneralReport.water)
    await message.answer("Воды на утро:", reply_markup=water_kb)

@dp.message(GeneralReport.water)
async def gen_water(message: types.Message, state: FSMContext):
    await state.update_data(water=message.text)
    await state.set_state(GeneralReport.mirrors)
    await message.answer("Сколько окклюзионных зеркал в ЦСО?")

@dp.message(GeneralReport.mirrors)
async def gen_mirrors(message: types.Message, state: FSMContext):
    await state.update_data(mirrors=message.text)
    await state.set_state(GeneralReport.autoclave)
    await message.answer("Нужно запустить автоклав утром?", reply_markup=yes_no_kb)

@dp.message(GeneralReport.autoclave)
async def gen_auto(message: types.Message, state: FSMContext):
    await state.update_data(autoclave=message.text)
    await state.set_state(GeneralReport.distiller)
    await message.answer("Нужно запустить дистиллятор?", reply_markup=yes_no_kb)

@dp.message(GeneralReport.distiller)
async def gen_dist(message: types.Message, state: FSMContext):
    await state.update_data(distiller=message.text)
    await state.set_state(GeneralReport.journals_cso)
    await message.answer("Журнал ЦСО заполнен?", reply_markup=yes_no_kb)

@dp.message(GeneralReport.journals_cso)
async def gen_jcso(message: types.Message, state: FSMContext):
    await state.update_data(journals_cso=message.text)
    await state.set_state(GeneralReport.journals_xray)
    await message.answer("Журнал рентген-кабинета заполнен?", reply_markup=yes_no_kb)

@dp.message(GeneralReport.journals_xray)
async def gen_jxray(message: types.Message, state: FSMContext):
    await state.update_data(journals_xray=message.text)
    await state.set_state(GeneralReport.cso_order)
    await message.answer("Порядок в ЦСО наведен?", reply_markup=yes_no_kb)

@dp.message(GeneralReport.cso_order)
async def gen_order(message: types.Message, state: FSMContext):
    await state.update_data(cso_order=message.text)
    await state.set_state(GeneralReport.cso_devices)
    await message.answer("Приборы в ЦСО выключены?", reply_markup=yes_no_kb)

@dp.message(GeneralReport.cso_devices)
async def gen_devices(message: types.Message, state: FSMContext):
    await state.update_data(cso_devices=message.text)
    await state.set_state(GeneralReport.filters)
    await message.answer("Фильтры в компрессорной промыты?", reply_markup=yes_no_kb)

@dp.message(GeneralReport.filters)
async def gen_filters(message: types.Message, state: FSMContext):
    await state.update_data(filters=message.text)
    await show_general_report(message, state)

async def show_general_report(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    report = f"""
🧹 **ОБЩИЙ ОТЧЕТ ДЕЖУРНОГО АССИСТЕНТА**

**Наконечники:** всего {data.get('n_total')}н
• В автоклаве: {data.get('n_in_autoclave')}н
• В нестерильном: {data.get('n_in_nonsterile')}н
• В стерильном: {data.get('n_in_sterile')}н

**Сопла:** {data.get('s_total')}с, лежат {data.get('s_location')}

**Расходники:**
• Лотки: {data.get('lotki')}
• Вода: {data.get('water')}
• Зеркала: {data.get('mirrors')} шт

**Оборудование утром:**
• Автоклав: {data.get('autoclave')}
• Дистиллятор: {data.get('distiller')}

**Журналы:** ЦСО {data.get('journals_cso')}, рентген {data.get('journals_xray')}

**Дежурный ассистент:**
• Порядок в ЦСО: {data.get('cso_order')}
• Приборы выключены: {data.get('cso_devices')}
• Фильтры: {data.get('filters')}

✅ Отметился на ресепшене
"""
    await message.answer(report, reply_markup=main_kb)
    await state.clear()

async def main():
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

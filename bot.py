from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
from datetime import datetime, timedelta
import yaml
import aiosqlite
import aiofiles
import asyncio
import random
import string

# Зберігаємо інформацію про запити на підтвердження
reset_requests = {}

# Асинхронне завантаження конфігурації
async def load_config():
    async with aiofiles.open("config.yaml", "r") as file:
        content = await file.read()
        return yaml.safe_load(content)

# Асинхронне створення таблиці
async def init_db():
    async with aiosqlite.connect("dick.db") as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS sizes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                userid INTEGER,
                chatid INTEGER,
                username TEXT,
                expire_date TEXT,
                size INTEGER,
                UNIQUE(userid, chatid)
            )
        ''')
        await db.commit()

# Перевірка чи є користувач адміністратором
async def is_admin(client, message):
    # Якщо ID чату позитивний - це приватний чат
    if message.chat.id > 0:
        return False
    
    chat_member = await client.get_chat_member(message.chat.id, message.from_user.id)
    return chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

# Функція перевірки чи чат є приватним
def is_private_chat(chat_id):
    return chat_id > 0

# Генеруємо випадковий код для капчі
def generate_captcha_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Запускаємо ініціалізацію конфігу та БД перед стартом бота
async def main():
    global config
    config = await load_config()
    await init_db()

    # Ініціалізація бота
    bot = Client(
        "dick_bot",
        api_id=config["API_ID"],
        api_hash=config["API_HASH"],
        bot_token=config["BOT_TOKEN"]
    )

    # Команда /start
    @bot.on_message(filters.command("start"))
    async def start(client, message):
        await message.reply(f"""**Dick Bot | {config["bot_version"]}**
Бот працює лише в групових чатах. Раз в 24 години гравець може прописати команду /dick, щоб отримати випадковий розмір.
Наразі розмір від {config["random_min"]} до {config["random_max"]} см.
Якщо у тебе є питання — пиши /help.""")

    # Команда /help
    @bot.on_message(filters.command("help"))
    async def help(client, message):
        await message.reply("""**Команди бота:**
- /dick — вирощувати/зменшувати піську.
- /top_dick — топ 10 пісьок у групі.
- /global_top — глобальний топ 10 гравців.
- /tos — Полiтика конфіденційності та умови використання.
- /reset — скинути груповий чат (лише модераторам).""")


    @bot.on_message(filters.command("tos"))
    async def tos(client, message):
        if message.chat.id < 0:
            bot.reply_to(message, "Ця команда доступна лише в приватному чаті.")
            return
        await message.reply("""**Полiтика конфіденційності та умови використання**

**1. Загальні положення**
Цей бот призначений для використання у групових чатах та створений виключно з розважальною метою. Використовуючи бота, ви погоджуєтесь з цими умовами.

**2. Вікові обмеження**
Бот дозволено використовувати лише особам, які досягли 16-річного віку. Якщо вам менше 16 років, ви не маєте права користуватися ботом. Автор бота не несе відповідальності за використання його особами, які не відповідають віковому обмеженню.

**3. Збір та використання даних**
Бот зберігає такі дані користувачів:
- Ідентифікатор користувача Telegram (User ID)
- Ім'я користувача (Username)
- Ідентифікатор чату (Chat ID)
- Час використання команд
- Результати взаємодії з ботом

Ці дані використовуються виключно для коректного функціонування бота. Автор бота не передає ці дані третім особам і не використовує їх для інших цілей.

**4. Відповідальність**
Автор бота не несе відповідальності за будь-яке неправильне використання бота, а також за будь-які можливі наслідки його використання. Використання бота є добровільним, і кожен користувач бере на себе відповідальність за свої дії.

**5. Видалення даних**
Якщо ви бажаєте видалити свої дані, ви можете звернутися до адміністратора групи, де використовується бот, або припинити взаємодію з ботом.

**6. Зміни в умовах**
Автор залишає за собою право змінювати цю політику конфіденційності та умови використання в будь-який час без попереднього повідомлення. Актуальна версія документа завжди буде доступною в описі бота.

**7. Контакти**
Якщо у вас є питання щодо роботи бота, звертайтеся до його адміністратора або розробника через контактні дані, зазначені в офіційному каналі @nestor_churin

""")

    # Команда /dick
    @bot.on_message(filters.command("dick"))
    async def dick(client, message):
        # Перевіряємо чи це групове спілкування
        if is_private_chat(message.chat.id):
            await message.reply("Бот працює лише в групових чатах!")
            return
            
        user_id = message.from_user.id
        chat_id = message.chat.id
        username = message.from_user.username or f"user{user_id}"
        current_time = datetime.now()

        async with aiosqlite.connect("dick.db") as db:
            async with db.execute("SELECT size, expire_date FROM sizes WHERE userid = ? AND chatid = ?", (user_id, chat_id)) as cursor:
                result = await cursor.fetchone()

            if result:
                current_size, expire_date = result
                if expire_date:
                    expire_time = datetime.strptime(expire_date, "%Y-%m-%d %H:%M:%S")
                    if current_time < expire_time:
                        remaining_time = expire_time - current_time
                        hours, remainder = divmod(int(remaining_time.total_seconds()), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        time_str = f"{hours} год. {minutes} хв. {seconds} сек."
                        
                        await message.reply(f"""{username}, ти вже використовував цю команду.
Розмір твого пісюна: {current_size} см.
Наступна спроба через {time_str}.""")
                        return
                else:
                    current_size = 0
            else:
                current_size = 0

            # Генеруємо новий розмір
            size_change = random.randint(config["random_min"], config["random_max"])
            new_size = max(0, current_size + size_change)

            # Оновлюємо БД
            expire_new = (current_time + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
            await db.execute(
                "REPLACE INTO sizes (userid, chatid, username, expire_date, size) VALUES (?, ?, ?, ?, ?)",
                (user_id, chat_id, username, expire_new, new_size)
            )
            await db.commit()

            # Отримуємо рейтинг у групі
            async with db.execute("SELECT userid, size FROM sizes WHERE chatid = ? ORDER BY size DESC", (chat_id,)) as cursor:
                ranking = await cursor.fetchall()

            rank = next((i + 1 for i, (uid, sz) in enumerate(ranking) if uid == user_id), len(ranking))
            
            # Формуємо повідомлення з результатом
            emoji = "📈" if size_change > 0 else "📉"
            message_text = f"{username}, твій пісюн {'виріс на' if size_change > 0 else 'зменшився на'} {abs(size_change)} см {emoji}\n"
            message_text += f"Тепер він {new_size} см.\n"
            message_text += f"Ти займаєш {rank}-е місце в групі.\n"
            message_text += f"Твоя наступна спроба в {expire_new} за Київським часом."
            
            await message.reply(message_text)

    # Команда /top_dick - топ 10 у поточному чаті
    @bot.on_message(filters.command("top_dick"))
    async def top_dick(client, message):
        if is_private_chat(message.chat.id):
            await message.reply("Ця команда працює лише в групових чатах!")
            return
            
        chat_id = message.chat.id
        
        async with aiosqlite.connect("dick.db") as db:
            async with db.execute(
                "SELECT userid, username, size FROM sizes WHERE chatid = ? ORDER BY size DESC LIMIT 10", 
                (chat_id,)
            ) as cursor:
                top_users = await cursor.fetchall()
        
        if not top_users:
            await message.reply("У цьому чаті ще немає гравців!")
            return
            
        top_message = "**🏆 Топ 10 пісюнів у чаті:**\n\n"
        
        for idx, (userid, username, size) in enumerate(top_users, 1):
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
            top_message += f"{medal} {username}: {size} см\n"
        
        await message.reply(top_message)

    # Команда /global_top - глобальний топ 10
    @bot.on_message(filters.command("global_top"))
    async def global_top(client, message):
        async with aiosqlite.connect("dick.db") as db:
            async with db.execute(
                """SELECT username, MAX(size) as max_size 
                   FROM sizes 
                   GROUP BY userid 
                   ORDER BY max_size DESC 
                   LIMIT 10"""
            ) as cursor:
                global_top_users = await cursor.fetchall()
        
        if not global_top_users:
            await message.reply("Наразі немає гравців!")
            return
            
        top_message = "**🌍 Глобальний топ 10 пісюнів:**\n\n"
        
        for idx, (username, size) in enumerate(global_top_users, 1):
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
            top_message += f"{medal} {username}: {size} см\n"
        
        await message.reply(top_message)

    # Команда /reset - скидання результатів у групі (лише для адмінів)
    @bot.on_message(filters.command("reset"))
    async def reset(client, message):
        if is_private_chat(message.chat.id):
            await message.reply("Ця команда працює лише в групових чатах!")
            return
            
        # Перевіряємо чи відправник є адміністратором групи
        if not await is_admin(client, message):
            await message.reply("Ця команда доступна лише адміністраторам групи!")
            return
            
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Генеруємо капчу
        captcha_code = generate_captcha_code()
        reset_requests[f"{chat_id}_{user_id}"] = captcha_code
        
        # Створюємо клавіатуру з кнопками підтвердження та скасування
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✅ Підтвердити", callback_data=f"confirm_reset_{chat_id}"),
                    InlineKeyboardButton("❌ Скасувати", callback_data=f"cancel_reset_{chat_id}")
                ]
            ]
        )
        
        await message.reply(
            f"⚠️ **УВАГА!** ⚠️\n\n"
            f"Ви впевнені, що хочете скинути всі результати для цього чату?\n"
            f"Ця дія незворотна і видалить усі дані про розміри пісюнів у цьому чаті.\n\n"
            f"Для підтвердження, натисніть кнопку 'Підтвердити' та введіть цей код: **{captcha_code}**",
            reply_markup=keyboard
        )

    # Обробник кнопок для команди reset
    @bot.on_callback_query(filters.regex(r"^(confirm|cancel)_reset_"))
    async def reset_callback(client, callback_query):
        action, _, chat_id_str = callback_query.data.split("_", 2)
        chat_id = int(chat_id_str)
        user_id = callback_query.from_user.id
        
        # Перевіряємо чи користувач є адміністратором
        is_user_admin = False
        try:
            chat_member = await client.get_chat_member(chat_id, user_id)
            is_user_admin = chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
        except Exception:
            pass
        
        if not is_user_admin:
            await callback_query.answer("Ця дія доступна лише адміністраторам групи!", show_alert=True)
            return
        
        if action == "cancel":
            # Видаляємо запит на скидання
            key = f"{chat_id}_{user_id}"
            if key in reset_requests:
                del reset_requests[key]
            
            await callback_query.message.edit_text("❌ Операцію скасовано. Дані залишаються без змін.")
            await callback_query.answer("Операцію скасовано")
        else:  # confirm
            # Тут просимо ввести код-капчу
            await callback_query.message.edit_text(
                "Для завершення скидання, будь ласка, введіть код, який був показаний у повідомленні.\n"
                "Введіть /captcha КОД (наприклад, /captcha ABC123)"
            )
            await callback_query.answer("Введіть код для підтвердження")
    
    # Обробник для команди з капчею
    @bot.on_message(filters.command("captcha"))
    async def captcha_verification(client, message):
        if is_private_chat(message.chat.id):
            return
            
        # Перевіряємо чи відправник є адміністратором групи
        if not await is_admin(client, message):
            await message.reply("Ця команда доступна лише адміністраторам групи!")
            return
        
        chat_id = message.chat.id
        user_id = message.from_user.id
        key = f"{chat_id}_{user_id}"
        
        # Перевіряємо чи є активний запит
        if key not in reset_requests:
            await message.reply("Немає активного запиту на скидання даних!")
            return
        
        # Отримуємо введений код
        parts = message.text.split(" ", 1)
        if len(parts) != 2:
            await message.reply("Неправильний формат. Використовуйте: /captcha КОД")
            return
        
        entered_code = parts[1].strip().upper()
        expected_code = reset_requests[key]
        
        # Перевіряємо код
        if entered_code != expected_code:
            await message.reply("❌ Неправильний код! Операцію скасовано.")
            del reset_requests[key]
            return
        
        # Код правильний, виконуємо скидання
        async with aiosqlite.connect("dick.db") as db:
            await db.execute("DELETE FROM sizes WHERE chatid = ?", (chat_id,))
            await db.commit()
        
        # Видаляємо запит
        del reset_requests[key]
        
        await message.reply("✅ Код підтверджено! Всі дані для цього чату було видалено!")

    # Команда /my_dick - перевірка власних результатів
    @bot.on_message(filters.command("my_dick"))
    async def my_dick(client, message):
        if is_private_chat(message.chat.id):
            await message.reply("Ця команда працює лише в групових чатах!")
            return
            
        user_id = message.from_user.id
        chat_id = message.chat.id
        username = message.from_user.username or f"user{user_id}"
        
        async with aiosqlite.connect("dick.db") as db:
            async with db.execute(
                "SELECT size, expire_date FROM sizes WHERE userid = ? AND chatid = ?", 
                (user_id, chat_id)
            ) as cursor:
                result = await cursor.fetchone()
        
        if not result:
            await message.reply(f"{username}, ти ще не брав участі у грі. Використай команду /dick!")
            return
            
        size, expire_date = result
        current_time = datetime.now()
        expire_time = datetime.strptime(expire_date, "%Y-%m-%d %H:%M:%S")
        
        # Визначаємо час до наступної спроби
        if current_time < expire_time:
            remaining_time = expire_time - current_time
            hours, remainder = divmod(int(remaining_time.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours} год. {minutes} хв. {seconds} сек."
            cooldown_msg = f"Наступна спроба через {time_str}."
        else:
            cooldown_msg = "Ти можеш скористатися командою /dick прямо зараз!"
        
        async with aiosqlite.connect("dick.db") as db:
            async with db.execute(
                "SELECT COUNT(*) FROM sizes WHERE chatid = ? AND size > ?", 
                (chat_id, size)
            ) as cursor:
                rank = (await cursor.fetchone())[0] + 1
        
        message_text = f"{username}, розмір твого пісюна: {size} см.\n"
        message_text += f"Твій ранг: {rank} у цьому чаті.\n"
        message_text += cooldown_msg
        
        await message.reply(message_text)

    # Запуск бота
    await bot.start()
    print(f"Bot started! Version: {config['bot_version']}")
    
    # Тримаємо бота запущеним
    await asyncio.Event().wait()

# Запускаємо асинхронний main()
if __name__ == "__main__":
    asyncio.run(main())
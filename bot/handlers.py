import asyncio

from aiogram import Router, F
from aiogram.filters import CommandStart, Filter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from app.keyboards import main_menu_keyboard, contact_keyboard, admin_keyboard, confirmation_keyboard, \
    get_pagination_keyboard, back, user_back
from database.requests import add_user, get_role, add_stock, all_stock, get_stock, \
    delete_stock, manager_settings, get_manager, count_user
from settings.logging_config import setup_logger


logger = setup_logger("handlers")


class IsAdmin(Filter):
    async def __call__(self, message: Message):
        ADMIN_IDS = await get_role("admin")
        if message.from_user.id in ADMIN_IDS:
            return True
        else:
            await message.answer('Сообщение не распознано!'
                                 '\n\nИспользуйте кнопки в главном меню бота, вернуться в него вы можете нажав на команду -> /start 🙂')


user_router = Router()
admin_router = Router()
admin_router.message.filter(IsAdmin())


async def delete_previous_message(chat_id: int, message_id: int, bot):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        pass


@user_router.message(CommandStart())
@admin_router.callback_query(F.data == "start")
async def cmd_start(message: Message):
    try:
        await add_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
        manager = await get_manager()
        await message.answer("""
        🌸 Добро пожаловать в \"A cosmo\"!
        \nВаша красота — наш главный приоритет! С помощью этого бота вы можете:
        \n✨ Оставить заявку – подберем процедуру и удобное время
        \n✨ Задать вопрос менеджеру – эксперты ответят в чате
        \n✨ Получать VIP-скидки – закрытые акции и персональные предложения
        \nВыберите действие ниже ⤵️
        """, reply_markup=main_menu_keyboard(manager[0]))
    except Exception as err:
        logger.error(
            f"Error in cmd_start: {err} | User: {message.from_user.id}",
            exc_info=True
        )


@user_router.callback_query(F.data == "submit_your_application")
async def contact_manager(callback: CallbackQuery):
    try:
        await delete_previous_message(callback.message.chat.id, callback.message.message_id, callback.bot)
        sent_message = await callback.message.answer(
            "Нажмите кнопку ниже, чтобы отправить контакт менеджеру ⬇️",
            reply_markup=contact_keyboard
        )
        await callback.answer()
        from bot.bot_init import bot
        bot.contact_request_message_id = sent_message.message_id
    except Exception as err:
        logger.error(
            f"Error in contact_manager: {err} | User: {callback.from_user.id}",
            exc_info=True
        )


@user_router.message(F.contact)
async def handle_contact(message: Message):
    try:
        from bot.bot_init import bot
        if hasattr(bot, 'contact_request_message_id'):
            try:
                await message.bot.delete_message(message.chat.id, bot.contact_request_message_id)
            except:
                pass

        contact = message.contact
        manager = await get_role("manager")
        for id in manager:
            await bot.send_message(
                id,
                text=f"📌Поступила новая заявка:"
                     f"\nИмя: {contact.first_name}"
                     f"\nНомер: {contact.phone_number}"
            )

        await delete_previous_message(message.chat.id, message.message_id, message.bot)
        sent_message = await message.answer(
            "✨Ваша заявка успешно принята!\nЧерез 5 секунд Вы будете перенаправлены в главное меню!")

        await asyncio.sleep(5)

        await delete_previous_message(message.chat.id, sent_message.message_id, message.bot)

        await cmd_start(message)
    except Exception as err:
        logger.error(
            f"Error in handle_contact: {err} | User: {message.from_user.id}",
            exc_info=True
        )


@admin_router.message(Command('admin'))
@admin_router.callback_query(F.data == "home")
async def admin(message: Message | CallbackQuery):
    try:
        if isinstance(message, Message):
            await message.answer("""
            👑 Администратор \"A cosmo\"!
            \nДобро пожаловать в закрытый раздел управления!
            \nЗдесь вы можете:
            \n• ✨ Создать и удалять рассылку для клиентов
            \n• 🔐 Управлять доступом сотрудников (Можно добавить при желании)
            """, reply_markup=admin_keyboard)
        if isinstance(message, CallbackQuery):
            await delete_previous_message(message.message.chat.id, message.message.message_id, message.bot)
            await message.message.answer("""
            👑 Администратор \"A cosmo\"!
            \nДобро пожаловать в закрытый раздел управления!
            \nЗдесь вы можете:
            \n• ✨ Создать, просмотреть и удалять рассылку для клиентов
            \n• 🔐 Управлять доступом сотрудников (Можно добавить при желании)
            """, reply_markup=admin_keyboard)
            await message.answer()
    except Exception as err:
        logger.error(
            f"Error in admin: {err} | User: {message.from_user.id}",
            exc_info=True
        )


class ManagerStates(StatesGroup):
    waiting_for_username = State()


@admin_router.callback_query(F.data == "edit_manager")
async def new_manager(callback: CallbackQuery, state: FSMContext):
    try:
        await delete_previous_message(callback.message.chat.id, callback.message.message_id, callback.bot)
        await callback.message.answer("Введите username менеджера (например, @username или просто username):",
                                      reply_markup=back)
        await state.set_state(ManagerStates.waiting_for_username)
        await callback.answer()
    except Exception as err:
        logger.error(
            f"Error in new_manager: {err} | User: {callback.from_user.id}",
            exc_info=True
        )


@admin_router.message(ManagerStates.waiting_for_username)
async def process_manager_username(message: Message, state: FSMContext):
    try:
        username = message.text.strip().lstrip('@')
        res = await manager_settings(username)
        await message.answer(res, reply_markup=back)
        await state.clear()
    except Exception as err:
        logger.error(
            f"Error in process_manager_username: {err} | User: {message.from_user.id}",
            exc_info=True
        )


class PromotionCreation(StatesGroup):
    awaiting_name = State()
    awaiting_content = State()


@admin_router.callback_query(F.data == "make_newsletter")
async def make_newsletter(callback: CallbackQuery, state: FSMContext):
    try:
        await state.set_state(PromotionCreation.awaiting_name)
        await delete_previous_message(callback.message.chat.id, callback.message.message_id, callback.bot)
        await callback.message.answer("""
        🎀 Введите название акции (например: "Летний уход со скидкой 30%")
        \nЭто поможет вам легко найти эту рассылку в списке.
        """, reply_markup=back)
        await callback.answer()
    except Exception as err:
        logger.error(
            f"Error in make_newsletter: {err} | User: {callback.from_user.id}",
            exc_info=True
        )


@admin_router.message(PromotionCreation.awaiting_name)
async def handle_promotion_name(message: Message, state: FSMContext):
    try:
        await state.update_data(promotion_name=message.text)
        await state.set_state(PromotionCreation.awaiting_content)
        await message.answer(f"""
        🌺 Отлично! Акция \"{message.text}\" готова к оформлению.
        \n\nПришлите:
        \n1. Фото (рекомендуем качественное изображение процедуры)
        \n2. Краткий, но привлекательный текст для клиентов
        \n\nПример: "Подарите коже сияние молодости ❤️"
        """, reply_markup=back)
    except Exception as err:
        logger.error(
            f"Error in handle_promotion_name: {err} | User: {message.from_user.id}",
            exc_info=True
        )


@admin_router.message(PromotionCreation.awaiting_content, F.photo)
async def handle_promotion_content(message: Message, state: FSMContext):
    try:
        photo = message.photo[-1]
        caption = message.caption or ""

        data = await state.get_data()
        promotion_name = data.get('promotion_name')

        await state.update_data({
            'photo': photo.file_id,
            'caption': caption
        })

        await message.answer(
            f"""
            ✨ Подтвердите рассылку акции ✨
            \n🎀 Название: "{promotion_name}"
            """,
            reply_markup=confirmation_keyboard
        )
    except Exception as err:
        logger.error(
            f"Error in handle_promotion_content: {err} | User: {message.from_user.id}",
            exc_info=True
        )


@admin_router.callback_query(F.data.startswith('confirm'))
async def confirm_newsletter(callback: CallbackQuery, state: FSMContext):
    try:
        _, confirm = callback.data.split("_")


        if confirm == 'approve':
            data = await state.get_data()
            promotion_name = data.get('promotion_name')
            photo = data.get('photo')
            caption = data.get('caption')


            users = await get_role("users")
            sent_message_id = None

            for user_id in users:
                try:
                    sent_message = await callback.bot.send_message(
                        chat_id=user_id,
                        text="""
                            ✨ <b>Спешим поделиться радостной новостью! </b>✨
                            \n\nТолько что стартовала новая акция – скорее загляните в раздел «🛍️ Акции и предложения», чтобы первыми узнать все детали и успеть воспользоваться особыми условиями!
                            \n\n🔥 Не упустите выгоду – предложение ограничено! 🔥
                            """, parse_mode="HTML"
                        )
                    sent_message_id = sent_message.message_id
                except Exception as e:
                    print(f"😔Ошибка при отправке пользователю {user_id}: {e}")

            if sent_message_id:
                await add_stock(
                    title=promotion_name,
                    msg_id=callback.message.message_id,
                    photo_id=photo,
                    caption=caption
                )

            await delete_previous_message(callback.message.chat.id, callback.message.message_id, callback.bot)
            await callback.message.answer("🎉 Рассылка успешно отправлена!")
            await admin(callback)

        elif confirm == "deny":
            await delete_previous_message(callback.message.chat.id, callback.message.message_id, callback.bot)
            await callback.message.answer("😖Рассылка отменена. Нажмите 'Сделать рассылку' для новой попытки.", reply_markup=back)
        else:
            await delete_previous_message(callback.message.chat.id, callback.message.message_id, callback.bot)
            await callback.message.answer("Данные для рассылки не найдены!😔", reply_markup=back)

        await state.clear()
        await callback.answer()
    except Exception as err:
        logger.error(
            f"Error in confirm_newsletter: {err} | User: {callback.from_user.id}",
            exc_info=True
        )


@admin_router.callback_query(F.data == "all_promotions")
async def make_newsletter(callback: CallbackQuery):
    try:
        page = await all_stock()
        total_page = len(page)

        await delete_previous_message(callback.message.chat.id, callback.message.message_id, callback.bot)
        if total_page <= 0:
            await callback.message.answer("В данный момент нет действующих рассылок ☺️", reply_markup=back)
        else:
            await show_item(callback, 0, True)
        await callback.answer()
    except Exception as err:
        logger.error(
            f"Error in make_newsletter: {err} | User: {callback.from_user.id}",
            exc_info=True
        )


async def show_item(callback: CallbackQuery, current_page: int, admin: bool = False):
    try:
        from bot.bot_init import bot
        stock = await get_stock(current_page)

        page = await all_stock()
        total_page = len(page)

        caption = stock[1]
        photo = stock[2]


        try:
            await delete_previous_message(callback.message.chat.id, callback.message.message_id, callback.bot)
            await bot.send_photo(
                chat_id=callback.from_user.id,
                reply_markup=get_pagination_keyboard(current_page, total_page, admin),
                caption=caption,
                photo=photo
            )
        except Exception as ex:
            await callback.message.answer("Возникла ошибка, попробуйте позднее", reply_markup=user_back)
        await callback.answer()
    except Exception as err:
        logger.error(
            f"Error in show_item: {err} | User: {callback.from_user.id}",
            exc_info=True
        )


@admin_router.callback_query(F.data.startswith(("prev_", "next_")))
@user_router.callback_query(F.data.startswith(("prev_", "next_")))
async def handle_pagination(callback: CallbackQuery):
    try:
        action, page, admin = callback.data.split("_")

        if action == "prev":
            await show_item(callback, int(page) - 1, bool(admin))
        elif action == "next":
            await show_item(callback, int(page) + 1, bool(admin))
    except Exception as err:
        logger.error(
            f"Error in handle_paggination: {err} | User: {callback.from_user.id}",
            exc_info=True
        )


@admin_router.callback_query(F.data.startswith("delete_"))
async def handle_delete_stock(callback: CallbackQuery):
    try:
        _, page = callback.data.split("_")
        page = int(page)

        deleted_message_id = await delete_stock(page)

        users = await get_role("users")
        for user_id in users:
            try:
                await callback.bot.delete_message(chat_id=user_id, message_id=deleted_message_id)
            except Exception as e:
                print(f"😖Не удалось удалить сообщение у пользователя {user_id}: {e}")

        page = await all_stock()
        total_page = len(page)

        await delete_previous_message(callback.message.chat.id, callback.message.message_id, callback.bot)
        if total_page <= 0:
            await callback.message.answer("Рассылок пока нет 😴", reply_markup=back)
        else:
            await show_item(callback, 0, True)

        await callback.answer("Акция удалена! ☺️")
    except Exception as err:
        logger.error(
            f"Error in handle_delete_stock: {err} | User: {callback.from_user.id}",
            exc_info=True
        )


@user_router.callback_query(F.data == "user_home")
async def user_home(callback: CallbackQuery):
    try:
        await callback.message.delete()
        await cmd_start(callback.message)
    except Exception as err:
        logger.error(
            f"Error in user_home: {err} | User: {callback.from_user.id}",
            exc_info=True
        )


@user_router.callback_query(F.data == "promotions_and_offers")
async def handle_get_stock(callback: CallbackQuery):
    try:
        page = await all_stock()
        total_page = len(page)
        stock = await get_stock(0)
        print(stock)


        if total_page <= 0:
            await callback.message.delete()
            await callback.message.answer("В данный момент нет действующих предложений ☺️", reply_markup=user_back)
        else:
            await show_item(callback, 0)
        await callback.answer()
    except Exception as err:
        logger.error(
            f"Error in handle_get_stock: {err} | User: {callback.from_user.id}",
            exc_info=True
        )


@user_router.callback_query(F.data == "page_num")
async def handle_get_stock(callback: CallbackQuery):
    try:
        await callback.answer("Эта кнопка не нажимается 😊")
    except Exception as err:
        logger.error(
            f"Error in handle_get_stock: {err} | User: {callback.from_user.id}",
            exc_info=True
        )

@admin_router.message(Command('stat'))
async def admin(message: Message):
    count = await count_user()
    await message.answer(f"<b>Статистика:</b>"
                         f"\n👤Всего пользователей: {count['total']}"
                         f"\n💼Всего менеджеров: {count['managers']}"
                         f"\n👑Всего администраторов: {count['admins']}", parse_mode="HTML")
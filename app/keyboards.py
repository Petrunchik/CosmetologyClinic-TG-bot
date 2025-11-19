from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard(manager):
    main_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝Оставить заявку", callback_data="submit_your_application")],
        [InlineKeyboardButton(text="💬Связаться с менеджером", url=f"tg://resolve?domain={manager}&text=Здравствуйте!")],
        [InlineKeyboardButton(text="🛍️Акции и предложения", callback_data=f"promotions_and_offers")]
    ])
    return main_menu

contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="☎️Отправить контакт", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📢Создать рассылку", callback_data="make_newsletter")],
    [InlineKeyboardButton(text="📂Все рассылки", callback_data="all_promotions")],
    [InlineKeyboardButton(text="👤Изменить состояние менеджера", callback_data="edit_manager")],
])

confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅Да, все верно', callback_data='confirm_approve')],
    [InlineKeyboardButton(text='❌Нет, выбрать другие данные', callback_data='confirm_deny')]
])


confirmation_delete_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅Да, все верно', callback_data='confirm_delete_approve')],
    [InlineKeyboardButton(text='❌Нет, отмена', callback_data='confirm_delete_deny')]
])


back = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🏠 Вернуться", callback_data=f"home")]
])


user_back = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🏠 Вернуться", callback_data=f"user_home")]
])


def get_pagination_keyboard(current_index: int, total: int, admin: bool = False):
    builder = InlineKeyboardBuilder()

    if total == 1:
        pass

    elif current_index == 0:
        # Первая страница
        builder.row(
            InlineKeyboardButton(text=f"{current_index + 1}/{total}", callback_data="page_num"),
            InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"next_{current_index}_{admin}"),
            width=2
        )

    elif current_index + 1 == total:
        # Последняя страница
        builder.row(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"prev_{current_index}_{admin}"),
            InlineKeyboardButton(text=f"{current_index + 1}/{total}", callback_data="page_num"),
            width=2
        )

    elif 0 < current_index < total:
        # Остальные страницы
        builder.row(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"prev_{current_index}_{admin}"),
            InlineKeyboardButton(text=f"{current_index + 1}/{total}", callback_data="page_num"),
            InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"next_{current_index}_{admin}"),
            width=3
        )

    # Дополнительные кнопки
    if admin == True:
        builder.row(
            InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_{current_index}"),
            InlineKeyboardButton(text="🏠 Домой", callback_data="home"),
            width=2
        )
    elif admin == False:
        builder.row(
            InlineKeyboardButton(text="🏠 Домой", callback_data="user_home"),
            width=1
        )

    return builder.as_markup()
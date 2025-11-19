from sqlalchemy import select, update, exists, func
from database.models import User, Stock, async_session

from settings.logging_config import setup_logger

logger = setup_logger("database")

async def get_role(role):
    async with async_session() as session:
        try:
            if role == "manager":
                result = await session.scalars(
                    select(User.id).where(User.is_manager == True)
                )
                return result.all()

            elif role == "admin":
                result = await session.scalars(
                    select(User.id).where(User.is_admin == True)
                )
                return result.all()

            elif role == "users":
                result = await session.scalars(
                    select(User.id).where(User.is_admin == False)
                )
                return result.all()
        except Exception as err:
            logger.error(f"Failed to get role {role}:\nException: {err}", exc_info=True)



async def add_stock(title, msg_id, photo_id, caption):
    async with async_session() as session:
        try:
            session.add(Stock(title=title, message_id=msg_id, photo_id=photo_id, caption=caption))
            await session.commit()
        except Exception as err:
            logger.error(f"Failed to add stock {title}:\nException: {err}", exc_info=True)


async def all_stock():
    async with async_session() as session:
        try:
            result = await session.scalars(select(Stock.title, Stock.caption, Stock.photo_id).distinct())
            return result.all()
        except Exception as err:
            logger.error(f"Failed to get all stock:\nException: {err}", exc_info=True)


async def get_stock(stock_id: int):
    async with async_session() as session:
        try:
            result = await session.execute(
                select(Stock.title, Stock.caption, Stock.photo_id)
            )
            stocks = result.all()
            return stocks[stock_id] if stock_id < len(stocks) else None
        except Exception as err:
            logger.error(f"Failed to get stock {stock_id}:\nException: {err}", exc_info=True)


async def add_user(id, name, username):
    async with async_session() as session:
        try:
            exists = await session.scalar(
                select(select(User.id).where(User.id == id).exists())
            )
            if not exists:
                session.add(User(id=id, name=name, username=username))
                await session.commit()
        except Exception as err:
            logger.error(f"Failed to add user {id}:\nException: {err}", exc_info=True)


async def delete_stock(stock_id: int):
    async with async_session() as session:
        try:
            stock = await session.scalar(
                select(Stock).offset(stock_id).limit(1)
            )
            if not stock:
                return None

            msg_id = stock.message_id
            await session.delete(stock)
            await session.commit()
            return msg_id
        except Exception as err:
            logger.error(f"Failed to delete stock {stock_id}:\nException: {err}", exc_info=True)


async def manager_settings(username: str):
    async with async_session() as session:
        try:
            user_exists = await session.scalar(
                select(exists().where(User.username == username)))

            if not user_exists:
                return f"Ошибка: пользователь {username} не найден."

            current_status = await session.scalar(
                select(User.is_manager).where(User.username == username))
            new_status = not current_status

            if current_status and not new_status:
                managers_count = await session.scalar(
                    select(func.count()).where(User.is_manager == True))

                if managers_count <= 1:
                    return "Ошибка: нельзя удалить последнего менеджера. Назначьте другого менеджера перед этим."

            await session.execute(
                update(User)
                .where(User.username == username)
                .values(is_manager=new_status)
            )
            await session.commit()

            action = "добавлен" if new_status else "удален"
            return f"Менеджер {username} успешно {action}!"

        except Exception as err:
            await session.rollback()
            logger.error(f"Failed to change manager {username}:\nException: {err}", exc_info=True)
            return f"Ошибка в изменении менеджера: {str(err)}"


async def get_manager():
    async with async_session() as session:
        try:
            result = await session.scalars(
                select(User.username).where(User.is_manager == True)
            )
            return result.all()
        except Exception as err:
            logger.error(f"Failed to get manager:\nException: {err}", exc_info=True)

async def count_user():
    async with async_session() as session:
        try:
            from sqlalchemy import union_all, literal
            # Создаем подзапросы для каждого COUNT
            total_q = select(func.count().label("count"), literal("total").label("type")).select_from(User)
            managers_q = select(func.count(), literal("managers")).where(User.is_manager == True)
            admins_q = select(func.count(), literal("admins")).where(User.is_admin == True)

            # Объединяем в один запрос
            union_stmt = union_all(total_q, managers_q, admins_q)
            result = await session.execute(union_stmt)

            # Преобразуем в словарь
            rows = result.all()
            return {row[1]: row[0] for row in rows}
        except Exception as err:
            logger.error(f"Failed to count_user:\nException: {err}", exc_info=True)


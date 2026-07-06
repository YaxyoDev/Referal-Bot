"""Database: SQLAlchemy 2.0 (async) modellari va DB bilan ishlash funksiyalari."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    delete,
    func,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import DB_URL

# Async engine va sessiya yaratuvchi
engine = create_async_engine(DB_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Barcha modellar uchun asosiy klass."""
    pass


class User(Base):
    """Foydalanuvchi jadvali."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String, nullable=True)
    invite_link: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Referral(Base):
    """Taklif qilinganlar jadvali."""
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, index=True)  # Link egasi
    joined_user_id: Mapped[int] = mapped_column(BigInteger)  # Kirgan odam
    joined_user_name: Mapped[str] = mapped_column(String)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    left: Mapped[bool] = mapped_column(Boolean, default=False)  # Chiqib ketganmi

    # Bir odam bitta linkdan faqat 1 marta hisoblanadi
    __table_args__ = (UniqueConstraint("owner_id", "joined_user_id"),)


async def init_db():
    """Jadvallarni avtomatik yaratamiz (agar bo'lmasa)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_user(telegram_id: int) -> User | None:
    """Foydalanuvchini topadi, bo'lmasa None qaytaradi. Yaratmaydi."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def create_user(telegram_id: int, full_name: str, username: str | None, phone_number: str) -> User:
    """Yangi foydalanuvchi yaratadi (ism va telefon FSM orqali yig'ilgandan keyin chaqiriladi)."""
    async with async_session() as session:
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            phone_number=phone_number,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def set_invite_link(telegram_id: int, invite_link: str):
    """Foydalanuvchining shaxsiy invite linkini saqlaymiz."""
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(invite_link=invite_link)
        )
        await session.commit()


async def get_owner_by_link(invite_link: str) -> User | None:
    """Invite link egasini topamiz. Bizniki bo'lmasa None qaytadi."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.invite_link == invite_link)
        )
        return result.scalar_one_or_none()


async def add_referral(owner_id: int, joined_user_id: int, joined_user_name: str):
    """
    Yangi referal yozamiz. Agar bu juftlik oldin bor bo'lsa —
    qayta yozmaymiz, faqat left=False qilamiz (qaytib kelgan bo'lishi mumkin).
    """
    async with async_session() as session:
        result = await session.execute(
            select(Referral).where(
                Referral.owner_id == owner_id,
                Referral.joined_user_id == joined_user_id,
            )
        )
        referral = result.scalar_one_or_none()

        if referral is None:
            referral = Referral(
                owner_id=owner_id,
                joined_user_id=joined_user_id,
                joined_user_name=joined_user_name,
            )
            session.add(referral)
        else:
            referral.left = False  # Qaytib keldi — qayta faollashtiramiz

        await session.commit()


async def mark_referral_left(joined_user_id: int):
    """Kanaldan chiqib ketgan odamni left=True qilamiz (o'chirmaymiz)."""
    async with async_session() as session:
        await session.execute(
            update(Referral)
            .where(Referral.joined_user_id == joined_user_id)
            .values(left=True)
        )
        await session.commit()


async def count_referrals(owner_id: int) -> int:
    """Bitta odamning nechta faol (left=False) referali borligini sanaymiz."""
    async with async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Referral)
            .where(Referral.owner_id == owner_id, Referral.left == False)  # noqa: E712
        )
        return result.scalar_one()


async def get_top(limit: int = 10) -> list[tuple[str, str | None, str | None, int]]:
    """
    TOP reytingni qaytaramiz: [(full_name, username, phone_number, referallar_soni), ...].
    Faqat faol (left=False) referallar hisoblanadi.
    """
    async with async_session() as session:
        result = await session.execute(
            select(
                User.full_name,
                User.username,
                User.phone_number,
                func.count(Referral.id).label("cnt"),
            )
            .join(Referral, Referral.owner_id == User.telegram_id)
            .where(Referral.left == False)  # noqa: E712
            .group_by(User.telegram_id)
            .order_by(func.count(Referral.id).desc())
            .limit(limit)
        )
        return [(row.full_name, row.username, row.phone_number, row.cnt) for row in result.all()]


async def get_user_rank(telegram_id: int) -> tuple[int, int]:
    """
    Foydalanuvchining natijasi va o'rnini qaytaramiz: (referallar_soni, o'rin).
    Referali bo'lmasa (0, 0) qaytadi.
    """
    async with async_session() as session:
        # Har bir owner uchun faol referallar sonini sanaymiz
        subq = (
            select(
                Referral.owner_id,
                func.count(Referral.id).label("cnt"),
            )
            .where(Referral.left == False)  # noqa: E712
            .group_by(Referral.owner_id)
            .subquery()
        )
        result = await session.execute(
            select(subq.c.owner_id, subq.c.cnt).order_by(subq.c.cnt.desc())
        )
        rows = result.all()

    # O'rinni Python tomonda aniqlaymiz
    for position, row in enumerate(rows, start=1):
        if row.owner_id == telegram_id:
            return row.cnt, position
    return 0, 0


async def get_stats() -> tuple[int, int]:
    """Umumiy statistika: (foydalanuvchilar_soni, faol_referallar_soni)."""
    async with async_session() as session:
        users_count = await session.execute(select(func.count()).select_from(User))
        refs_count = await session.execute(
            select(func.count())
            .select_from(Referral)
            .where(Referral.left == False)  # noqa: E712
        )
        return users_count.scalar_one(), refs_count.scalar_one()


async def clear_referrals():
    """referrals jadvalini tozalaymiz (users jadvaliga TEGMAYMIZ)."""
    async with async_session() as session:
        await session.execute(delete(Referral))
        await session.commit()
async def clear_users():
    """users jadvalini tozalaymiz."""
    async with async_session() as session:
        await session.execute(delete(User))
        await session.commit()

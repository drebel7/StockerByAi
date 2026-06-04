from sqlalchemy import Column, Integer, String, Numeric, Date, SmallInteger, Boolean, BigInteger, ForeignKey, UniqueConstraint, Table
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Exchange(Base):
    __tablename__ = "exchanges"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    country = Column(String(10), nullable=False)

    companies = relationship("Company", back_populates="exchange")


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)


company_categories = Table(
    "company_categories", Base.metadata,
    Column("company_id", Integer, ForeignKey("companies.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True),
)


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), nullable=False)
    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False)
    full_name = Column(String(255), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    __table_args__ = (UniqueConstraint("ticker", "exchange_id"),)

    exchange = relationship("Exchange", back_populates="companies")
    categories = relationship("Category", secondary=company_categories)


class DailyQuote(Base):
    __tablename__ = "daily_quotes"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Numeric(12, 4))
    high = Column(Numeric(12, 4))
    low = Column(Numeric(12, 4))
    close = Column(Numeric(12, 4))
    volume = Column(BigInteger)
    __table_args__ = (UniqueConstraint("company_id", "date"),)


class Indicator(Base):
    __tablename__ = "indicators"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    date = Column(Date, nullable=False)
    sma_10d = Column(Numeric(12, 4))
    sma_20d = Column(Numeric(12, 4))
    sma_50d = Column(Numeric(12, 4))
    sma_200d = Column(Numeric(12, 4))
    obv_100d = Column(Numeric(20, 4))
    adr_30d = Column(Numeric(12, 4))
    atr_30d = Column(Numeric(12, 4))
    rs_value = Column(Numeric(12, 4))
    avg_volume_50d = Column(Numeric(20, 2))
    avg_turnover_50d = Column(Numeric(30, 2))
    __table_args__ = (UniqueConstraint("company_id", "date"),)


class Signal(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    date = Column(Date, nullable=False)
    signal_type = Column(String(100), nullable=False)
    value = Column(SmallInteger, nullable=False)
    __table_args__ = (UniqueConstraint("company_id", "date", "signal_type"),)


class SignalEffectiveness(Base):
    __tablename__ = "signal_effectiveness"
    id = Column(Integer, primary_key=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=False)
    close_at_signal = Column(Numeric(12, 4), nullable=False)
    return_10d = Column(Numeric(10, 4))
    return_20d = Column(Numeric(10, 4))
    return_50d = Column(Numeric(10, 4))
    drawdown_failed = Column(Boolean, default=False)
    low_10d = Column(Numeric(12, 4))
    high_10d = Column(Numeric(12, 4))


class SignalStatistic(Base):
    __tablename__ = "signal_statistics"
    id = Column(Integer, primary_key=True)
    signal_type = Column(String(100), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"))
    exchange_id = Column(Integer, ForeignKey("exchanges.id"))
    year = Column(SmallInteger, nullable=False)
    occurrences = Column(Integer, nullable=False, default=0)
    positive_count = Column(Integer, nullable=False, default=0)
    success_rate = Column(Numeric(6, 4))
    avg_return = Column(Numeric(10, 4))
    __table_args__ = (UniqueConstraint("signal_type", "company_id", "exchange_id", "year"),)

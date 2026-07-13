from sqlalchemy import Column, Integer, String, Float, Date, DateTime, SmallInteger, Boolean, ForeignKey, UniqueConstraint, Table
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Exchange(Base):
    __tablename__ = "exchanges"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    country = Column(String(10), nullable=False)
    active = Column(Boolean, nullable=False, default=True)

    instruments = relationship("Instrument", back_populates="exchange")


class DataSource(Base):
    __tablename__ = "data_sources"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    source = Column(String(20))


instrument_categories = Table(
    "instrument_categories", Base.metadata,
    Column("instrument_id", Integer, ForeignKey("instruments.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True),
)


class Instrument(Base):
    __tablename__ = "instruments"
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), nullable=False)
    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False)
    full_name = Column(String(255), nullable=False)
    instrument_type = Column(String(10), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    active = Column(Boolean, nullable=False, default=True)
    valid = Column(Boolean, nullable=False, default=True)
    dt_from = Column(Date)
    dt_to = Column(Date)
    market_cap = Column(Float)
    __table_args__ = (UniqueConstraint("ticker", "exchange_id"),)

    exchange = relationship("Exchange", back_populates="instruments")
    categories = relationship("Category", secondary=instrument_categories)


class DailyQuote(Base):
    __tablename__ = "daily_quotes"
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False, primary_key=True)
    dt = Column(Date, nullable=False, primary_key=True)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False)
    __table_args__ = (UniqueConstraint("instrument_id", "dt"),)


class IndicatorOld(Base):
    __tablename__ = "indicators_old"
    id = Column(Integer, primary_key=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    date = Column(Date, nullable=False)
    indicator_name = Column(String(50), nullable=False)
    value = Column(Float)
    parameters = Column(String(255))
    __table_args__ = (UniqueConstraint("instrument_id", "date", "indicator_name", "parameters"),)


class Indicator(Base):
    __tablename__ = "indicators"
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False, primary_key=True)
    dt = Column(Date, nullable=False, primary_key=True)
    sma_10 = Column(Float)
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    sma_200 = Column(Float)
    obv_100 = Column(Float)
    adr_30 = Column(Float)
    atr_30 = Column(Float)
    rs = Column(Float)
    avg_volume_50 = Column(Float)
    avg_turnover_50 = Column(Float)
    __table_args__ = (UniqueConstraint("instrument_id", "dt"),)


class Signal(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    date = Column(Date, nullable=False)
    signal_type = Column(String(100), nullable=False)
    value = Column(SmallInteger, nullable=False)
    __table_args__ = (UniqueConstraint("instrument_id", "date", "signal_type"),)


class SignalEffectiveness(Base):
    __tablename__ = "signal_effectiveness"
    id = Column(Integer, primary_key=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=False)
    close_at_signal = Column(Float, nullable=False)
    return_10d = Column(Float)
    return_20d = Column(Float)
    return_50d = Column(Float)
    return_100d = Column(Float)
    drawdown_failed = Column(Boolean, default=False)
    low_10d = Column(Float)
    high_10d = Column(Float)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    id = Column(Integer, primary_key=True)
    step = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="running")
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime)
    rows_affected = Column(Integer)


class SignalStatistic(Base):
    __tablename__ = "signal_statistics"
    id = Column(Integer, primary_key=True)
    signal_type = Column(String(100), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"))
    exchange_id = Column(Integer, ForeignKey("exchanges.id"))
    year = Column(SmallInteger, nullable=False)
    occurrences = Column(Integer, nullable=False, default=0)
    positive_count = Column(Integer, nullable=False, default=0)
    success_rate = Column(Float)
    avg_return = Column(Float)
    __table_args__ = (UniqueConstraint("signal_type", "instrument_id", "exchange_id", "year"),)
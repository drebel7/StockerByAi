from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import text, func
from sqlalchemy.orm import joinedload

from db.models import Instrument, Exchange, Category, instrument_categories, PipelineRun, Signal, SignalEffectiveness, SignalStatistic
from utils.database import get_session, engine

app = Flask(__name__)


@app.context_processor
def inject_nav():
    return {"active_page": request.path}


def _categories_with_counts():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT c.id, c.name, COUNT(ic.instrument_id) AS cnt
            FROM categories c
            LEFT JOIN instrument_categories ic ON ic.category_id = c.id
            GROUP BY c.id, c.name
            ORDER BY c.name
        """)).fetchall()
    return rows


def _get_instrument_query(session, exchange=None, inst_type=None, category=None, search=""):
    query = session.query(Instrument).join(Exchange, Instrument.exchange)
    if exchange:
        query = query.filter(Exchange.code == exchange)
    if inst_type:
        query = query.filter(Instrument.instrument_type == inst_type)
    if category:
        query = query.join(instrument_categories).join(Category).filter(Category.name == category)
    if search:
        query = query.filter(
            Instrument.ticker.ilike(f"%{search}%") | Instrument.full_name.ilike(f"%{search}%")
        )
    return query.options(joinedload(Instrument.exchange), joinedload(Instrument.categories))


@app.route("/")
def index():
    with engine.connect() as conn:
        instruments = conn.execute(text("SELECT COUNT(*) FROM instruments")).scalar()
        signals = conn.execute(text("SELECT COUNT(*) FROM signals")).scalar()
        categories = conn.execute(text("SELECT COUNT(*) FROM categories")).scalar()
        indicators = conn.execute(text("SELECT COUNT(*) FROM indicators")).scalar()
        categorized = conn.execute(text("SELECT COUNT(DISTINCT instrument_id) FROM instrument_categories")).scalar()

    session = get_session()
    try:
        runs = session.query(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(20).all()
    finally:
        session.close()

    return render_template("index.html", instruments=instruments, signals=signals,
                           categories=categories, indicators=indicators,
                           categorized=categorized, runs=runs)


@app.route("/instruments")
def instrument_list():
    session = get_session()
    try:
        exchange = request.args.get("exchange") or None
        inst_type = request.args.get("type") or None
        category = request.args.get("category") or None
        search = request.args.get("q", "").strip()

        page = request.args.get("page", 1, type=int)
        per_page = 50

        base = _get_instrument_query(session, exchange, inst_type, category, search)
        total = base.count()
        instruments = base.order_by(Instrument.ticker).offset((page - 1) * per_page).limit(per_page).all()

        exchanges = session.query(Exchange).order_by(Exchange.code).all()
        categories = _categories_with_counts()

        return render_template("instruments.html", instruments=instruments,
                               exchanges=exchanges, categories=categories,
                               selected_exchange=exchange or "",
                               selected_type=inst_type or "",
                               selected_category=category or "",
                               search=search, page=page, total=total, per_page=per_page)
    finally:
        session.close()


@app.route("/instruments/<int:inst_id>/categories", methods=["GET", "POST"])
def instrument_categories_edit(inst_id):
    session = get_session()
    try:
        inst = session.query(Instrument).options(joinedload(Instrument.categories)).get(inst_id)
        if not inst:
            return "Not found", 404

        if request.method == "POST":
            cat_ids = request.form.getlist("category_ids", type=int)
            session.query(instrument_categories).filter(
                instrument_categories.c.instrument_id == inst_id
            ).delete()
            for cid in cat_ids:
                session.execute(instrument_categories.insert().values(instrument_id=inst_id, category_id=cid))
            session.commit()
            return redirect(url_for("instrument_list", _anchor=f"inst-{inst_id}"))

        all_cats = session.query(Category).order_by(Category.name).all()
        assigned = {c.id for c in inst.categories}
        return render_template("instrument_categories.html", inst=inst,
                               all_categories=all_cats, assigned=assigned)
    finally:
        session.close()


@app.route("/indicators")
def indicator_list():
    with engine.connect() as conn:
        instrument_id = request.args.get("instrument_id", type=int)
        ticker_search = request.args.get("q", "").strip()

        indicators_cols = ["instrument_id", "dt", "sma_10", "sma_20", "sma_50", "sma_200",
                           "obv_100", "adr_30", "atr_30", "rs", "avg_volume_30", "avg_volume_50", "avg_turnover_50"]

        if instrument_id:
            query = "SELECT dt"
            for c in indicators_cols[2:]:
                query += f", {c}"
            query += " FROM indicators WHERE instrument_id = :iid ORDER BY dt DESC LIMIT 200"
            rows = conn.execute(text(query), {"iid": instrument_id}).fetchall()
            indicators = [dict(r._mapping) for r in rows]
        else:
            indicators = []

        if ticker_search:
            inst_rows = conn.execute(text("""
                SELECT i.id, i.ticker, i.full_name, e.code AS exchange
                FROM instruments i
                JOIN exchanges e ON e.id = i.exchange_id
                WHERE i.ticker ILIKE :q OR i.full_name ILIKE :q
                ORDER BY i.ticker LIMIT 20
            """), {"q": f"%{ticker_search}%"}).fetchall()
        else:
            inst_rows = []

    return render_template("indicators.html", indicators=indicators,
                           indicators_cols=indicators_cols[2:],
                           instrument_id=instrument_id, ticker_search=ticker_search,
                           instruments=inst_rows)


@app.route("/signals")
def signal_list():
    session = get_session()
    try:
        signal_type = request.args.get("signal_type") or None
        search = request.args.get("q", "").strip()
        page = request.args.get("page", 1, type=int)
        per_page = 50

        query = session.query(Signal, Instrument).join(Instrument, Signal.instrument_id == Instrument.id)
        if signal_type:
            query = query.filter(Signal.signal_type == signal_type)
        if search:
            query = query.filter(Instrument.ticker.ilike(f"%{search}%"))

        total = query.count()
        rows = query.order_by(Signal.date.desc()).offset((page - 1) * per_page).limit(per_page).all()
        signals = [{"id": s.id, "ticker": i.ticker, "date": s.date, "signal_type": s.signal_type, "value": s.value} for s, i in rows]

        types = [r[0] for r in session.query(Signal.signal_type).distinct().all()]

        return render_template("signals.html", signals=signals, types=types,
                               selected_type=signal_type or "", search=search,
                               page=page, total=total, per_page=per_page)
    finally:
        session.close()


@app.route("/statistics")
def statistics_view():
    with engine.connect() as conn:
        signal_type = request.args.get("signal_type") or None
        category_name = request.args.get("category") or None
        year = request.args.get("year", type=int) or None

        query = """
            SELECT ss.signal_type, ss.year, ss.occurrences, ss.positive_count,
                   ss.success_rate, ss.avg_return,
                   i.ticker, i.full_name, e.code AS exchange,
                   c.name AS category
            FROM signal_statistics ss
            JOIN instruments i ON i.id = ss.instrument_id
            JOIN exchanges e ON e.id = i.exchange_id
            LEFT JOIN instrument_categories ic ON ic.instrument_id = i.id
            LEFT JOIN categories c ON c.id = ic.category_id
            WHERE 1=1
        """
        params = {}
        if signal_type:
            query += " AND ss.signal_type = :st"
            params["st"] = signal_type
        if category_name:
            query += " AND c.name = :cat"
            params["cat"] = category_name
        if year:
            query += " AND ss.year = :yr"
            params["yr"] = year

        query += " ORDER BY ss.success_rate DESC NULLS LAST LIMIT 200"
        rows = conn.execute(text(query), params).fetchall()
        stats = [dict(r._mapping) for r in rows]

        types = [r[0] for r in conn.execute(text("SELECT DISTINCT signal_type FROM signal_statistics")).fetchall()]
        years = [r[0] for r in conn.execute(text("SELECT DISTINCT year FROM signal_statistics ORDER BY year DESC")).fetchall()]
        categories = _categories_with_counts()

    return render_template("statistics.html", stats=stats, types=types,
                           years=years, categories=categories,
                           selected_type=signal_type or "",
                           selected_category=category_name or "",
                           selected_year=year or "")


@app.route("/pipeline")
def pipeline_view():
    session = get_session()
    try:
        runs = session.query(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(200).all()
    finally:
        session.close()

    with engine.connect() as conn:
        latest = conn.execute(text("""
            SELECT step, status, started_at, finished_at
            FROM pipeline_runs
            ORDER BY started_at DESC
            LIMIT 1
        """)).fetchone()

    return render_template("pipeline.html", runs=runs, latest=latest)


@app.route("/api/pipeline/current")
def pipeline_current():
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT step, status, started_at, finished_at, rows_affected
            FROM pipeline_runs
            ORDER BY started_at DESC
            LIMIT 1
        """)).fetchone()
    if not row:
        return jsonify({"step": None, "status": "none"})
    return jsonify({
        "step": row.step,
        "status": row.status,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
        "rows_affected": row.rows_affected,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)

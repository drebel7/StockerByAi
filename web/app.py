from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import text

from db.models import Instrument, Exchange, Category, instrument_categories, PipelineRun, Indicator
from utils.database import get_session, engine

app = Flask(__name__)


@app.route("/pipeline")
def pipeline_status():
    session = get_session()
    try:
        runs = session.query(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(100).all()
        return render_template("pipeline.html", runs=runs)
    finally:
        session.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/instruments")
def instrument_list():
    session = get_session()
    try:
        exchange = request.args.get("exchange")
        inst_type = request.args.get("type")
        category = request.args.get("category")
        search = request.args.get("q", "").strip()

        query = session.query(Instrument).join(Exchange)

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

        instruments = query.order_by(Instrument.ticker).all()
        exchanges = session.query(Exchange).order_by(Exchange.code).all()
        categories = session.query(Category).order_by(Category.name).all()

        return render_template(
            "instruments.html",
            instruments=instruments,
            exchanges=exchanges,
            categories=categories,
            selected_exchange=exchange or "",
            selected_type=inst_type or "",
            selected_category=category or "",
            search=search,
        )
    finally:
        session.close()


@app.route("/indicators", methods=["GET", "POST"])
def indicator_list():
    session = get_session()
    try:
        if request.method == "POST":
            name = request.form.get("indicator_name", "").strip()
            params = request.form.get("parameters", "").strip() or None
            if name:
                existing = session.query(Indicator).filter_by(indicator_name=name, parameters=params).first()
                if not existing:
                    session.add(Indicator(
                        instrument_id=1, date="2000-01-01",
                        indicator_name=name, value=None, parameters=params,
                    ))
                    session.commit()
            return redirect(url_for("indicator_list"))

        rows = session.execute(text("""
            SELECT indicator_name, parameters, COUNT(*) as total
            FROM indicators
            GROUP BY indicator_name, parameters
            ORDER BY indicator_name, parameters
        """)).fetchall()
        return render_template("indicators.html", indicators=rows)
    finally:
        session.close()


@app.route("/indicators/delete", methods=["POST"])
def indicator_delete():
    name = request.form.get("indicator_name")
    params = request.form.get("parameters") or None
    session = get_session()
    try:
        session.query(Indicator).filter_by(indicator_name=name, parameters=params).delete()
        session.commit()
        return redirect(url_for("indicator_list"))
    finally:
        session.close()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
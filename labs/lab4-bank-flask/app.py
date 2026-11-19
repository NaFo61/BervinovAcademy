"""Flask entry point: bank product catalog with GET filters."""

from pathlib import Path

from flask import Flask, abort, render_template, request, send_from_directory

from logic import all_audiences, filtered_products, init_db, is_safe_image_name

app = Flask(__name__)
IMAGES_DIR = Path(__file__).resolve().parent / "static" / "catalog_images"


@app.before_request
def ensure_db() -> None:
    init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/products")
def products():
    cleared = "clearFilter" in request.args
    name_value = "" if cleared else (request.args.get("name") or "").strip()
    audience_value = "" if cleared else (request.args.get("audience_id") or "")
    description_value = "" if cleared else (request.args.get("description") or "").strip()
    cost_value = "" if cleared else (request.args.get("tariff_cost") or "").strip()

    audiences = all_audiences()
    items = filtered_products(request.args)

    return render_template(
        "products.html",
        audiences=audiences,
        products=items,
        name_value=name_value,
        audience_value=audience_value,
        description_value=description_value,
        cost_value=cost_value,
    )


@app.route("/images/<path:filename>")
def catalog_image(filename: str):
    if not is_safe_image_name(filename):
        abort(404)
    return send_from_directory(IMAGES_DIR, filename)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)

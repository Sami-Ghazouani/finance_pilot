import os
from decimal import Decimal, InvalidOperation
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import psycopg
from psycopg.rows import dict_row

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")

STATUSES = ("À faire", "En cours", "Terminée")
PRIORITIES = ("Basse", "Normale", "Haute")
CATEGORIES = ("Logement", "Courses", "Transport", "Études", "Loisirs", "Autre")


def db_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        dbname=os.getenv("POSTGRES_DB", "finance_db"),
        user=os.getenv("POSTGRES_USER", "finance_user"),
        password=os.getenv("POSTGRES_PASSWORD", "finance_password"),
        row_factory=dict_row,
    )


def init_db():
    with db_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(160) NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                status VARCHAR(20) NOT NULL DEFAULT 'À faire',
                priority VARCHAR(20) NOT NULL DEFAULT 'Normale',
                category VARCHAR(40) NOT NULL DEFAULT 'Autre',
                amount NUMERIC(10,2) NOT NULL DEFAULT 0,
                due_date DATE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CHECK (status IN ('À faire', 'En cours', 'Terminée')),
                CHECK (priority IN ('Basse', 'Normale', 'Haute')),
                CHECK (amount >= 0)
            )
        """)


def parse_amount(value):
    try:
        amount = Decimal((value or "0").replace(",", "."))
        if not amount.is_finite() or amount < 0 or amount > Decimal("99999999.99"):
            raise InvalidOperation
        return amount
    except (InvalidOperation, ValueError):
        raise ValueError("Le montant doit être un nombre positif ou nul.")


def task_form_data():
    title = request.form.get("title", "").strip()
    if not title:
        raise ValueError("Le titre est obligatoire.")
    if len(title) > 160:
        raise ValueError("Le titre ne doit pas dépasser 160 caractères.")
    status = request.form.get("status", "À faire")
    priority = request.form.get("priority", "Normale")
    category = request.form.get("category", "Autre")
    if status not in STATUSES or priority not in PRIORITIES or category not in CATEGORIES:
        raise ValueError("Une des valeurs sélectionnées n'est pas valide.")
    due_date = request.form.get("due_date") or None
    return {
        "title": title,
        "details": request.form.get("details", "").strip()[:2000],
        "status": status,
        "priority": priority,
        "category": category,
        "amount": parse_amount(request.form.get("amount", "0")),
        "due_date": due_date,
    }


@app.before_request
def ensure_schema():
    # Idempotent: safe to run on app start and useful in simple classroom deployments.
    init_db()


@app.get("/")
def dashboard():
    search = request.args.get("q", "").strip()[:100]
    status_filter = request.args.get("status", "")
    category_filter = request.args.get("category", "")
    if status_filter and status_filter not in STATUSES:
        status_filter = ""
    if category_filter and category_filter not in CATEGORIES:
        category_filter = ""

    conditions, params = [], []
    if search:
        conditions.append("(title ILIKE %s OR details ILIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])
    if status_filter:
        conditions.append("status = %s")
        params.append(status_filter)
    if category_filter:
        conditions.append("category = %s")
        params.append(category_filter)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""

    with db_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE status='Terminée') AS completed, "
                    "COALESCE(SUM(amount) FILTER (WHERE status <> 'Terminée'),0) AS pending_amount FROM tasks")
        stats = cur.fetchone()
        cur.execute("SELECT * FROM tasks" + where +
                    " ORDER BY CASE priority WHEN 'Haute' THEN 1 WHEN 'Normale' THEN 2 ELSE 3 END, "
                    "due_date NULLS LAST, created_at DESC", params)
        tasks = cur.fetchall()
        cur.execute("SELECT category, COALESCE(SUM(amount),0) AS total FROM tasks "
                    "WHERE status <> 'Terminée' GROUP BY category ORDER BY total DESC")
        category_totals = cur.fetchall()

    return render_template(
        "dashboard.html", tasks=tasks, stats=stats, category_totals=category_totals,
        q=search, status_filter=status_filter, category_filter=category_filter,
        statuses=STATUSES, priorities=PRIORITIES, categories=CATEGORIES
    )


@app.post("/tasks")
def create_task():
    try:
        data = task_form_data()
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute("""INSERT INTO tasks
                (title, details, status, priority, category, amount, due_date)
                VALUES (%(title)s, %(details)s, %(status)s, %(priority)s, %(category)s,
                        %(amount)s, %(due_date)s)""", data)
        flash("La tâche a été ajoutée.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("dashboard"))


@app.post("/tasks/<int:task_id>/update")
def update_task(task_id):
    try:
        data = task_form_data()
        data["id"] = task_id
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute("""UPDATE tasks SET title=%(title)s, details=%(details)s,
                status=%(status)s, priority=%(priority)s, category=%(category)s,
                amount=%(amount)s, due_date=%(due_date)s WHERE id=%(id)s""", data)
            if cur.rowcount == 0:
                flash("Tâche introuvable.", "error")
            else:
                flash("Les modifications ont été enregistrées.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("dashboard"))


@app.post("/tasks/<int:task_id>/status")
def update_status(task_id):
    status = request.form.get("status", "")
    if status not in STATUSES:
        flash("Statut invalide.", "error")
    else:
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute("UPDATE tasks SET status=%s WHERE id=%s", (status, task_id))
            flash("Statut mis à jour." if cur.rowcount else "Tâche introuvable.",
                  "success" if cur.rowcount else "error")
    return redirect(url_for("dashboard"))


@app.post("/tasks/<int:task_id>/delete")
def delete_task(task_id):
    with db_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
        flash("Tâche supprimée." if cur.rowcount else "Tâche introuvable.",
              "success" if cur.rowcount else "error")
    return redirect(url_for("dashboard"))


@app.get("/api/tasks")
def api_tasks():
    with db_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, title, details, status, priority, category, amount, due_date, created_at "
                    "FROM tasks ORDER BY created_at DESC")
        rows = cur.fetchall()
    return jsonify({"tasks": [
        {**row, "amount": float(row["amount"]),
         "due_date": row["due_date"].isoformat() if row["due_date"] else None,
         "created_at": row["created_at"].isoformat()}
        for row in rows
    ]})


@app.get("/health")
def health():
    try:
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception:
        return {"status": "error", "database": "unavailable"}, 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)

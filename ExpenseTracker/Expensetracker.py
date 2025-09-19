from flask import Flask, render_template, request, redirect, url_for
import datetime
import calendar

app = Flask(__name__)
EXPENSE_FILE = "expenses.csv"
BUDGET_FILE = "budget.txt"
DEFAULT_BUDGET = 2000.0

class Expense:
    def __init__(self, name: str, amount: float, category: str):
        self.name = name
        self.amount = amount
        self.category = category

def read_expenses():
    expenses = []
    try:
        with open(EXPENSE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",", 2)
                if len(parts) < 3:
                    continue
                name = parts[0].strip()
                try:
                    amount = float(parts[1].strip())
                except ValueError:
                    continue
                category = parts[2].strip()
                expenses.append(Expense(name, amount, category))
    except FileNotFoundError:
        pass
    return expenses

def append_expense(expense: Expense):
    with open(EXPENSE_FILE, "a", encoding="utf-8", newline="") as f:
        f.write(f"{expense.name},{expense.amount:.2f},{expense.category}\n")

def delete_expense_by_index(index: int):
    try:
        with open(EXPENSE_FILE, "r", encoding="utf-8") as f:
            lines = [ln for ln in f if ln.strip()]
    except FileNotFoundError:
        return False
    if index < 0 or index >= len(lines):
        return False
    del lines[index]
    with open(EXPENSE_FILE, "w", encoding="utf-8", newline="") as f:
        for ln in lines:
            f.write(ln.rstrip("\n") + "\n")
    return True

def read_budget():
    try:
        with open(BUDGET_FILE, "r", encoding="utf-8") as f:
            val = f.read().strip()
            return float(val) if val else DEFAULT_BUDGET
    except (FileNotFoundError, ValueError):
        return DEFAULT_BUDGET

def write_budget(value: float):
    try:
        with open(BUDGET_FILE, "w", encoding="utf-8") as f:
            f.write(f"{value:.2f}")
    except Exception:
        pass

def summarize(expenses, budget_value):
    by_cat = {}
    for e in expenses:
        by_cat[e.category] = by_cat.get(e.category, 0.0) + e.amount
    total = sum(e.amount for e in expenses)
    remaining = budget_value - total
    now = datetime.datetime.now()
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    remaining_days = days_in_month - now.day
    daily = remaining if remaining_days <= 0 else remaining / remaining_days
    return by_cat, total, remaining, daily

@app.route("/", methods=["GET"])
def index():
    budget = read_budget()
    expenses = read_expenses()
    by_cat, total, remaining, daily = summarize(expenses, budget)
    categories = ["🍔 Food","🏠 Home","💼 Work","🎉 Fun","✨ Misc"]
    return render_template("index.html",
                           expenses=expenses,
                           by_cat=by_cat,
                           total=total,
                           remaining=remaining,
                           daily=daily,
                           categories=categories,
                           budget=budget)

@app.route("/add", methods=["POST"])
def add():
    name = request.form.get("name", "").strip() or "Unnamed"
    amount_str = request.form.get("amount", "0").strip()
    try:
        amount = float(amount_str)
    except ValueError:
        amount = 0.0
    category = request.form.get("category", "✨ Misc").strip()
    e = Expense(name, amount, category)
    append_expense(e)
    return redirect(url_for("index"))

@app.route("/delete/<int:idx>", methods=["POST"])
def delete(idx):
    delete_expense_by_index(idx)
    return redirect(url_for("index"))

@app.route("/set_budget", methods=["POST"])
def set_budget():
    bstr = request.form.get("budget", "").strip()
    try:
        bval = float(bstr)
        if bval < 0:
            bval = DEFAULT_BUDGET
    except ValueError:
        bval = DEFAULT_BUDGET
    write_budget(bval)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
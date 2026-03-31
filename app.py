from flask import Flask, render_template, request, redirect, url_for, session
from bson.objectid import ObjectId
# from config import users_collection, daily_expenses_collection, trips_collection, trip_expenses_collection
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users_collection = db["users"]
daily_expenses_collection = db["daily_expenses"]
trips_collection = db["trips"]
trip_expenses_collection = db["trip_expenses"]

app = Flask(__name__)
app.secret_key = "hisabkitab_secret_key"

# ─── HOME ─────────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")

# ─── DB TEST ──────────────────────────────────────────────────────────────────
@app.route("/test-db")
def test_db():
    users_count = users_collection.count_documents({})
    return f"MongoDB connected successfully! Total users: {users_count}"

# ─── AUTH ─────────────────────────────────────────────────────────────────────
@app.route("/signup", methods=["GET", "POST"])
def signup():
    message = ""
    if request.method == "POST":
        name     = request.form["name"].strip()
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        if users_collection.find_one({"username": username}):
            message = "Username already exists. Please choose another."
        else:
            users_collection.insert_one({
                "name":     name,
                "username": username,
                "password": password
            })
            return redirect(url_for("login"))
    return render_template("signup.html", message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        user = users_collection.find_one({"username": username, "password": password})
        if user:
            session["username"] = user["username"]
            session["name"]     = user["name"]
            return redirect(url_for("dashboard"))
        else:
            message = "Invalid username or password. Please try again."
    return render_template("login.html", message=message)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ─── DASHBOARD ────────────────────────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template(
        "dashboard.html",
        name=session["name"],
        username=session["username"]
    )

# ─── DAILY EXPENSES ───────────────────────────────────────────────────────────
@app.route("/add-expense", methods=["GET", "POST"])
def add_expense():
    if "username" not in session:
        return redirect(url_for("login"))
    message = ""
    if request.method == "POST":
        title    = request.form["title"].strip()
        amount   = request.form["amount"].strip()
        category = request.form["category"].strip()
        date     = request.form["date"].strip()

        if title and amount and category and date:
            daily_expenses_collection.insert_one({
                "username": session["username"],
                "title":    title,
                "amount":   float(amount),
                "category": category,
                "date":     date
            })
            message = "Expense added successfully!"
    expenses     = list(daily_expenses_collection.find({"username": session["username"]}))
    total_amount = sum(e["amount"] for e in expenses)
    return render_template(
        "add_expense.html",
        message=message,
        expenses=expenses,
        total_amount=total_amount,
        name=session["name"],
        username=session["username"]
    )

@app.route("/delete-expense/<expense_id>")
def delete_expense(expense_id):
    if "username" not in session:
        return redirect(url_for("login"))
    expense = daily_expenses_collection.find_one({"_id": ObjectId(expense_id)})
    if expense and expense["username"] == session["username"]:
        daily_expenses_collection.delete_one({"_id": ObjectId(expense_id)})
    return redirect(url_for("add_expense"))

# ─── TRIPS ────────────────────────────────────────────────────────────────────
@app.route("/create-trip", methods=["GET", "POST"])
def create_trip():
    if "username" not in session:
        return redirect(url_for("login"))
    message = ""
    error   = ""
    if request.method == "POST":
        trip_name    = request.form.get("trip_name", "").strip()
        member_count = request.form.get("member_count", "").strip()
        if not trip_name or not member_count:
            error = "Please fill all required fields."
            return render_template("create_trip.html", name=session["name"], message=message, error=error)
        try:
            member_count = int(member_count)
        except ValueError:
            error = "Number of people must be a valid number."
            return render_template("create_trip.html", name=session["name"], message=message, error=error)
        members = [session["username"]]
        for i in range(2, member_count + 1):
            uname = request.form.get(f"member_{i}", "").strip()
            if uname and uname != session["username"]:
                members.append(uname)
        invalid_users = [u for u in members if not users_collection.find_one({"username": u})]
        if invalid_users:
            error = "These usernames do not exist: " + ", ".join(invalid_users)
        elif trips_collection.find_one({"trip_name": trip_name, "created_by": session["username"]}):
            error = "A trip with this name already exists. Choose a different name."
        else:
            trips_collection.insert_one({
                "trip_name":    trip_name,
                "created_by":   session["username"],
                "members":      members,
                "member_count": len(members)
            })
            message = f"Trip '{trip_name}' created successfully!"
    return render_template("create_trip.html", name=session["name"], message=message, error=error)

@app.route("/trip-details")
def trip_details():
    if "username" not in session:
        return redirect(url_for("login"))
    user_trips = list(trips_collection.find({"members": session["username"]}))
    return render_template(
        "trip_details.html",
        name=session["name"],
        username=session["username"],
        trips=user_trips
    )

@app.route("/delete-trip/<trip_id>")
def delete_trip(trip_id):
    if "username" not in session:
        return redirect(url_for("login"))
    trip = trips_collection.find_one({"_id": ObjectId(trip_id)})
    if not trip:
        return redirect(url_for("trip_details"))
    if trip["created_by"] != session["username"]:
        return "Only the trip creator can delete this trip."
    trips_collection.delete_one({"_id": ObjectId(trip_id)})
    trip_expenses_collection.delete_many({"trip_id": str(trip_id)})
    return redirect(url_for("trip_details"))


# ─── TRIP EXPENSES ────────────────────────────────────────────────────────────
@app.route("/add-trip-expense/<trip_id>", methods=["GET", "POST"])
def add_trip_expense(trip_id):
    if "username" not in session:
        return redirect(url_for("login"))
    trip = trips_collection.find_one({"_id": ObjectId(trip_id)})
    if not trip:
        return "Trip not found!", 404
    if session["username"] not in trip["members"]:
        return "You are not a member of this trip.", 403
    message = ""
    error   = ""
    if request.method == "POST":
        title   = request.form.get("title", "").strip()
        amount  = request.form.get("amount", "").strip()
        paid_by = request.form.get("paid_by", "").strip()
        date    = request.form.get("date", "").strip()
        if not all([title, amount, paid_by, date]):
            error = "Please fill all fields."
        else:
            try:
                amount = float(amount)
            except ValueError:
                error = "Amount must be a valid number."
            else:
                trip_expenses_collection.insert_one({
                    "trip_id":      str(trip["_id"]),
                    "trip_name":    trip["trip_name"],
                    "title":        title,
                    "amount":       amount,
                    "paid_by":      paid_by,
                    "split_among":  trip["members"],
                    "date":         date,
                    "added_by":     session["username"]
                })
                message = "Trip expense added successfully!"
    expenses = list(trip_expenses_collection.find({"trip_id": str(trip["_id"])}))
    return render_template(
        "add_trip_expense.html",
        name=session["name"],
        trip=trip,
        expenses=expenses,
        message=message,
        error=error
    )

@app.route("/delete-trip-expense/<expense_id>/<trip_id>")
def delete_trip_expense(expense_id, trip_id):
    if "username" not in session:
        return redirect(url_for("login"))
    expense = trip_expenses_collection.find_one({"_id": ObjectId(expense_id)})
    if expense:
        trip = trips_collection.find_one({"_id": ObjectId(trip_id)})
        if trip and session["username"] in trip["members"]:
            trip_expenses_collection.delete_one({"_id": ObjectId(expense_id)})
    return redirect(url_for("add_trip_expense", trip_id=trip_id))

@app.route("/view-trip-expenses/<trip_id>")
def view_trip_expenses(trip_id):
    if "username" not in session:
        return redirect(url_for("login"))
    trip = trips_collection.find_one({"_id": ObjectId(trip_id)})
    if not trip:
        return "Trip not found!", 404
    if session["username"] not in trip["members"]:
        return "You are not a member of this trip.", 403
    expenses      = list(trip_expenses_collection.find({"trip_id": str(trip["_id"])}))
    total_expense = sum(e["amount"] for e in expenses)
    member_totals = {m: 0 for m in trip["members"]}
    member_share  = {m: 0 for m in trip["members"]}
    balances      = {m: 0 for m in trip["members"]}
    for expense in expenses:
        paid_by      = expense["paid_by"]
        amount       = expense["amount"]
        split_members = expense["split_among"]
        if paid_by in member_totals:
            member_totals[paid_by] += amount
        if split_members:
            per_person = amount / len(split_members)
            for m in split_members:
                if m in member_share:
                    member_share[m] += per_person
    for m in trip["members"]:
        balances[m] = round(member_totals[m] - member_share[m], 2)
    creditors = [[m, b]      for m, b in balances.items() if b > 0]
    debtors   = [[m, abs(b)] for m, b in balances.items() if b < 0]
    settlements = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        settle = round(min(debtors[i][1], creditors[j][1]), 2)
        settlements.append({"from": debtors[i][0], "to": creditors[j][0], "amount": settle})
        debtors[i][1]   = round(debtors[i][1]   - settle, 2)
        creditors[j][1] = round(creditors[j][1] - settle, 2)
        if debtors[i][1]   == 0: i += 1
        if creditors[j][1] == 0: j += 1
    return render_template(
        "view_trip_expenses.html",
        name=session["name"],
        trip=trip,
        expenses=expenses,
        total_expense=total_expense,
        member_totals=member_totals,
        member_share=member_share,
        balances=balances,
        settlements=settlements
    )

# ─── RUN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
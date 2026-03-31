from flask import Flask, request, jsonify
from flask_cors import CORS
from bson.objectid import ObjectId
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

app = Flask(__name__)
CORS(app)

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users_collection = db["users"]
daily_expenses_collection = db["daily_expenses"]
trips_collection = db["trips"]
trip_expenses_collection = db["trip_expenses"]


@app.route("/")
def home():
    return jsonify({"message": "HisabKitab Backend is running"})


@app.route("/api/test-db")
def test_db():
    users_count = users_collection.count_documents({})
    return jsonify({
        "success": True,
        "message": "MongoDB connected successfully",
        "total_users": users_count
    })


# ---------------- AUTH ----------------

@app.route("/api/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()

        name = data.get("name", "").strip()
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not name or not username or not password:
            return jsonify({
                "success": False,
                "message": "Please fill all fields."
            }), 400

        existing_user = users_collection.find_one({"username": username})
        if existing_user:
            return jsonify({
                "success": False,
                "message": "Username already exists. Please choose another."
            }), 400

        users_collection.insert_one({
            "name": name,
            "username": username,
            "password": password
        })

        return jsonify({
            "success": True,
            "message": "Signup successful."
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Please fill all fields."
            }), 400

        user = users_collection.find_one({
            "username": username,
            "password": password
        })

        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid username or password."
            }), 401

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "name": user["name"],
            "username": user["username"]
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ---------------- DAILY EXPENSES ----------------

@app.route("/api/add-expense", methods=["POST"])
def add_expense():
    try:
        data = request.get_json()

        username = data.get("username", "").strip()
        title = data.get("title", "").strip()
        amount = data.get("amount")
        category = data.get("category", "").strip()
        date = data.get("date", "").strip()

        if not username or not title or amount in [None, ""] or not category or not date:
            return jsonify({
                "success": False,
                "message": "Please fill all fields."
            }), 400

        daily_expenses_collection.insert_one({
            "username": username,
            "title": title,
            "amount": float(amount),
            "category": category,
            "date": date
        })

        return jsonify({
            "success": True,
            "message": "Expense added successfully."
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/expenses/<username>", methods=["GET"])
def get_expenses(username):
    try:
        expenses = list(daily_expenses_collection.find({"username": username}))
        expense_list = []

        total_amount = 0
        for expense in expenses:
            expense_list.append({
                "_id": str(expense["_id"]),
                "title": expense["title"],
                "amount": expense["amount"],
                "category": expense["category"],
                "date": expense["date"]
            })
            total_amount += expense["amount"]

        return jsonify({
            "success": True,
            "expenses": expense_list,
            "total_amount": round(total_amount, 2)
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/delete-expense/<expense_id>/<username>", methods=["DELETE"])
def delete_expense(expense_id, username):
    try:
        expense = daily_expenses_collection.find_one({"_id": ObjectId(expense_id)})

        if not expense:
            return jsonify({
                "success": False,
                "message": "Expense not found."
            }), 404

        if expense["username"] != username:
            return jsonify({
                "success": False,
                "message": "You are not allowed to delete this expense."
            }), 403

        daily_expenses_collection.delete_one({"_id": ObjectId(expense_id)})

        return jsonify({
            "success": True,
            "message": "Expense deleted successfully."
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ---------------- TRIPS ----------------

@app.route("/api/create-trip", methods=["POST"])
def create_trip():
    try:
        data = request.get_json()

        current_username = data.get("current_username", "").strip()
        trip_name = data.get("trip_name", "").strip()
        members = data.get("members", [])

        if not current_username or not trip_name or not members:
            return jsonify({
                "success": False,
                "message": "Please fill all required fields."
            }), 400

        if current_username not in members:
            members.insert(0, current_username)

        cleaned_members = []
        for member in members:
            member = member.strip()
            if member and member not in cleaned_members:
                cleaned_members.append(member)

        invalid_users = []
        for member in cleaned_members:
            user = users_collection.find_one({"username": member})
            if not user:
                invalid_users.append(member)

        if invalid_users:
            return jsonify({
                "success": False,
                "message": "These usernames do not exist: " + ", ".join(invalid_users)
            }), 400

        existing_trip = trips_collection.find_one({
            "trip_name": trip_name,
            "created_by": current_username
        })

        if existing_trip:
            return jsonify({
                "success": False,
                "message": "A trip with this name already exists."
            }), 400

        trips_collection.insert_one({
            "trip_name": trip_name,
            "created_by": current_username,
            "members": cleaned_members,
            "member_count": len(cleaned_members)
        })

        return jsonify({
            "success": True,
            "message": "Trip created successfully."
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/trips/<username>", methods=["GET"])
def get_trips(username):
    try:
        trips = list(trips_collection.find({"members": username}))
        trip_list = []

        for trip in trips:
            trip_list.append({
                "_id": str(trip["_id"]),
                "trip_name": trip["trip_name"],
                "created_by": trip["created_by"],
                "members": trip["members"],
                "member_count": trip["member_count"]
            })

        return jsonify({
            "success": True,
            "trips": trip_list
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/delete-trip/<trip_id>/<username>", methods=["DELETE"])
def delete_trip(trip_id, username):
    try:
        trip = trips_collection.find_one({"_id": ObjectId(trip_id)})

        if not trip:
            return jsonify({
                "success": False,
                "message": "Trip not found."
            }), 404

        if trip["created_by"] != username:
            return jsonify({
                "success": False,
                "message": "Only the trip creator can delete this trip."
            }), 403

        trips_collection.delete_one({"_id": ObjectId(trip_id)})
        trip_expenses_collection.delete_many({"trip_id": trip_id})

        return jsonify({
            "success": True,
            "message": "Trip deleted successfully."
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ---------------- TRIP EXPENSES ----------------

@app.route("/api/add-trip-expense/<trip_id>", methods=["POST"])
def add_trip_expense(trip_id):
    try:
        data = request.get_json()

        current_username = data.get("current_username", "").strip()
        title = data.get("title", "").strip()
        amount = data.get("amount")
        paid_by = data.get("paid_by", "").strip()
        date = data.get("date", "").strip()

        trip = trips_collection.find_one({"_id": ObjectId(trip_id)})

        if not trip:
            return jsonify({
                "success": False,
                "message": "Trip not found."
            }), 404

        if current_username not in trip["members"]:
            return jsonify({
                "success": False,
                "message": "You are not a member of this trip."
            }), 403

        if not title or amount in [None, ""] or not paid_by or not date:
            return jsonify({
                "success": False,
                "message": "Please fill all fields."
            }), 400

        trip_expenses_collection.insert_one({
            "trip_id": str(trip["_id"]),
            "trip_name": trip["trip_name"],
            "title": title,
            "amount": float(amount),
            "paid_by": paid_by,
            "split_among": trip["members"],
            "date": date,
            "added_by": current_username
        })

        return jsonify({
            "success": True,
            "message": "Trip expense added successfully."
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/trip-expenses/<trip_id>/<username>", methods=["GET"])
def get_trip_expenses(trip_id, username):
    try:
        trip = trips_collection.find_one({"_id": ObjectId(trip_id)})

        if not trip:
            return jsonify({
                "success": False,
                "message": "Trip not found."
            }), 404

        if username not in trip["members"]:
            return jsonify({
                "success": False,
                "message": "You are not a member of this trip."
            }), 403

        expenses = list(trip_expenses_collection.find({"trip_id": trip_id}))
        expense_list = []

        for expense in expenses:
            expense_list.append({
                "_id": str(expense["_id"]),
                "title": expense["title"],
                "amount": expense["amount"],
                "paid_by": expense["paid_by"],
                "date": expense["date"],
                "added_by": expense["added_by"]
            })

        return jsonify({
            "success": True,
            "trip": {
                "_id": str(trip["_id"]),
                "trip_name": trip["trip_name"],
                "members": trip["members"],
                "member_count": trip["member_count"],
                "created_by": trip["created_by"]
            },
            "expenses": expense_list
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/delete-trip-expense/<expense_id>/<trip_id>/<username>", methods=["DELETE"])
def delete_trip_expense(expense_id, trip_id, username):
    try:
        trip = trips_collection.find_one({"_id": ObjectId(trip_id)})

        if not trip:
            return jsonify({
                "success": False,
                "message": "Trip not found."
            }), 404

        if username not in trip["members"]:
            return jsonify({
                "success": False,
                "message": "You are not allowed to delete this expense."
            }), 403

        expense = trip_expenses_collection.find_one({"_id": ObjectId(expense_id)})

        if not expense:
            return jsonify({
                "success": False,
                "message": "Expense not found."
            }), 404

        trip_expenses_collection.delete_one({"_id": ObjectId(expense_id)})

        return jsonify({
            "success": True,
            "message": "Trip expense deleted successfully."
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/trip-summary/<trip_id>/<username>", methods=["GET"])
def trip_summary(trip_id, username):
    try:
        trip = trips_collection.find_one({"_id": ObjectId(trip_id)})

        if not trip:
            return jsonify({
                "success": False,
                "message": "Trip not found."
            }), 404

        if username not in trip["members"]:
            return jsonify({
                "success": False,
                "message": "You are not a member of this trip."
            }), 403

        expenses = list(trip_expenses_collection.find({"trip_id": trip_id}))
        expense_list = []

        total_expense = 0
        member_totals = {m: 0 for m in trip["members"]}
        member_share = {m: 0 for m in trip["members"]}
        balances = {m: 0 for m in trip["members"]}

        for expense in expenses:
            expense_list.append({
                "_id": str(expense["_id"]),
                "title": expense["title"],
                "amount": expense["amount"],
                "paid_by": expense["paid_by"],
                "date": expense["date"]
            })

            total_expense += expense["amount"]

            paid_by = expense["paid_by"]
            split_members = expense["split_among"]

            if paid_by in member_totals:
                member_totals[paid_by] += expense["amount"]

            if split_members:
                per_person = expense["amount"] / len(split_members)
                for member in split_members:
                    if member in member_share:
                        member_share[member] += per_person

        for member in trip["members"]:
            balances[member] = round(member_totals[member] - member_share[member], 2)

        creditors = [[m, b] for m, b in balances.items() if b > 0]
        debtors = [[m, abs(b)] for m, b in balances.items() if b < 0]

        settlements = []
        i = 0
        j = 0

        while i < len(debtors) and j < len(creditors):
            settle = round(min(debtors[i][1], creditors[j][1]), 2)

            settlements.append({
                "from": debtors[i][0],
                "to": creditors[j][0],
                "amount": settle
            })

            debtors[i][1] = round(debtors[i][1] - settle, 2)
            creditors[j][1] = round(creditors[j][1] - settle, 2)

            if debtors[i][1] == 0:
                i += 1
            if creditors[j][1] == 0:
                j += 1

        return jsonify({
            "success": True,
            "trip": {
                "_id": str(trip["_id"]),
                "trip_name": trip["trip_name"],
                "members": trip["members"],
                "member_count": trip["member_count"]
            },
            "expenses": expense_list,
            "total_expense": round(total_expense, 2),
            "member_totals": member_totals,
            "member_share": {k: round(v, 2) for k, v in member_share.items()},
            "balances": balances,
            "settlements": settlements
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
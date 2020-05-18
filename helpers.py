import csv
import urllib.request
from datetime import datetime

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Renders message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def get_item(db, id):
    # query database for specific schedule item
    item = db.execute("SELECT A.*,B.label,B.factor,C.frequency,C.modifier,C.n,ifnull(A.snoozed_dt,A.current_dt) dt \
                      FROM schedule A \
                      INNER JOIN type B ON A.type_id = B.id \
                      INNER JOIN frequency C ON A.frequency_id = C.id \
                      WHERE A.id = :id;", id=id)

    # since querying specific item return index 0
    return item[0]


def get_scheduled(db, user_id):
    # query database for scheduled items prior to next pay check (type_id)
    scheduled = db.execute("SELECT A.*,B.label,B.factor,C.frequency,C.modifier,C.n,ifnull(A.snoozed_dt,A.current_dt) dt \
                           FROM schedule A \
                           INNER JOIN type B ON A.type_id = B.id \
                           INNER JOIN frequency C ON A.frequency_id = C.id \
                           INNER JOIN ( \
                           SELECT user_id \
                           ,MIN(current_dt) AS current_dt \
                           ,MIN(date(current_dt, (repeat * F.n) || ' ' || F.modifier)) As next_dt \
                           FROM schedule S \
                           INNER JOIN frequency F ON S.frequency_id = F.id \
                           WHERE type_id = 1 \
                           AND completed_dt is NULL \
                           GROUP BY user_id) D ON A.user_id = D.user_id \
                           WHERE A.user_id = :user_id AND \
                           completed_dt is NULL AND \
                           dt < D.current_dt \
                           ORDER BY dt;", user_id=user_id)

    return scheduled


def get_next(db, user_id):
    # query database for scheduled items prior to next pay check (type_id)
    next = db.execute("SELECT A.*,B.label,B.factor,C.frequency,C.modifier,C.n,ifnull(A.snoozed_dt,A.current_dt) dt \
                           FROM schedule A \
                           INNER JOIN type B ON A.type_id = B.id \
                           INNER JOIN frequency C ON A.frequency_id = C.id \
                           INNER JOIN ( \
                           SELECT user_id \
                           ,MIN(current_dt) AS current_dt \
                           ,MIN(date(current_dt, (repeat * F.n) || ' ' || F.modifier)) As next_dt \
                           FROM schedule S \
                           INNER JOIN frequency F ON S.frequency_id = F.id \
                           WHERE type_id = 1 \
                           AND completed_dt is NULL \
                           GROUP BY user_id) D ON A.user_id = D.user_id \
                           WHERE A.user_id = :user_id AND \
                           completed_dt is NULL AND \
                           dt >= D.current_dt AND \
                           dt < D.next_dt\
                           ORDER BY dt;", user_id=user_id)

    return next


def get_future(db, user_id):
    # query database for all items on or after next pay check (type_id)
    future = db.execute("SELECT A.*,B.label,B.factor,C.frequency,C.modifier,C.n,ifnull(A.snoozed_dt,A.current_dt) dt \
                        FROM schedule A \
                        INNER JOIN type B ON A.type_id = B.id \
                        INNER JOIN frequency C ON A.frequency_id = C.id \
                        INNER JOIN ( \
                        SELECT user_id \
                        ,MIN(current_dt) AS current_dt \
                        ,MIN(date(current_dt, (repeat * F.n) || ' ' || F.modifier)) As next_dt \
                        FROM schedule S \
                        INNER JOIN frequency F ON S.frequency_id = F.id \
                        WHERE type_id = 1 \
                        AND completed_dt is NULL \
                        GROUP BY user_id) D ON A.user_id = D.user_id \
                        WHERE A.user_id = :user_id AND \
                        completed_dt is NULL AND \
                        dt >= D.next_dt \
                        ORDER BY dt;", user_id=user_id)

    return future


# Format schedule is run separate from get_scheduled for usage in page display
def format_schedule(schedule):
    for item in schedule:
        # format usd
        item["amount"] = usd(item["amount"] * item["factor"])

        # format date
        item["dt"] = format_date(item["dt"])

        # standard 1 repeat or One Time display actual frequency
        if item["repeat"] == 1 or item["frequency"] == "One Time":
            item["frequency_display"] = item["frequency"]

        # modifier for weekly date updates is days but display will show weeks
        elif item["frequency"] == "Weekly":
            item["frequency_display"] = "Every " + str(item["repeat"]) + " Weeks"

        # else "Every n modifier"
        else:
            item["frequency_display"] = "Every " + str(item["n"] * item["repeat"]) + " " + item["modifier"]


def get_balances(db, user_id):
    # query database for balances
    balance = db.execute("SELECT * \
                         FROM balance \
                         WHERE user_id = :user_id;", user_id=user_id)

     # create dictionary for balances
    balances = {}

    # current balance
    balances["current"] = balance[0]["current"]

    # get available balance
    balances["available"] = balance[0]["available"]

    # pending transactions if any
    balances["pending"] = balances["current"] - balances["available"]

    # query database for scheduled
    scheduled = get_scheduled(db, user_id)

    # query database for next scheduled
    next_scheduled = get_next(db, user_id)

    # scheduled available balance
    # amount is converted by factor payments/bills are negative and deposits are positive
    balances["net"] = balances["available"] + sum(item['amount'] * item['factor'] for item in scheduled)

    # next scheduled available balance
    balances["next_net"] = balances["net"] + sum(item['amount'] * item['factor'] for item in next_scheduled)

    print(balances)
    return balances


def format_balances(balances):
    # convert all balances to usd for display on page
    for k, v in balances.items():
        balances[k] = usd(balances[k])


def format_modifier(item):

    try:
        # set n for date modifier
        n = item["repeat"] * item["n"]

        # create modifier string for date function
        modifier = str(n) + " " + item["modifier"]

        return modifier

    except:
        raise RuntimeError("unable to format date modifier")


def get_types(db):
    # query database for types
    types = db.execute("SELECT * \
                       FROM type \
                       ORDER BY id;")

    return types


def get_frequencies(db):
    # query database for frequencies
    frequencies = db.execute("SELECT * \
                             FROM frequency \
                             ORDER BY id;")

    return frequencies


def insert_schedule(db, user_id, data):
    # insert into schedule
    db.execute("INSERT INTO schedule (name, type_id, current_dt, frequency_id, repeat, amount, user_id)\
               VALUES(:name, :type_id, :current_dt, :frequency_id, :repeat, :amount, :user_id);",\
               name=data["name"], type_id=data["type_id"], current_dt=data["current_dt"],
               frequency_id=data["frequency_id"], repeat=data["repeat"], amount=data["amount"], user_id=user_id)


def complete_item(db, id):
    # update completed_dt and reset snoozed_dt
    db.execute("UPDATE schedule \
               SET completed_dt = date('now') \
               ,snoozed_dt = NULL \
               WHERE id = :id;", id=id)


def snooze_item(db, data):
    # update snoozed_dt
    db.execute("UPDATE schedule \
               SET snoozed_dt = :snoozed \
               WHERE id = :id;",snoozed=data["snoozed"], id=data["id"])


def update_schedule(db, user_id, data):
    # logic for post action
    if data["action"] == "Post":
        # get schedule item
        item = get_item(db, data["id"])

        # set completed_dt for One Time
        if item['frequency'] == "One Time":
                complete_item(db, data["id"])

        # all others move current_dt forward
        else:
            # format date modifier string
            modifier = format_modifier(item)

            # set new current_dt
            db.execute("UPDATE schedule \
                       SET current_dt = date(current_dt, :modifier) \
                       ,snoozed_dt = NULL \
                       ,previous_dt = current_dt \
                       WHERE id = :id;", id=data["id"], modifier=modifier)

    # complete action
    elif data["action"] == "Complete":
        complete_item(db, data["id"])

    # edit action
    elif data["action"] == "Edit":
            # update all fields from form
            db.execute("UPDATE schedule \
                       SET name = :name \
                       ,type_id = :type_id \
                       ,current_dt = :current_dt \
                       ,snoozed_dt = NULL \
                       ,frequency_id = :frequency_id \
                       ,repeat = :repeat \
                       ,amount = :amount \
                       WHERE id = :id;", id=data["id"], name=data["name"], type_id=data["type_id"],
                       current_dt=data["current_dt"], frequency_id=data["frequency_id"],
                       repeat=data["repeat"], amount=data["amount"])


def usd(value):
    """Formats value as USD."""
    if value < 0:
        return f"-${value*-1:,.2f}"
    else:
        return f"${value:,.2f}"


def format_date(date):
    """Formats date as m/d/yyyy."""
    d = datetime.strptime(date, '%Y-%m-%d')
    return d.strftime("%m/%d/%Y")


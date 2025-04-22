from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import os

app = Flask(__name__)

FINANCE_FILE = "data/finance.json"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/load", methods=["GET"])
def load_data_from_file():
    if os.path.exists(FINANCE_FILE):
        with open(FINANCE_FILE, 'r') as file:
            data = json.load(file)
        return jsonify(success=True, data=data)
    return jsonify(success=False, message="No saved data found")

@app.route("/save", methods=["POST"])
def save_data_to_file():
    data = request.get_json()

    #   Spara i JSON-fil
    with open(FINANCE_FILE, "w") as file:
        json.dump(data, file, indent=2)
        
    
    #   input data
    birth_year = data["birth"]["year"]
    birth_month = data["birth"]["month"]
    
    salary = data["income"]["salary"]
    
    emergency_now = data["assets"]["emergencyNow"]
    emergency_goal = data["assets"]["emergencyGoal"]
    stock_savings = data["assets"]["stockSavings"]
    stocks_gain = data["assets"]["stocksGain"]
    
    mortgage = data["loans"]["mortgage"]
    mortgage_rate = data["loans"]["mortgageRate"]
    csn_debt = data["loans"]["csnTotal"]
    
    csn_monthly_payoff = data["fixedCosts"]["csnPayoff"]
    must_haves = data["fixedCosts"]["mustHaves"]
    
    food_costs = data["spending"]["foodCosts"]
    travel_costs = data["spending"]["travelCosts"]
    
    mortgage_monthly_payoff = data["payChoices"]["amortization"]
    split_strategy = data["payChoices"].get("splitStrategy") == "true"
    if not split_strategy:
        split_strategy = "true"
    
    
    montly_stocks_gain_factor = pow(1 + stocks_gain/100, 1/12)
    
    #   loop preparations
    emergency_filled_date = None
    csn_free_date = None
    mortgage_free_date = None
    fire_date = None
    fire_amount = None

    current_date = datetime.today().replace(day=1)
    month_counter = 0
    
    while not (emergency_filled_date and mortgage_free_date and csn_free_date and fire_date) and month_counter < 600:
        
        #   Räkna disponibelt belopp samt fire-belopp
        monthly_cost = must_haves + food_costs + travel_costs
        mortgage_cost = (mortgage_rate/100) * mortgage / 12
        monthly_cost += mortgage_cost
            
        available = salary - monthly_cost
        fire_amount = 25 * monthly_cost * 12
        print(month_counter, fire_amount)
        
        #   Räkna ut portfolio värde och evaluera fire
        stock_savings *= montly_stocks_gain_factor
        if not fire_date and stock_savings >= fire_amount:
            fire_date = current_date

        
        #   Betala CSN, fast kostnad
        if not csn_free_date:
            csn_payoff = min(csn_monthly_payoff, csn_debt)
            csn_debt -= csn_payoff
            if csn_debt <= 0:
                csn_free_date = current_date
        
        #   Betala till nödkontot först
        if emergency_now < emergency_goal:
            emergency_payoff = min(available, emergency_goal - emergency_now)
            emergency_now += emergency_payoff
            available -= emergency_payoff
            if not emergency_filled_date and emergency_now >= emergency_goal:
                emergency_filled_date = current_date
        
        if (available > 0):
            
            #   Betala av bolån
            if not mortgage_free_date:
                if not split_strategy:
                    this_mortgage_payoff = min(available, mortgage_monthly_payoff)
                else:
                    this_mortgage_payoff = available / 2
            
                mortgage -= this_mortgage_payoff
                available -= this_mortgage_payoff
                if (mortgage <= 0):
                    mortgage_free_date = current_date
            
            #   Investera resten i börsen
            stock_savings += max(0, available)
        
        #   Nästa månad
        current_date += relativedelta(months=1)
        month_counter += 1
    
    result = {
        "emergencyFilled":{
            "date":emergency_filled_date.strftime("%Y-%m"),
            "age":calcAge(birth_year, birth_month, emergency_filled_date)
        },
        "csnFree":{
            "date":csn_free_date.strftime("%Y-%m"),
            "age":calcAge(birth_year, birth_month, csn_free_date)
        },
        "mortgageFree":{
            "date":mortgage_free_date.strftime("%Y-%m"),
            "age":calcAge(birth_year, birth_month, mortgage_free_date)
        },
        "fire":{
            "date":fire_date.strftime("%Y-%m"),
            "age":calcAge(birth_year, birth_month, fire_date),
            "fireAmount":fire_amount,
            "monthlyCosts":fire_amount/(25*12)
        }
    }

    return jsonify(result)

def calcAge(birth_year, birth_month, current_date):
    age = current_date.year - birth_year
    if current_date.month < birth_month:
        age -= 1
    return age

if __name__ == "__main__":
    app.run(debug=True)
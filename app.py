from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import os

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/save", methods=["POST"])
def save_data():
    data = request.get_json()

    #   Spara i JSON-fil
    with open("data/finance.json", "w") as f:
        json.dump(data, f, indent=2)
        
    
    #   input data
    birth_year = data["birth_year"]
    birth_month = data["birth_month"]
    pay = data["pay"]
    mortgage = data["mortgage"]
    mortgage_rate = data["interest"]
    mortgage_monthly_payoff = data["mortgage_payoff"]
    csn_debt = data["csn"]
    csn_monthly_payoff = data["csn_payoff"]
    emergency_goal = data["emergency_goal"]
    emergency_now = data["emergency_now"]
    stock_savings = data["stock_savings"]
    stocks_gain = data["stocks_gain"]
    fixed_costs = data["fixed_costs"]
    rent = data["rent"]
    food_costs = data["food_costs"]
    split_strategy = data.get("split_strategy") == "true"
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
        monthly_cost = fixed_costs + food_costs + rent
        if not mortgage_free_date:
            mortgage_cost = (mortgage_rate/100) * mortgage / 12
            monthly_cost += mortgage_cost
            
        available = pay - monthly_cost
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
            "amount":fire_amount
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
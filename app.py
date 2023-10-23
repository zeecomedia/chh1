from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    url_for,
    jsonify,
    flash,
)

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import os
import datetime as dt
import warnings
import pymongo

from flask_login import LoginManager


from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
import stripe
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators
from flask_bcrypt import Bcrypt
from authlib.integrations.flask_client import OAuth
from flask_login import login_user, current_user, login_required
from dateutil.relativedelta import relativedelta

warnings.filterwarnings("ignore")

# Import the Hedge v5 trading strategy script
from modules.ma_crossover_strategy.charts import generate_charts
from modules.ma_crossover_strategy.sma_ema import add_sma_ema_signals
from modules.ma_crossover_strategy.data_download import download_ticker_data
from modules.ma_crossover_strategy.kpi_calcs import calculate_kpis
from datetime import datetime
# import rebalancing functions
from modules.rebalancing_strategy.get_rebalancing_data import get_rebalancing_data


# default values
default_symbol = "QQQ"
default_short = 5
default_long = 200
default_ind = "SMA"
default_start_date = "2000-01-01"
default_end_date = "2023-12-30"
default_transaction_costs = 5




USER_TYPE = ["FREE","PREMIUM"]

#mongodb
from pymongo.mongo_client import MongoClient
# Retrieve the MongoDB URI
uri = os.getenv('MONGO_URI')
print("Connecting to MongoDB")

# Create a new client and connect to the server
client = MongoClient(uri)
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print("No connection to MongoDB:", e)

#print("URI:", os.getenv('MONGO_URI'))



app = Flask(__name__, template_folder="templates", static_folder="static")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

app.config["SECRET_KEY"] = os.getenv('SECRET_KEY')
app.config["GOOGLE_CLIENT_ID"] = os.getenv('GOOGLE_CLIENT_ID')
app.config["GOOGLE_SECRET_KEY"] = os.getenv('GOOGLE_SECRET_KEY')

#stripe details
app.config["STRIPE_PUBLISHABLE_KEY"] = "pk_test_hqGtAv97ws7TdC8O367fft3W"
app.config["STRIPE_SECRET_KEY"] = "sk_test_m5sw5JWx3z9Ob54AAnRQv1Vn"
app.config["STRIPE_PRICE_ID"] ="price_1O4KXNILsyIIwJfD0vieEEjV"
app.config["STRIPE_ENDPOINT_SECRET"] = "whsec_36e1cc4f123b13a630b01c0bdce14516085f8e0174efdfc3a6e7f8b87a5750a5"


stripe.api_key = "sk_test_m5sw5JWx3z9Ob54AAnRQv1Vn"

oauth = OAuth()
oauth.init_app(app)

if os.environ.get("FLASK_ENV") == "development":
    base_url = "http://localhost:5000"
else:
    base_url = "https://subsapp-9504fa1fc11f.herokuapp.com/"

redirect_uri = f"{base_url}/login/authorized"


# Register Google as an OAuth provider
google = oauth.register(
    'google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_SECRET_KEY'),
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri=redirect_uri,
    client_kwargs={'scope': 'email profile'},
)


@app.route("/")
def index():
    session['user_type_data'] = USER_TYPE 
    # print(check_user_type)
    if session['user_type_data'] == 'FREE':
        # Get the start and end dates from the session
        start_date = session.get("start_date", default_start_date)
        end_date = session.get("end_date", default_end_date)

        if isinstance(start_date, str):
           start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # duration_in_years = end_date.year - start_date.year
        # Calculate the date difference in years

        date_diff = relativedelta(end_date, start_date).years
    
        # If the date difference is more than 2 years, limit it to 2 years
        if date_diff > 2:
            end_date = start_date + relativedelta(years=2)
            flash('As free user, 2 year is the maximum year you can select', 'danger')
           
     
    return render_template(
            "index.html",
            symbol=session.get("symbol", default_symbol),
            short=session.get("short", default_short),
            long=session.get("long", default_long),
            ind=session.get("ind", default_ind),
            start_date=session.get("start_date", default_start_date),
            end_date=session.get("end_date", default_end_date),
            transaction_costs=session.get("transaction_costs", default_transaction_costs),
            img_str="",
            table_str=""
    )


#Login forms below

bcrypt = Bcrypt(app)

class LoginForm(FlaskForm):
    email = StringField('Email', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    email = StringField('Email', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])
    submit = SubmitField('Register')


@login_manager.user_loader
def load_user(user_id):
    r_user = client.chartchampUserDatabase.chartchampUsers.find_one(
            {"email": user_id.email.data})
    return r_user.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = client.chartchampUserDatabase.chartchampUsers.find_one(
            {"email": form.email.data})  # Assuming you're using a MongoDB collection named 'users'
        if user and bcrypt.check_password_hash(user['password'], form.password.data):
            session['user'] = form.email.data
            flash('Logged in successfully!', 'success')
            session['logged_in'] = True
            return redirect(url_for('index'))  # or wherever you want to redirect after login
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)

# ###  adding chargebee payment sub




@app.route("/profile")
def user_profile():
    user_email = session['user']
    user_type = "FREE"  # Default user type

    try:
        # Retrieve the customer's subscriptions
        customers = stripe.Customer.list(email=user_email).auto_paging_iter()
        for customer in customers:
            subscriptions = stripe.Subscription.list(customer=customer.id).auto_paging_iter()
            for subscription in subscriptions:
                # If the user has a subscription, set the user type to PREMIUM
                if subscription.id:
                    user_type = "PREMIUM"
                    session['user_type_data'] = user_type
                    break
    except stripe.error.InvalidRequestError as e:
        user_type = "FREE"
        session['user_type_data'] = user_type

    return render_template('profile.html', user_email=user_email, user_type=user_type)
    # return data



@app.route("/config")
def get_publishable_key():
    stripe_config = {"publicKey": "pk_test_hqGtAv97ws7TdC8O367fft3W"}
    return jsonify(stripe_config)


@app.route('/create-checkout-session/', methods=['GET'])
def create_checkout_session():
    domain_url = 'http://localhost:5000/'  # Flask runs on port 5000 by default
    try:
        checkout_session = stripe.checkout.Session.create(
            client_reference_id=request.args.get('user_id'),  # Get user_id from the query string
            success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + 'cancel/',
            payment_method_types=['card'],
            mode='subscription',
            line_items=[
                {
                    'price': "price_1O4KXNILsyIIwJfD0vieEEjV",
                    'quantity': 1,
                }
            ]
        )
        return jsonify({'sessionId': checkout_session['id']})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    return jsonify(data)


@app.route("/success")
def success():
    return redirect(url_for('index'))

# app.py
@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    endpoint_secret = "whsec_36e1cc4f123b13a630b01c0bdce14516085f8e0174efdfc3a6e7f8b87a5750a5"
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return jsonify(error=str(e)), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify(error=str(e)), 400

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Fetch all the required data from session
        client_reference_id = session.get('client_reference_id')
        stripe_customer_id = session.get('customer')
        stripe_subscription_id = session.get('subscription')


    return jsonify(message="Successfully created StripeCustomer..."), 200



@app.route('/cancel/', methods=['GET'])
def cancel():
    return jsonify(message="Transaction was unsuccessfully"), 200





@app.route('/cancel-subscription', methods=['POST'])
def cancel_subscription():
    email = session['user']
    user_type = "FREE"  # Default user type

    try:
        # Retrieve the customer's subscriptions
        customers = stripe.Customer.list(email=email).auto_paging_iter()
        for customer in customers:
            subscriptions = stripe.Subscription.list(customer=customer.id).auto_paging_iter()
            for subscription in subscriptions:
                # If the user has a subscription, cancel it
                if subscription.status == 'active':
                    stripe.Subscription.delete(subscription.id)
                    user_type = "FREE"
                    session['user_type_data'] = user_type
                    flash('You have unsubscribed successfully', 'success')
                    break
    except stripe.error.InvalidRequestError as e:
        user_type = "FREE"
        session['user_type_data'] = user_type

    return redirect(url_for('user_profile', user_type=session['user_type_data']))

    

# ################## end of code

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorized', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/authorized')
def authorized():
    token = google.authorize_access_token()
    if not token or 'access_token' not in token:
        return 'Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        )

    user_info_response = google.get('https://www.googleapis.com/oauth2/v1/userinfo')
    user_info_json = user_info_response.json()  # Parse the JSON response

    if not user_info_json or 'email' not in user_info_json:
        return 'Error fetching user information from Google.'

    session['google_token'] = (token['access_token'], '')

    user_email = user_info_json['email']
    user = client.chartchampUserDatabase.chartchampUsers.find_one({"email": user_email})

    if not user:  # if user doesn't exist, create a new one
        new_user = {
            "email": user_email,
            "name": user_info_json['name'],  # Store additional info if needed
            "profile_pic": user_info_json['picture']  # Store additional info if needed
        }
        client.chartchampUserDatabase.chartchampUsers.insert_one(new_user)
        flash('Account created with Google login!', 'success')
    else:
        flash('Welcome back!', 'success')

    session['user'] = user_email
    session['logged_in'] = True
    flash('Logged in with Google!', 'success')
    return redirect(url_for('index'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    print("Inside register function")

    form = RegisterForm()
    print("Form data:", form.data)

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = {
            "email": form.email.data,
            "password": hashed_password
        }
        print("Form validated")
        
        # Insert the user in the database
        try:
            client.chartchampUserDatabase.chartchampUsers.insert_one(user)
            # subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
            # session["customer_id"] = create_chargebee_user.customer.id
            flash('Your account has been created! You can now log in', 'success')
            print("Inserted data to MongoDB")
            return redirect(url_for('login'))
        except Exception as e:
            flash('Error registering user: ' + str(e), 'danger')
            return render_template('register.html', form=form)

    return render_template('register.html', form=form)


@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    # Redirect to the homepage
    return redirect(url_for('index'))

@app.route('/forgot_password')
def forgot_password():
    # Add logic to handle password reset here
    return render_template('forgot_password.html')





@app.route("/rebalancing_strategy")
def rebalancing_strategy():
    return render_template("rebalancing_strategy.html")





@app.route("/generate_chart", methods=["POST"])
def generate_chart():

    try:
        # Get user input
        symbol = request.form.get("symbol", default_symbol)
        short = int(request.form.get("short", default_short))
        long = int(request.form.get("long", default_long))
        ind = request.form.get("ind", default_ind)
        start_date = request.form.get("start_date", default_start_date)
        end_date = request.form.get("end_date", default_end_date)
        transaction_costs = float(
            request.form.get("transaction_costs", default_transaction_costs)
        )

        start_date_obj = dt.datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = dt.datetime.strptime(end_date, "%Y-%m-%d")
        difference = (start_date_obj - end_date_obj).days

        ticker_signal = symbol
        ticker_strat = symbol

        # Define the tickers to download data for
        tickers = [symbol]

        # Download historical data for tickers
        ohlc_data = download_ticker_data(tickers, start_date, end_date)

        # Add SMA/EMA signals and buy/sell signals
        ohlc_dict = add_sma_ema_signals(ohlc_data, symbol, short, long, ind)

        # Calculate returns with long strategy and ticker signal
        df_temp = pd.concat(ohlc_dict, axis=1)
        strat_returns = df_temp.xs("Adj Close", axis=1, level=1)
        strat_returns["Position"] = df_temp.xs("Position", axis=1, level=1)
        strat_returns = strat_returns.copy()
        strat_returns["Signal"] = df_temp.xs("Signal", axis=1, level=1)
        strat_returns["Returns"] = 0

        # print(df_temp)

        prev_signal = 0
        for i in range(1, len(strat_returns)):
            signal = strat_returns["Signal"].iloc[i]
            if signal == 1:
                strat_returns["Returns"].iloc[i] = (
                    strat_returns[ticker_strat].iloc[i]
                    / strat_returns[ticker_strat].iloc[i - 1]
                ) - 1
                if prev_signal != 1:
                    strat_returns["Returns"].iloc[i] -= transaction_costs / 10000
            else:
                strat_returns["Returns"].iloc[i] = 0
                if prev_signal == 1:
                    strat_returns["Returns"].iloc[i] -= transaction_costs / 10000
            prev_signal = signal

        strat_returns["All Returns"] = strat_returns[ticker_strat].pct_change()

        # Call the calculate_kpis function to get the KPI data
        table_html = calculate_kpis(strat_returns)

        buys = ohlc_dict[ticker_signal][ohlc_dict[ticker_signal]["Position"] == 1].index
        sells = ohlc_dict[ticker_signal][
            ohlc_dict[ticker_signal]["Position"] == -1
        ].index

        buys = buys.strftime("%Y-%m-%d").tolist()
        sells = sells.strftime("%Y-%m-%d").tolist()

        # Call the generate_charts function and get the chart_data
        chart_data = generate_charts(
                ohlc_dict,
                ticker_signal,
                short,
                long,
                ind,
                ticker_strat,
                strat_returns,
                buys,
                sells,
            )

        session["symbol"] = symbol
        session["short"] = short
        session["long"] = long
        session["ind"] = ind
        session["start_date"] = start_date
        session["end_date"] = end_date
        session["transaction_costs"] = transaction_costs

        # print('Chart data in app.py is ',chart_data)

        # Combine the json_chart_data and table_html into a single dictionary
        response_data = {
            "chart_data": chart_data.to_json(orient="split", index=False),
            "table_html": table_html,
        }

        # Return the combined data as a JSON response
        return jsonify(response_data)

    except ValueError:
        error_message = "Invalid ticker symbol. Please try again."
    print(error_message)
    return jsonify({"status": "error", "message": error_message})




@app.route("/get_rebalancing_data", methods=["POST"])
def handle_get_rebalancing_data():
    data = request.get_json()
    stock1 = data["stock1"]
    stock2 = data["stock2"]
    weight1 = data["weight1"]
    rebalancing_period = int(data["rebalancing_period"])
    start_date = data["start_date"]
    end_date = data["end_date"]
    result = get_rebalancing_data(
        stock1, stock2, weight1, rebalancing_period, start_date, end_date
    )
    return jsonify(result[0])

#this is for REBALANCING Strategy
@app.route("/get_return_data", methods=["POST"])
def handle_get_return_data():
    data = request.get_json()
    stock1 = data.get("stock1")
    stock2 = data.get("stock2")
    weight1 = data.get("weight1")
    rebalancing_period = data.get("rebalancing_period")
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    # Check if all required data is present in the request
    if not all([stock1, stock2, weight1, rebalancing_period, start_date, end_date]):
        return "Error: Missing data in the request", 400

    result = get_rebalancing_data(
        stock1, stock2, weight1, rebalancing_period, start_date, end_date
    )
    return_data_df = result[1]

    # Return the original DataFrame object
    return render_template("table.html", return_data_df=return_data_df)






if __name__ == "__main__":
    # Get the port number from the environment variable, or use 5000 as a fallback
    # port = int(os.environ.get("PORT", 5000))
    # Run the app on the specified port port=port
    # app.run(host="127.0.0.1:5000", debug=True)
    import sentry_sdk
    from flask import Flask
    sentry_sdk.init(
        dsn="https://1dee190f08c4c37438c3aefd02caf966@o349605.ingest.sentry.io/4506099975847936",
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
    )
    app.run(host="https://subsapp-9504fa1fc11f.herokuapp.com/", port=5000, debug=False)


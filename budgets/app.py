from flask import Flask, render_template, request, redirect, flash,Blueprint,url_for
import mysql.connector
from datetime import datetime
import os
from werkzeug.utils import secure_filename

# Flask Application
app = Flask(__name__)
app.secret_key = "your_secret_key"

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

budget_bp = Blueprint('budget', __name__, template_folder='templates', static_folder='static')



def get_db_connection():
    """Establish and return a database connection."""
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='roshni04',
        database='ProjectUFFT'
    )

def allowed_file(filename):
    """Check if the uploaded file is allowed based on extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@budget_bp.route('/')
def home():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Budgets")
    budgets = cursor.fetchall()
    connection.close()
    return render_template('home.html', budgets=budgets)


@budget_bp.route('/add_budget', methods=['GET', 'POST'])
def add_budget():
    # Fetch category names and their corresponding category_id from the "categories" table
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT category_id, name FROM categories')  # Fetch category names and IDs
    categories = cursor.fetchall()
    cursor.close()
    connection.close()

    if request.method == 'POST':
        category_id = request.form['category_id']  # Get the selected category_id
        if not category_id:
            flash('Category is required!', 'error')
            return redirect(url_for('budget.add_budget'))

        # Fetch the category_name based on the selected category_id
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT category_name FROM categories WHERE category_id = %s', (category_id,))
        category_row = cursor.fetchone()
        cursor.close()
        connection.close()

        if category_row:
            category_name = category_row['category_name']
        else:
            flash('Category not found!', 'error')
            return redirect(url_for('budget.add_budget'))

        budget_amount = float(request.form['amount'])
        threshold_amount = float(request.form['threshold_value'])
        start_date = request.form['start_date']
        end_date = request.form['end_date']  # Changed due_date to end_date
        recurring = int(request.form.get('recurring', 0))  # Default to 0 if not checked

        # Insert the budget into the database with the category_id and category_name
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO budgets (category, category_id, amount, threshold_value, start_date, end_date, recurring) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (category_name, category_id, budget_amount, threshold_amount, start_date, end_date, recurring)
        )

        connection.commit()
        connection.close()

        flash('Budget added successfully!', 'success')
        return redirect('/')

    return render_template('add_budget.html', categories=categories)



@budget_bp.route('/expenses', methods=['GET', 'POST'])
def expenses():
    if request.method == 'POST':
        budget_id = int(request.form['budget_id'])
        amount = float(request.form['amount'])
        description = request.form['description']
        date = request.form['date'] or datetime.now().strftime('%Y-%m-%d')
        receipt_path = None

        # Handle file upload
        if 'receipt' in request.files:
            receipt = request.files['receipt']
            if receipt and allowed_file(receipt.filename):
                # Ensure the 'uploads' directory exists
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                
                filename = secure_filename(receipt.filename)
                receipt_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                receipt.save(receipt_path)

        # Insert the expense into the Expenses table
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)  # Ensure dictionary mode here

        cursor.execute(
            """
            INSERT INTO Expenses (budget_id, amount, description, date, receipt_url) 
            VALUES (%s, %s, %s, %s, %s)
            """,
            (budget_id, amount, description, date, receipt_path)
        )

        # After inserting the expense, get the total expenses for the selected budget
        cursor.execute(
            """
            SELECT SUM(amount) AS total_expenses FROM Expenses WHERE budget_id = %s
            """,
            (budget_id,)
        )

        total_expenses_result = cursor.fetchone()

        # Handle the result: if it's None, set total_expenses to 0
        if total_expenses_result is not None:
            total_expenses = total_expenses_result['total_expenses'] if total_expenses_result['total_expenses'] is not None else 0
        else:
            total_expenses = 0

        # Fetch threshold_value for alert comparison
        cursor.execute("SELECT threshold_value FROM Budgets WHERE budget_id = %s", (budget_id,))
        threshold_result = cursor.fetchone()

        if threshold_result:
            threshold_value = threshold_result['threshold_value']
        else:
            threshold_value = 0

        # Insert alert if total_expenses exceed the threshold
        if total_expenses > threshold_value:
            alert_message = f"Alert: Your expenses for the {budget_id} category have exceeded the threshold of ${threshold_value}"
            cursor.execute(
                "INSERT INTO BudgetAlerts (budget_id, alert_type, alert_message, alert_date) VALUES (%s, %s, %s, %s)",
                (budget_id, "Threshold Exceeded", alert_message, datetime.now())
            )

        # Commit changes and close connection
        connection.commit()
        connection.close()

        flash('Expense added successfully!', 'success')
        return redirect('/')

    # Retrieve budgets for the dropdown list
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)  # Ensure dictionary mode here
    cursor.execute("SELECT * FROM Budgets")
    budgets = cursor.fetchall()
    connection.close()

    return render_template('expenses.html', budgets=budgets)





@budget_bp.route('/report')
def report():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Budgets")
    budgets = cursor.fetchall()

    cursor.execute("SELECT * FROM Expenses")
    expenses = cursor.fetchall()

    connection.close()

    # Process data for report
    budget_expenses = {}
    for expense in expenses:
        if expense['budget_id'] not in budget_expenses:
            budget_expenses[expense['budget_id']] = 0
        budget_expenses[expense['budget_id']] += expense['amount']

    budget_details = []
    for budget in budgets:
        total_expenses = budget_expenses.get(budget['budget_id'], 0)
        remaining_budget = budget['amount'] - total_expenses  # 'amount' instead of 'budget_amount'
        
        # Corrected to use 'threshold_value'
        if total_expenses >= budget['threshold_value'] and total_expenses < budget['amount']:
            alert_message = f"Warning: Your expenses (${total_expenses}) have reached the limit and are nearing your budget (${budget['amount']})."
        elif total_expenses == budget['amount']:
            alert_message = f"Alert: You’ve hit your budget of ${budget['amount']}; no more spending allowed!"
        elif total_expenses > budget['amount']:
            alert_message = f"Critical: Your expenses (${total_expenses}) have exceeded your budget (${budget['amount']})!"
        else:
            alert_message = "No Alert"
        
        budget_details.append({
            'category': budget['category'],
            'budget_amount': budget['amount'],  # 'amount' instead of 'budget_amount'
            'total_expenses': total_expenses,
            'remaining_budget': remaining_budget,
            'due_date': budget['end_date'],
            'alert_message': alert_message
        })

    return render_template('report.html', budget_details=budget_details)




@budget_bp.route('/edit_budget/<int:budget_id>', methods=['GET', 'POST'])
def edit_budget(budget_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        category = request.form['category']
        budget_amount = float(request.form['budget_amount'])
        cursor.execute(
            "UPDATE Budgets SET category = %s, budget_amount = %s WHERE budget_id = %s",
            (category, budget_amount, budget_id)
        )
        connection.commit()
        connection.close()
        flash('Budget updated successfully!', 'success')
        return redirect('/')

    cursor.execute("SELECT * FROM Budgets WHERE budget_id = %s", (budget_id,))
    budget = cursor.fetchone()
    connection.close()
    return render_template('edit_budget.html', budget=budget)

# Run the Application
if __name__ == '__main__':
    app.run(debug=True)

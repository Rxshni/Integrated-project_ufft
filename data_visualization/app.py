from flask import Flask, render_template, send_file, request,Blueprint,url_for
import mysql.connector
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors



data_visualization_bp = Flask(__name__)

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'roshni04',
    'database': 'ProjectUFFT'
}




data_visualization_bp = Blueprint('data_visualization', __name__, template_folder='templates', static_folder='static')


# Utility function to fetch database connection
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Route to fetch user-specific data
@data_visualization_bp.route('/', methods=['GET', 'POST'])
def index():
    selected_user_id = None
    search_query = None
    expense_data = []
    category_totals = {}
    user_ids = []

    # Fetch all unique user IDs
    with get_db_connection() as connection:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT DISTINCT user_id FROM expenses")
            user_ids = [row['user_id'] for row in cursor.fetchall()]

    if request.method == 'POST':
        selected_user_id = request.form.get('user_id')
        search_query = request.form.get('search_query', '').strip()

        try:
            selected_user_id = int(selected_user_id)
        except (ValueError, TypeError):
            selected_user_id = None

        if selected_user_id:
            with get_db_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    sql = """
                        SELECT e.expense_id, c.name AS category, e.amount, e.date, e.description
                        FROM expenses e
                        JOIN categories c ON e.category_id = c.category_id
                        WHERE e.user_id = %s
                    """
                    if search_query:
                        sql += " AND e.description LIKE %s"
                        cursor.execute(sql, (selected_user_id, f"%{search_query}%"))
                    else:
                        cursor.execute(sql, (selected_user_id,))
                    
                    expenses = cursor.fetchall()

                    expense_data = [
                        {
                            'expense_id': exp['expense_id'],
                            'category': exp['category'],
                            'amount': exp['amount'],
                            'date': exp['date'].strftime("%d-%m-%Y"),
                            'description': exp['description'] or "N/A"
                        } for exp in expenses
                    ]

                    # Prepare data for chart
                    for exp in expenses:
                        category_totals[exp['category']] = category_totals.get(exp['category'], 0) + exp['amount']

    return render_template(
        'index1.html',
        user_ids=user_ids,
        selected_user_id=selected_user_id,
        search_query=search_query,
        expenses=expense_data,
        category_totals=category_totals
    )

# Route to download CSV
@data_visualization_bp.route('/download/csv')
def download_csv():
    selected_user_id = request.args.get('user_id', type=int)

    with get_db_connection() as connection:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT e.expense_id, c.name AS category, e.amount, e.date, e.description
                FROM expenses e
                JOIN categories c ON e.category_id = c.category_id
                WHERE e.user_id = %s
            """, (selected_user_id,))
            expenses = cursor.fetchall()

    data = {
        'Expense ID': [exp['expense_id'] for exp in expenses],
        'Category': [exp['category'] for exp in expenses],
        'Amount': [exp['amount'] for exp in expenses],
        'Date': [exp['date'].strftime("%d-%m-%Y") for exp in expenses],
        'Description': [exp['description'] or "N/A" for exp in expenses]
    }

    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8')
    output.seek(0)

    return send_file(output, as_attachment=True, download_name='expenses.csv', mimetype='text/csv')

# Route to download Excel
@data_visualization_bp.route('/download/excel')
def download_excel():
    selected_user_id = request.args.get('user_id', type=int)

    with get_db_connection() as connection:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT e.expense_id, c.name AS category, e.amount, e.date, e.description
                FROM expenses e
                JOIN categories c ON e.category_id = c.category_id
                WHERE e.user_id = %s
            """, (selected_user_id,))
            expenses = cursor.fetchall()

    data = {
        'Expense ID': [exp['expense_id'] for exp in expenses],
        'Category': [exp['category'] for exp in expenses],
        'Amount': [exp['amount'] for exp in expenses],
        'Date': [exp['date'].strftime("%d-%m-%Y") for exp in expenses],
        'Description': [exp['description'] or "N/A" for exp in expenses]
    }

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Expenses')
    output.seek(0)

    return send_file(output, as_attachment=True, download_name='expenses.xlsx', mimetype='data_visualization_bplication/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# Route to download PDF
@data_visualization_bp.route('/download/pdf')
def download_pdf():
    selected_user_id = request.args.get('user_id', type=int)

    with get_db_connection() as connection:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT e.expense_id, c.name AS category, e.amount, e.date, e.description
                FROM expenses e
                JOIN categories c ON e.category_id = c.category_id
                WHERE e.user_id = %s
            """, (selected_user_id,))
            expenses = cursor.fetchall()

    data = [['Expense ID', 'Category', 'Amount', 'Date', 'Description']]
    data += [
        [exp['expense_id'], exp['category'], f"{exp['amount']:.2f}", exp['date'].strftime("%Y-%m-%d"), exp['description'] or "N/A"]
        for exp in expenses
    ]

    pdf_output = BytesIO()
    doc = SimpleDocTemplate(pdf_output, pagesize=letter)
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    doc.build([Paragraph("Expense Report", getSampleStyleSheet()['Heading1']), Spacer(1, 12), table])
    pdf_output.seek(0)

    return send_file(pdf_output, as_attachment=True, download_name="expenses.pdf", mimetype="data_visualization_bplication/pdf")

if __name__ == '__main__':
    data_visualization_bp.run(debug=True)

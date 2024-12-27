import mysql.connector
from datetime import datetime 
from flask import Flask,request,render_template,jsonify,redirect,url_for,Blueprint
import os
from werkzeug.utils import secure_filename
## initializing the flask application
app=Flask(__name__)

UPLOAD_FOLDER = 'Expense/static/uploads/receipts'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


expense_bp = Blueprint('expense', __name__, template_folder='templates', static_folder='static')





@expense_bp.route('/upload_receipt', methods=['POST'])
def upload_receipt():
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('expense.index'))




#configuring the connection with the database

db_config={
    'host':'localhost',
    'user':'root',
    'password':'roshni04',
    'database':'ProjectUFFT',
    'port':3306
}

#establishing a conenction with the database using the configuration
connect_=mysql.connector.connect(**db_config)
cursor=connect_.cursor()

########### ESTABLISHING A ROUTE FOR THE HTML REQUEST

@expense_bp.route('/') #creates a root route for the flask application
 #index function that returnrs the HTML content from the file and sends it to the user as a response for accessing the root URL
def index():
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute("SELECT expense_id,date,name,amount,description,receipt FROM expenses e1 JOIN categories c1 where e1.category_id=c1.category_id ORDER BY expense_id DESC")
    expenses=cursor.fetchall()
    
    expense_records=[
        {
            'expense_id':exp[0],
            'date_in':exp[1],
            'category':exp[2],            
            'amount':exp[3],
            'desc':exp[4],
            'receipt':exp[5]            
        }
        for exp in expenses
    ]
    return render_template('index.html', expenses=expense_records,max_date=current_date) #Flask by default looks for templkate forlder to render the html file



###### getting the form data and calling the add expense function
@expense_bp.route('/get_form_data',methods=['POST'])
def get_form_data():
    
    user_id=1
    
    family_id=1
    
    category=request.form.get('category')
    #print("Category being queried:", category)

    cursor.execute("SELECT category_id FROM categories WHERE name=%s",(category,))
    res=cursor.fetchone()
    category_id=res[0]
    
    
    date_in=request.form.get('date')
    #print(date_in)
        
    amount=float(request.form.get('amount'))
    #print(amount)
    
    description=request.form.get('desc')
    if not description :
        description=""
    #print(description)
        
    # Handle the receipt file upload
    receipt_file = request.files['file']
    receipt_filename = None
    if receipt_file:
        receipt_filename = secure_filename(receipt_file.filename)
        receipt_file.save(os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename))
        receipt = receipt_filename
    
    # Add the expense to the database
    add_expense(user_id, family_id, category_id, amount, date_in, description, receipt)
    
    return redirect(url_for('expense.index')) ##### this returns a success message 


####### ADD EXPENSE ###########

def add_expense(user_id,family_id,category_id,amount,date_in,description,receipt):
   
    cursor.execute("INSERT INTO EXPENSES (user_id,category_id,date,amount,description,family_id,receipt) VALUES (%s,%s,%s,%s,%s,%s,%s)",(user_id,category_id,date_in,amount,description,family_id,receipt,))
    connect_.commit() #reflects in our database
   
########## to delete the expense #######
@expense_bp.route('/delete_expense/<int:expense_id>',methods=["POST"])
def delete_expense(expense_id):
    cursor.execute("DELETE FROM expenses WHERE expense_id=%s",(expense_id,))
    connect_.commit()
    return redirect(url_for('expense.index'))

if __name__=="__main__":
    app.run(debug=True,port=8000)

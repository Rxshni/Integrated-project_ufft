from flask import Flask, request, render_template, redirect, url_for, session,flash,make_response,Blueprint
import mysql.connector
import re
import smtplib
import random
from email.message import EmailMessage
import random
import string
import random


app = Flask(__name__)
app.secret_key = 'ProjectUFFT'

con = mysql.connector.connect(host='localhost', user='root', password='roshni04', database='ProjectUFFT')
cur = con.cursor(buffered=True)

user_reg_bp = Blueprint('user_reg', __name__, template_folder='templates', static_folder='static')




def is_username_taken(username):
    query = "SELECT COUNT(*) FROM users WHERE user_name = %s"
    cur.execute(query, (username,))
    count = cur.fetchone()[0]
    return count > 0

def is_valid_password(password):
    special_characters = "!@#$%^&*(),.?\":{}|<>"
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    has_lowercase = False
    has_uppercase = False
    has_digit = False
    has_special = False
    for char in password:
        if char.islower():
            has_lowercase = True
        elif char.isupper():
            has_uppercase = True
        elif char.isdigit():
            has_digit = True
        elif char in special_characters:
            has_special = True
    if not has_lowercase:
        return False, "Password must include at least one lowercase letter."
    if not has_uppercase:
        return False, "Password must include at least one uppercase letter."
    if not has_digit:
        return False, "Password must include at least one digit."
    if not has_special:
        return False, "Password must include at least one special character."

    return True, "Password is valid."

def validate_phone_number(phone_no):
    if len(str(phone_no)) != 10:
        return "Enter a valid phone number (10 digits)."
    
    elif str(phone_no)[0] not in "6789":
        return "Phone number should start with 6, 7, 8, or 9."
    return None




def validate_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email)

def otp_gen(email):
    otp=""
    for i in range(4):
        otp+=str(random.randint(0,9))
    server=smtplib.SMTP('smtp.gmail.com',587)
    server.starttls()
    server.login('dum31555@gmail.com',"dweg wzyz mbfa wvkv")
    to_mail=email
    from_mail="dum31555@gmail.com"
    msg=EmailMessage()
    msg['Subject']="OTP Verification"
    msg['From']=from_mail
    msg['To']=to_mail
    msg.set_content("Your OTP is : " + otp)
    server.send_message(msg)
    return otp

def validate_account_number(account_number):
    if account_number.isdigit() and 9 <= len(account_number) <= 18:
        return True
    else:
        return False




@user_reg_bp.route("/")
def index():
    return render_template("home.html")

@user_reg_bp.route("/signup",methods=['GET','POST'])
def signup():
    if request.method=="GET":
        return render_template("signup.html")
    else:
         name = request.form['name']
         user_name = request.form['username']
         password = request.form['password']
         phone_no=request.form['phone']
         email = request.form['email']


         session['name'] = name
         session['user_name'] = user_name
         session['password'] = password
         session['phone_no']=phone_no
         session['email'] = email

         if is_username_taken(user_name):
             return render_template('signup.html', error="The username already exists. Please choose a different one.")
         
         is_valid, message = is_valid_password(password)
         if not is_valid:
            return render_template('signup.html', error=f"{message}")
         
         error_message = validate_phone_number(phone_no)
         if error_message:
            return render_template('signup.html', error=f"{error_message}")
         
         if not validate_email(email):
            return render_template('signup.html', error="Not a valid email adress")
         
         otp=otp_gen(email)
         session['otp']=otp
         

    return redirect(url_for('user_reg.otp'))




@user_reg_bp.route("/otp",methods=['GET','POST'])
def otp():
    if request.method=='GET':
        return render_template("otp.html")
    else:
        user_otp=request.form['otp']
        mail_otp=session.get('otp')

        if user_otp==mail_otp:
            return redirect(url_for('user_reg.bankAcc'))
        else:
            return render_template('otp.html',error="Incorrect OTP")




@user_reg_bp.route("/bankAcc",methods=['GET','POST'])
def bankAcc():
    if request.method=='GET':
        return render_template("bankAcc.html")
    else:
        bank_acc_no=request.form['acc']
        role=request.form['role']

        if not validate_account_number(bank_acc_no):
            return render_template('bankAcc.html', error="Invalid account number. It must be a digit and between 9 and 18 digits long.")

        name=session.get('name')
        user_name=session.get('user_name')
        password=session.get('password')
        phone_no=session.get('phone_no')
        email=session.get('email')
        cur.execute("insert into users (name,user_name,password,phone_no,email,bank_acc_no,role) values (%s,%s,%s,%s,%s,%s,%s)",(name,user_name,password,phone_no,email,bank_acc_no,role))
        con.commit()

    return redirect(url_for('user_reg.welcome'))

@user_reg_bp.route("/welcome")
def welcome():
    return render_template('welcome.html')
    


if __name__ == '__main__':
    app.run(debug=True,port=8000)
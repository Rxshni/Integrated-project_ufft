from flask import Flask, request, render_template, redirect, url_for, session,flash,make_response,Blueprint
import mysql.connector
import re
import smtplib
import random
from email.message import EmailMessage
import random
import string
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta



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

def check_account(login_name,login_pass):
    cur.execute("select user_name from users where user_name = %s",(login_name,))
    row=cur.fetchone()
    if row!=None:
        cur.execute("select password from users where user_name = %s", (login_name,))
        row=cur.fetchone()
        if row==(login_pass,):
            return True,"Successfull login"
        else:
            return False,"Invalid password"
    else:
        return False,"Invalid username"

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
    
def reset_pass(email):
    pass_otp=""
    for i in range(4):
        pass_otp+=str(random.randint(0,9))
    server=smtplib.SMTP('smtp.gmail.com',587)
    server.starttls()
    server.login('dum31555@gmail.com',"dweg wzyz mbfa wvkv")
    to_mail=email
    from_mail="dum31555@gmail.com"
    msg=EmailMessage()
    msg['Subject']="Reset password"
    msg['From']=from_mail
    msg['To']=to_mail
    msg.set_content("Your OTP is to reset password is : " + pass_otp)
    server.send_message(msg)
    return pass_otp



def generate_family_code(cur):
    while True:
        
        family_code = random.randint(100000, 999999)
        
        cur.execute("SELECT COUNT(*) FROM users WHERE family_id = %s", (family_code,))
        if cur.fetchone()[0] == 0:  
            return family_code

def member_code(mem_code):
    cur.execute("SELECT COUNT(*) FROM users WHERE family_id = %s", (mem_code,))
    members_count = cur.fetchone()[0]
        
    if members_count >= 8:
        return False, 'Family code already has 8 members. You cannot join this family.'
    elif members_count > 0:
        return True,'Sucess'
    else:
        return False,'Family code not found. Please try again'


@user_reg_bp.route("/")
def index():
    return render_template("home_1.html")

@user_reg_bp.route("/signup",methods=['GET','POST'])
def signup():
    if request.method=="GET":
        return render_template("signup.html")
    else:
         name = request.form['name']
         user_name = request.form['username']
         password = request.form['password']
         dob= request.form['DOB']
         phone_no=request.form['phone']
         email = request.form['email']


         session['name'] = name
         session['user_name'] = user_name
         session['password'] = password
         session['dob'] = dob
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

@user_reg_bp.route('/signin',methods=['GET','POST'])
def signin():
    if request.method=='GET':
        return render_template('signin.html')
    else:
         login_name = request.form['login_name']
         login_pass = request.form['login_pass']
         
         val, mess =check_account(login_name,login_pass)
         if not val:
            return render_template('signin.html', error=f"{mess}")
         
    return redirect(url_for('user_reg.welcome'))

@user_reg_bp.route('/get_mail',methods=['GET','POST'])
def get_mail():
    if request.method=='GET':
        return render_template('email.html')
    else:
        pass_email=request.form['email_otp']
        pass_user=request.form['user']

        pass_otp=reset_pass(pass_email)
        session['pass_otp']=pass_otp
        session['pass_email']=pass_email
        session['pass_user']=pass_user
    return redirect(url_for('user_reg.forgot_password'))

@user_reg_bp.route('/forgot_password',methods=['GET','POST'])
def forgot_password():

    if request.method=='GET':
        return render_template('pass_otp.html')
    else:
        user_otp=request.form['passOTP']
        mail_pass=session.get('pass_otp')

        if user_otp==mail_pass:
            if user_otp==mail_pass:
                return redirect(url_for('user_reg.reset'))
        else:
            return render_template('pass_otp.html',error="Incorrect OTP")
            

@user_reg_bp.route('/reset',methods=['GET','POST'])
def reset():
    if request.method=='GET':
        return render_template('reset.html')
    else:
        new_pass=request.form['new_pass']
        new_user=session.get('pass_user')
        cur.execute("UPDATE users SET password = %s WHERE user_name = %s", 
                        (new_pass, new_user))
        con.commit()
    return redirect(url_for('user_reg.signin'))




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
        dob=session.get('dob')
        phone_no=session.get('phone_no')
        email=session.get('email')
        cur.execute("insert into users (name,user_name,password,phone_no,email,bank_acc_no,role,dob) values (%s,%s,%s,%s,%s,%s,%s,%s)",(name,user_name,password,phone_no,email,bank_acc_no,role,dob))
        con.commit()

        if role=='HOF':
            hof_code=generate_family_code(cur)
            session['hof_code']=hof_code
            cur.execute("update users set family_id=%s where user_name=%s",(hof_code,user_name))
            con.commit()
            return redirect(url_for('user_reg.hof'))
        elif role=='Member':
            return redirect(url_for('user_reg.member'))
        else:
            return redirect(url_for('user_reg.welcome'))



@user_reg_bp.route("/hof",methods=['GET','POST'])
def hof():
    if request.method=='GET':
        hof_code=session.get('hof_code')
        message=hof_code
        return render_template("hof.html",message=message)
    return redirect(url_for('user_reg.welcome'))
    
@user_reg_bp.route("/member",methods=['GET','POST'])
def member():
    if request.method=='GET':
        return render_template("member.html")
    elif request.method=='POST':
        mem_code=request.form['code']
        user_name=session.get('user_name')
        is_valid, message = member_code(mem_code)
        if not is_valid:
            return render_template('member.html', error=f"{message}")
        else:
            cur.execute("update users set family_id=%s where user_name=%s",(mem_code,user_name))
            con.commit()
    return redirect(url_for('user_reg.welcome'))




@user_reg_bp.route("/del_acc",methods=['GET','POST'])
def del_acc():
    if request.method=='GET':
        return render_template("delAcc.html")
    else:
        del_user=request.form['del_user']
        del_pass=request.form['del_pass']
        session['user']=del_user
        cur.execute("select role from users where user_name=%s",(del_user,))
        
        row=cur.fetchone()

        if row==('HOF',) or row==('hof',):
            cur.execute("select family_id from users where user_name=%s",(del_user,))
            fam_row=cur.fetchone()
            session['family_id'] = fam_row[0]
            return redirect(url_for('user_reg.options'))
        elif row==('Member',) or row==('None',) :
            cur.execute("delete from users where user_name=%s", (del_user,))
            con.commit()
            return redirect(url_for('user_reg.index'))
        

    
@user_reg_bp.route("/options",methods=['GET','POST'])
def options():
    if request.method=='GET':
        return render_template("options.html")
    else:
        opt=request.form['1']
        if opt=='assign_hof':
            return redirect(url_for('user_reg.new_hof'))
        elif opt=='full' :
            user=session.get('user')
            fam_id=session.get('family_id')
            cur.execute("UPDATE users SET family_id = NULL WHERE family_id = %s", (fam_id,))


            cur.execute("DELETE FROM users WHERE user_name = %s", (user,))
            con.commit()
            return redirect(url_for('user_reg.index'))

        elif opt=='fam' :
            fam_id=session.get('family_id')
            cur.execute("UPDATE users SET family_id = NULL WHERE family_id = %s", (fam_id,))
            con.commit()
            return redirect(url_for('user_reg.welcome'))

        
    

@user_reg_bp.route("/new_hof",methods=['GET','POST'])
def new_hof():
    if request.method=='GET':
        fam_id=session.get('family_id')
        cur.execute("SELECT user_name FROM users WHERE family_id = %s", (fam_id,))
        rows = cur.fetchall()
        
        names = [row[0] for row in rows]
        return render_template("new_hof.html",names=names)
    else :
        new_hof=request.form['new_hof']
        user=session.get('user')
        cur.execute("UPDATE users SET role = 'hof' WHERE user_name = %s", (new_hof,))
        cur.execute("delete from users where user_name=%s", (user,))
        con.commit()
        return redirect(url_for('user_reg.index'))
    


       


@user_reg_bp.route("/welcome")
def welcome():
    return render_template('welcome.html')
    


if __name__ == '__main__':
    app.run(debug=True,port=8000)
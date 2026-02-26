from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import re
from config import config

app = Flask(__name__)

# 根据环境变量选择配置
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 自定义过滤器
@app.template_filter('nl2br')
def nl2br_filter(text):
    if text:
        return text.replace('\n', '<br>')
    return text

# 数据模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    company_description = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200))
    salary_range = db.Column(db.String(100))
    job_type = db.Column(db.String(50))  # 全职/兼职/实习
    experience_level = db.Column(db.String(50))  # 初级/中级/高级
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    benefits = db.Column(db.Text)
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 路由
@app.route('/')
def index():
    jobs = Job.query.filter_by(is_active=True).order_by(Job.posted_at.desc()).limit(10).all()
    companies = User.query.filter_by(is_admin=False).all()
    return render_template('index.html', jobs=jobs, companies=companies)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        company_name = request.form['company_name']
        company_description = request.form['company_description']
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            company_name=company_name,
            company_description=company_description
        )
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_jobs = Job.query.filter_by(posted_by=current_user.id).order_by(Job.posted_at.desc()).all()
    return render_template('dashboard.html', jobs=user_jobs)

@app.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if request.method == 'POST':
        job = Job(
            title=request.form['title'],
            company_name=current_user.company_name,
            location=request.form['location'],
            salary_range=request.form['salary_range'],
            job_type=request.form['job_type'],
            experience_level=request.form['experience_level'],
            description=request.form['description'],
            requirements=request.form['requirements'],
            benefits=request.form['benefits'],
            contact_email=request.form['contact_email'],
            contact_phone=request.form['contact_phone'],
            posted_by=current_user.id
        )
        db.session.add(job)
        db.session.commit()
        flash('职位发布成功')
        return redirect(url_for('dashboard'))
    
    return render_template('post_job.html')

@app.route('/jobs')
def jobs():
    page = request.args.get('page', 1, type=int)
    company_filter = request.args.get('company', '')
    title_filter = request.args.get('title', '')
    location_filter = request.args.get('location', '')
    job_type_filter = request.args.get('job_type', '')
    
    query = Job.query.filter_by(is_active=True)
    
    if company_filter:
        query = query.filter(Job.company_name.contains(company_filter))
    if title_filter:
        query = query.filter(Job.title.contains(title_filter))
    if location_filter:
        query = query.filter(Job.location.contains(location_filter))
    if job_type_filter:
        query = query.filter(Job.job_type == job_type_filter)
    
    jobs = query.order_by(Job.posted_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    companies = User.query.filter_by(is_admin=False).all()
    
    return render_template('jobs.html', jobs=jobs, companies=companies)

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('job_detail.html', job=job)

@app.route('/api/jobs')
def api_jobs():
    company_filter = request.args.get('company', '')
    title_filter = request.args.get('title', '')
    
    query = Job.query.filter_by(is_active=True)
    
    if company_filter:
        query = query.filter(Job.company_name.contains(company_filter))
    if title_filter:
        query = query.filter(Job.title.contains(title_filter))
    
    jobs = query.order_by(Job.posted_at.desc()).limit(20).all()
    
    return jsonify([{
        'id': job.id,
        'title': job.title,
        'company_name': job.company_name,
        'location': job.location,
        'salary_range': job.salary_range,
        'job_type': job.job_type,
        'experience_level': job.experience_level,
        'posted_at': job.posted_at.strftime('%Y-%m-%d')
    } for job in jobs])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # 获取配置
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 8080)
    debug = app.config.get('DEBUG', True)
    
    print(f"🌐 服务器启动在: http://{host}:{port}")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    print(f"📱 局域网访问: http://[您的IP地址]:{port}")
    
    app.run(debug=debug, port=port, host=host) 
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import date
import csv
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)

# UPLOAD_FOLDER = 'static/images/projects/'
UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DATABASEITEMSPOINT = 'items.csv'
DATABASENAMEITEMS = "evaluation.csv"
DATABASEUSERS = "users.csv"
DATABASEPROJECTS = "projects.csv"
DATABASBLOGS = "blogs.csv"
DATABASEUSEDITEMS = "used_items.csv"
delimiter = "\t"

app.secret_key = 'secret_pain'
# Получить путь к директории приложения
app_path = app.root_path
# Получить путь к статическим файлам
static_path = os.path.join(app_path, 'static')
# Получить путь к шаблонам
templates_path = os.path.join(app_path, 'templates')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash('You need to log in first.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def count_points(id):
    points = 0
    with open(DATABASEPROJECTS, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=delimiter)
        for row in reader:
            if 'author' in row and row['author'] == id:
                points += int(row['points'])
    return points


def get_author_by_project_id(project_id):
    # Возвращает автора проекта по id проекта
    #id	points	project_name	project_resume	project_text	author	project_img
    with open(DATABASEPROJECTS, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter, lineterminator="\r")
        for row in reader:
            if str(project_id) == str(row['id']):
                author_id = row['author']
                user = read_user(author_id)
        return user


def get_who_by_id(file_path, user_id):
    # Возвращает значение who по id пользователя
    #id	name	surname	email	password	date	who	points_remainder	room
    with open(file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        headers = next(reader)
        for row in reader:
            if row[0] == str(user_id):
                return row[6]
    return None


def write_used_items(used_items: list) -> list:
    file_path = DATABASEUSEDITEMS

    # Сначала загрузим существующие данные
    existing_items = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=delimiter)
            existing_items = list(reader)
    except FileNotFoundError:
        # Если файл не найден, начнем с пустого списка
        pass

    # Добавим новые элементы
    existing_items.append(used_items)

    # Запишем все обратно в файл
    with open(file_path, mode='w', encoding='utf-8', newline='') as file:
        if existing_items:
            writer = csv.DictWriter(file, fieldnames=existing_items[0].keys(), delimiter=delimiter)
            writer.writeheader()
            writer.writerows(existing_items)
    return used_items


def read_csv(filename):
    with open(filename, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter, lineterminator="\r")
        data = []
        for row in reader:
            data.append(row)
        return data


def read_project(id):
    with open(DATABASEPROJECTS, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter, lineterminator="\r")
        for project in reader:
            if project['id'] == str(id):
                return project


def read_blog(id):
    with open(DATABASBLOGS, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter, lineterminator="\r")
        for blog in reader:
            if 'id' in blog and blog['id'] == str(id):
                return blog


def clean_text(text: str) -> str:
    return text.replace(delimiter, "").replace("\n", "").replace("\r", "")


def update_points_in_user(target_id, new_points):
    file_path = DATABASEUSERS
    id_found = False
    updated_rows = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=delimiter)
        header = reader.fieldnames
        for row in reader:
            if row['id'] == target_id:
                row['points_remainder'] = str(int(row['points_remainder']) + int(new_points))
                id_found = True
            updated_rows.append(row)
    if id_found:
        with open(file_path, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=header, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(updated_rows)
    else:
        return "Update_point_in_user, no id_found"
    return new_points


def update_blog(file_path, updated_values):
    id_found = False
    updated_rows = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=delimiter)
        header = reader.fieldnames
        for row in reader:
            if 'id' in row and row['id'] == updated_values['id']:
                if 'blog_img' in row and 'blog_img' in updated_values:
                    row['blog_img'] = updated_values['blog_img']
                if 'blog_title' in row and 'blog_title' in updated_values:
                    row['blog_title'] = updated_values['blog_title']
                if 'blog_text' in row and 'blog_text' in updated_values:
                    row['blog_text'] = updated_values['blog_text']
                id_found = True
            updated_rows.append(row)
    if id_found:
        with open(file_path, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=header, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(updated_rows)
    else:
        return "Update blog, no id_found"

    return updated_values


def read_user(id):
    with open(DATABASEUSERS, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter, lineterminator="\r")
        for user in reader:
            if user['id'] == str(id):
                if 'password' in user:
                    user.pop('password')
                return user


def find_id_author_by_project_id(id):
    with open(DATABASEPROJECTS, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter, lineterminator="\r")
        for project in reader:
            if project['id'] == str(id):
                return project['author']


def check_user(email, password):
    with open(DATABASEUSERS, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter, lineterminator="\r")
        for user in reader:
            if "email" in user and user['email'] == email and "password" in user and check_password_hash(user['password'], password):
                return user


def count_id(filename):
    first_column_values = []
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line:
                values = line.split(delimiter)
                first_column_values.append(values[0])
    try:
        id = int(first_column_values[-1]) + 1
    except:
        id = 0
    return id


def write_csv(filename, values):
    with open(filename, 'a', encoding='utf-8') as file:
        file_writer = csv.writer(file, delimiter=delimiter, lineterminator="\r")
        file_writer.writerow(values)
    return values


def chech_unic(email):
    with open(DATABASEUSERS, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter, lineterminator="\r")
        for user in reader:
            if 'email' in user and user['email'] == email:
                return False
    return True


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def read_evalation():
    data = {}
    with open(DATABASENAMEITEMS, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=delimiter)
        for row in reader:
            if 'user_id' in row:
                if 'item_id' in row:
                    if row['user_id'] in data and len(data[row['user_id']]) > 0:
                        data[row['user_id']].append(row['item_id'])
                    else:
                        value = row['item_id']
                        data[row['user_id']] = [value]
    return data


def put_users_data_items(data):
    user_items = []
    for key, values in data.items():
        list_items = []
        new_dict = read_user(key)
        for value in values:
            dict_items = {}
            item = read_item(value)
            if item:
                if 'id' in item and 'value' in item and 'point' in item:
                    dict_items['id'] = item['id']
                    dict_items['value'] = item['value']
                    dict_items['point'] = item['point']
                    list_items.append(dict_items)
            new_dict['value'] = list_items
        user_items.append(new_dict)
    return user_items


def read_item(id):
    with open(DATABASEITEMSPOINT, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter, lineterminator="\r")
        for item in reader:
            if item['id'] == str(id):
                return item


def read_all_items():
    with open(DATABASEITEMSPOINT, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter, lineterminator="\r")
        items = []
        for item in reader:
            items.append(item)
        return items


def update_points_in_projects(file_path, target_id, new_points):
    id_found = False
    updated_rows = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=delimiter)
        header = reader.fieldnames
        for row in reader:
            if str(row['id']) == str(target_id):
                row['points'] = str(int(row['points']) + int(new_points))
                id_found = True
            updated_rows.append(row)
    if id_found:
        with open(file_path, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=header, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(updated_rows)
    else:
        return "Пользователь не найден"
    return new_points


def chec_unic_options(user_id, option):
    with open(DATABASENAMEITEMS, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter, lineterminator="\r")
        for item in reader:
            if 'user_id' in item and item['user_id'] == user_id and 'item_id' in item and item['item_id'] == option:
                return False
    return True


def count_used_points(user_id):
    new_data = {}
    used_point_data = []
    with open(DATABASEUSEDITEMS, mode='r', encoding='utf-8') as file:
        items = csv.DictReader(file, delimiter=delimiter, lineterminator="\r")
        for item in items:
            # teacher_id item_id point date
            if 'student_id' in item and str(item['student_id']) == str(user_id):
                if 'teacher_id' in item:
                    teacher_id = item['teacher_id']
                    value_item = read_item(item['item_id'])['value']
                    new_item = {
                        'item_id': item['item_id'],
                        'point': item['point'],
                        'value': value_item,
                        'date': item['date'],
                        }
                    if teacher_id in new_data:
                        new_data[teacher_id].append(new_item)
                    else:
                        new_data[teacher_id] = [new_item]

        for key, value in new_data.items():
            user_dict = {}
            user = read_user(key)
            user_dict['id'] = key
            user_dict['user'] = user
            user_dict['used_items'] = value
            used_point_data.append(user_dict)
    return used_point_data


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    email = None
    password = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = check_user(email, password)
        if user:
            if "email" in user:
                session['email'] = email
                if "id" in user:
                    session['id'] = user['id']
                return redirect(url_for('mainpage'))
            else:
                flash('Неправильный логин или пароль')
        else:
            flash('Неправильный логин или пароль')
    return render_template('login.html')


@app.route('/login/registration', methods=['GET', 'POST'])
def registration():
    name = None
    surname = None
    email = None
    password = None
    date = None
    who = None
    room = None
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        password = request.form['password']
        date = request.form['date']
        who = request.form['who']
        room = request.form['room']
        certificate = request.form['certificate']
        if chech_unic(email):
            if who == "Ученик":
                id = count_id(DATABASEUSERS)
                password_hashed = generate_password_hash(password)
                values = [id, name, surname, email, password_hashed, date, who, room]
                write_csv(DATABASEUSERS, values)
                session['email'] = email
                session['id'] = id
                return redirect(url_for("mainpage"))
            elif who == "Учитель":
                f = open("keys.txt")
                a = f.readlines()
                flag = False
                for i in range(len(a)):
                    if a[i] == certificate or a[i] == certificate + "\n":
                        flag = True
                        id = count_id(DATABASEUSERS)
                        password_hashed = generate_password_hash(password)
                        values = [
                            id,
                            name,
                            surname,
                            email,
                            password_hashed,
                            date,
                            who,
                            room
                            ]
                        write_csv(DATABASEUSERS, values)
                        session['email'] = email
                        session['id'] = id
                        return redirect(url_for("mainpage"))
                if not flag:
                    flash("Неверный код")
        else:
            flash("Этот email уже зарегистрирован")
    return render_template('registration.html')


@app.route('/login/mainpage')
@login_required
def mainpage():
    projects = []
    with open(DATABASEPROJECTS, mode='r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file, delimiter=delimiter, lineterminator="\r")
        for project in csv_reader:
            projects.append(project)
    return render_template(
        'projects_stellar.html',
        users_projects=projects
        )


@app.route("/blog/<string:id>/", methods=['GET', 'POST'])
@login_required
def blog(id):
    blog = read_blog(id)
    blog['user'] = None
    if 'user_id' in blog:
        blog['user'] = read_user(blog['user_id'])
    return render_template(
                'blog.html',
                blog=blog
                )


@app.route('/blog/create', methods=['GET', 'POST'])
@login_required
def blog_create():
    user_id = None
    blog_title = None
    blog_text = None
    blog_img = None
    data_creation = date.today()
    user = read_user(session["id"])
    if user['who'] == "Ученик":
        return redirect(url_for('blogs'))
    if request.method == 'POST':
        blog_title = request.form['title']
        blog_text = request.form['text']
        if 'file' not in request.files:
            flash('Нет файла для загрузки')
        else:
            file_img = request.files['file']
            if file_img and allowed_file(file_img.filename):
                filename_img = secure_filename(file_img.filename)
                file_img.save(os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    filename_img
                    ))
                blog_img = filename_img
                flash('Файл успешно загружен!')
        filename = DATABASBLOGS
        id = count_id(filename)
        user_id = session['id']
        values = [id, user_id, data_creation, blog_img, clean_text(blog_title), clean_text(blog_text)]
        write_csv(filename, values)
        return redirect(url_for('blogs'))
    return render_template('create_blog.html')


@app.route('/blog/update/<string:id>/', methods=['GET', 'POST'])
@login_required
def blog_update(id):
    # Получаем текущую статью блога по ID
    blog = read_blog(id)
    if blog is None:
        flash('Статья не найдена!')
        return redirect(url_for('blogs'))

    # Проверяем, является ли текущий пользователь автором статьи
    if 'user_id' in blog and blog['user_id'] != str(session['id']):
        flash('У вас нет прав для редактирования этой статьи.')
        return redirect(url_for('blogs'))

    if request.method == 'POST':
        # Получаем данные из формы
        blog_title = request.form['title']
        blog_text = request.form['text']
        blog_img = blog['blog_img']

        if 'file' in request.files and request.files['file'].filename != '':
            file_img = request.files['file']
            if allowed_file(file_img.filename):
                filename_img = secure_filename(file_img.filename)
                file_img.save(os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    filename_img
                ))
                blog_img = filename_img  # Обновляем изображение

        # Обновляем данные статьи
        updated_values = {'id': id,
                          'user_id': blog['user_id'],
                          'data_creation': blog['data_creation'],
                          'blog_img': blog_img,
                          'blog_title': clean_text(blog_title),
                          'blog_text': clean_text(blog_text)
                          }
        update_blog(DATABASBLOGS, updated_values)

        flash('Статья успешно обновлена!')
        return redirect(url_for('blog', id=id))

    return render_template('create_blog.html', blog=blog)


@app.route("/blogs/", methods=['GET', 'POST'])
@login_required
def blogs():
    blogs = read_csv(DATABASBLOGS)
    for blog in blogs:
        if 'user_id' in blog:
            blog['user'] = read_user(blog['user_id'])
    return render_template(
                'blogs.html',
                blogs=blogs
                )


@app.route("/login/mainpage/<string:id>/", methods=['GET', 'POST'])
@login_required
def project(id):
    file_path = DATABASEUSERS
    who_value = get_who_by_id(file_path, session['id'])
    user = read_user(session['id'])
    author_id = find_id_author_by_project_id(id)
    if who_value == "Учитель" or session['id'] == author_id:
        if read_project(id):
            new_points = None
            if request.method == 'POST':
                new_points = int(request.form.get('slider'))
                update_points_in_projects(DATABASEPROJECTS, id, new_points)
                update_points_in_user(author_id, new_points)
                return redirect(url_for('mainpage'))
            return render_template(
                'project_stellar.html',
                project=read_project(id),
                user=user,
                author=get_author_by_project_id(id),
                )
        else:
            return "Error 404"
    else:
        return redirect(url_for("mainpage"))


@app.route('/login/mainpage/account', methods=['GET', 'POST'])
@login_required
def account():
    user = read_user(session['id'])
    evalation = read_evalation()
    data = put_users_data_items(evalation)
    points = count_points(session['id'])
    points_total = int(user['points_remainder'])
    points_remainder = points - points_total
    if user:
        if data != None:
            return render_template(
                'account.html',
                user=user,
                data=data,
                points=points,
                points_remainder=points_remainder,
                points_total=points_total
                )
        else:
            return render_template(
                'account.html',
                user=user
                )
    else:
        return redirect(url_for("mainpage"))


@app.route('/login/mainpage/account/favourite')
@login_required
def favourite():
    return render_template('favourite.html')


@app.route('/login/mainpage/account/creation', methods=['GET', 'POST'])
@login_required
def creation():
    author = None
    project_name = None
    project_text = None
    project_resume = None
    project_img = None
    if request.method == 'POST':
        project_name = request.form['project_name']
        project_text = request.form['project_text']
        project_resume = request.form['project_resume']
        if 'file' not in request.files:
            flash('Нет файла для загрузки')
        else:
            file_img = request.files['file']
            if file_img and allowed_file(file_img.filename):
                filename_img = secure_filename(file_img.filename)
                file_img.save(os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    filename_img
                    ))
                project_img = filename_img
                flash('Файл успешно загружен!')
        filename = DATABASEPROJECTS
        id = count_id(filename)
        points = '0'
        author = session['id']
        values = [
            id,
            points,
            clean_text(project_name),
            clean_text(project_resume),
            clean_text(project_text),
            author,
            project_img
            ]
        write_csv(filename, values)
        return redirect(url_for("account"))
    return render_template('creation.html')


@app.route('/login/logout')
def logout():
    session.pop('email', None)
    session.pop('id', None)
    return redirect(url_for('home'))


def count_price(selected_options: list) -> int:
    total_price = 0
    for option_id in selected_options:
        option = read_item(option_id)
        if 'point' in option:
            total_price += int(option['point'])
    return total_price


@login_required
@app.route('/evaluation/<string:teacher_id>/', methods=['POST', 'GET'])
def use_points(teacher_id):
    user = read_user(session['id'])
    teacher = read_user(teacher_id)
    evalation = read_evalation()  # Возвращает опции для всех учителей
    points = int(user['points_remainder'])
    data = put_users_data_items({teacher_id: evalation[teacher_id]})
    if request.method == 'GET':
        if 'who' in user and user['who'] == "Ученик":
            if teacher_id in evalation:
                return render_template(
                    "evaluation.html",
                    data=data,
                    items=data[0]['value'],
                    points=points,
                    user=user,
                    teacher=teacher
                    )
        else:
            flash("Расходовать баллы могут только ученики!")
    elif request.method == 'POST':
        selected_options = request.form.getlist('selected_items[]')
        price = count_price(selected_options)
        if price > points:
            flash("Недостаточно баллов.")
            return render_template(
                "evaluation.html",
                data=data,
                items=data[0]['value'],
                points=points,
                user=user,
                teacher=teacher
                )
        if not selected_options:
            flash("Вы не выбрали ни одной опции.")
            return render_template(
                "evaluation.html",
                data=data,
                items=data[0]['value'],
                points=points,
                user=user,
                teacher=teacher
                )
        # записать потраченные опции
        id = count_id(DATABASEUSEDITEMS)
        for option_id in selected_options:
            item = read_item(option_id)
            current_date = date.today()
            #id	student_id	teacher_id	item_id	point	date
            used_item = {
                'id': id,
                'student_id': session['id'],
                'teacher_id': teacher_id,
                'item_id': item['id'],
                'point': item['point'],
                'date': current_date,
                }
            write_used_items(used_item)
            id += 1
        # уменьшить баллы у юзера
        update_points_in_user(session['id'], -price)
    return redirect(url_for("account"))


@login_required
@app.route('/login/mainpage/account/evaluation', methods=['POST', 'GET'])
def evaluation():
    user = read_user(session['id'])
    items = read_all_items()
    if request.method == 'POST':
        selected_options = request.form.getlist('selected_items[]')
        if not selected_options:
            flash("Вы не выбрали ни одной опции.")
        id = count_id(DATABASENAMEITEMS)
        with open(DATABASENAMEITEMS, 'a', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=delimiter, lineterminator="\r")
            for option in selected_options:
                if chec_unic_options(session['id'], option):
                    csvwriter.writerow([id, session['id'], option])
                    id += 1
        return redirect(url_for('account'))
    return render_template('evaluation.html', items=items, user=user)


@login_required
@app.route('/login/mainpage/account/my_projects', methods=['POST', 'GET'])
def my_projects():
    my_projects = []
    with open(DATABASEPROJECTS, mode='r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file, delimiter=delimiter, lineterminator="\r")
        for project in csv_reader:
            if project['author'] == session['id']:
                my_projects.append(project)
    return render_template(
        'projects_stellar.html',
        users_projects=my_projects
        )


@login_required
@app.route('/login/mainpage/account/statistic/<string:user_id>', methods=['POST', 'GET'])
def statistic_student(user_id):
    user = read_user(session['id'])
    used_items = count_used_points(user_id)
    return render_template("statistics.html", used_items=used_items, user=user)


if __name__ == '__main__':
    app.run()

from flask import Flask, render_template, request, redirect, session, send_file, send_from_directory
from flask_session.__init__ import Session
from flask_socketio import SocketIO, join_room, leave_room
from werkzeug.utils import secure_filename
from validate_email import validate_email
import imghdr
import json
import datetime
import random
import os
import time

import panthertunes_query

app = Flask(__name__)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
app.config['UPLOAD_PATH'] = 'static/uploads'
#app.config['SECRET'] = 'secret'
#app.config['SESSION_TYPE'] = 'filesystem'

Session(app)
socketio = SocketIO(app)
#socketio = SocketIO(app, manage_session=False)

Posts = []
Projects = []
color = ['red']

def jsonize_user(row):
  user = {
    'user_id': row[0],
    'username': row[1],
    'pw': row[2],
    'joined': row[3],
    'last_accessed': row[4],
    'num_accessed': row[5],
    'email': row[6],
    'posts': row[7],
    'projects': row[8],
    'comments_liked': row[9],
    'posts_liked': row[10],
    'bio': row[11],
    'saved': row[12],
    'instagram': row[13],
    'tiktok': row[14],
    'spotify': row[15],
    'apple_music': row[16]
  }
  return user

def jsonize_post(row):
  post = {
    'post_id': row[0],
    'project_id': row[1],
    'username': row[2],
    'timestamp': datetime_parser(row[3]),
    'title': row[4],
    'post': reformat_paragraph(row[5]),
    'music_genre': row[6],
    'help_needed': row[7],
    'img': row[8],
    'audio': row[9],
    'video': row[10],
    'likes': row[11],
    'comments': row[12]}
  return post

def jsonize_project(row):
  project = {
    'project_id': row[0],
    'usernames': row[1].split(' '),
    'title': row[2],
    'desc': row[3],
    'post_ids': row[4],
    'chat_id': row[5],
    'requested': row[6],
    'active': row[7]}
  if 'name' in session and session['name']:
    user_id = panthertunes_query.get_user_id(session['name'])
    unread_chats = panthertunes_query.get_unread_chats_from_project(row[0], user_id)
    project['unread'] = unread_chats
  return project

def jsonize_notification(row):
  notification = {
    'notification_id': row[0],
    'type': row[1],
    'source': row[2],
    'message': row[3],
    'link': row[4],
    'timestamp': row[5],
    'unread': row[6]}
  return notification

def jsonize_comment(row):
  comment = {
    'comment_id': row[0],
    'username': row[1],
    'comment': reformat_paragraph(row[2]),
    'reply_id': row[3],
    'timestamp': datetime_parser(row[4]),
    'likes': row[5],
    'position': row[6]}
  return comment

def jsonize_application(row):
  application = {
    'application_id': row[0],
    'project_id': row[1],
    'username': row[2],
    'pitch': reformat_paragraph(row[3]),
    'timestamp': datetime_parser(row[4])}
  return application

def jsonize_chat(row):
  chat = {
    'username': row[0],
    'msg': row[1],
    'timestamp': datetime_parser(row[2])}
  return chat

def jsonize_update(row):
  update = {
    'username': row[0],
    'msg': row[1],
    'timestamp': datetime_parser(row[2])}
  return update

def datetime_parser(now):
  split1 = now.split(' ')
  split1_1 = split1[0].split('-')
  split1_2 = split1[1].split(':')
  month = int(split1_1[1])
  month_str = ''
  if month == 1:
    month_str = 'Jan'
  elif month == 2:
    month_str = 'Feb'
  elif month == 3:
    month_str = 'Mar'
  elif month == 4:
    month_str = 'Apr'
  elif month == 5:
    month_str = 'May'
  elif month == 6:
    month_str = 'Jun'
  elif month == 7:
    month_str = 'Jul'
  elif month == 8:
    month_str = 'Aug'
  elif month == 9:
    month_str = 'Sep'
  elif month == 10:
    month_str = 'Oct'
  elif month == 11:
    month_str = 'Nov'
  elif month == 12:
    month_str = 'Dec'
  return [month_str, split1_1[2], split1_1[0], split1_2[0], split1_2[1], split1_2[2]]

def reformat_paragraph(para):
  lines = para.split('\n')
  newline_counter = 0
  index = 0
  for _ in range(0, len(lines)):
    if lines[index] == '' or lines[index] == '\r':
      newline_counter += 1
      lines[index] = ''
    else:
      newline_counter = 0
    if newline_counter > 2:
      del lines[index]
      index -= 1
    index += 1
  while len(lines) > 0 and (lines[len(lines) - 1] == '' or lines[len(lines) - 1] == '\\r'):
    del lines[len(lines) - 1]
  return lines

def validate_image(stream):
  header = stream.read(512)
  stream.seek(0) 
  format = imghdr.what(None, header)
  if not format:
      return None
  return '.' + (format if format != 'jpeg' else 'jpg')

def update():
  if 'name' in session and session['name'] and session['name'] != '':
    session['unread'] = panthertunes_query.get_unread_number(panthertunes_query.get_user_id(session['name']))

@app.route("/", methods=['GET','POST'])
@app.route("/")
def home():
  update()
  if request.method == 'GET':
    Posts.clear()
    records = panthertunes_query.get_all_posts()
    for row in records:
      Posts.insert(0, jsonize_post(row))
    user_projects = []
    user = []
    if 'name' in session and session['name'] and session['name'] != '':
      user_id = panthertunes_query.get_user_id(session['name'])
      project_records = panthertunes_query.get_all_projects(user_id)
      for row in project_records:
        user_projects.insert(0, jsonize_project(row))
      user = jsonize_user(panthertunes_query.get_user(user_id))
    return render_template("home.html", len=len(Posts), Posts=Posts, len_projects = len(user_projects), Projects=user_projects, user=user)
  if request.method == 'POST':
    try:
      data = json.loads(request.data)
      if not session or 'name' not in session or session['name'] == '':
        return json.dumps({'state':'redirect'})
      user_id = panthertunes_query.get_user_id(session['name'])
      result = ''
      if data['action'] == 'like':
        result = panthertunes_query.like_post(user_id, data['post_id'], 1)
      elif data['action'] == 'unlike':
        result = panthertunes_query.like_post(user_id, data['post_id'], -1)
      elif data['action'] == 'save':
        result = panthertunes_query.save_post(user_id, data['post_id'], 1)
      elif data['action'] == 'unsave':
        result = panthertunes_query.save_post(user_id, data['post_id'], -1)
      if result == 'done':
        return json.dumps({'state':'success'})
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})

@app.route("/search/<query>")
def home_searchquery(query):
  update()
  Posts.clear()
  records = panthertunes_query.get_posts_from_query(query)
  for row in records:
    Posts.insert(0, jsonize_post(row))
  user_projects = []
  user = []
  if 'name' in session and session['name'] and session['name'] != '':
    user_id = panthertunes_query.get_user_id(session['name'])
    project_records = panthertunes_query.get_all_projects(user_id)
    for row in project_records:
      user_projects.insert(0, jsonize_project(row))
    user = jsonize_user(panthertunes_query.get_user(user_id))
  return render_template("home.html", len=len(Posts), Posts=Posts, len_projects = len(user_projects), Projects=user_projects, query=query, user=user)

@app.route("/search/<genres>/<helplist>")
def home_search(genres, helplist):
  update()
  Posts.clear()
  genres_queuer = []
  helplist_queuer = []
  if genres != 'default':
    genres_queuer = genres.split('%')
  if helplist != 'default':
    helplist_queuer = helplist.split('%')
  records = panthertunes_query.get_posts(genres_queuer, helplist_queuer)
  for row in records:
    Posts.insert(0, jsonize_post(row))
  user_projects = []
  user = []
  if 'name' in session and session['name'] and session['name'] != '':
    user_id = panthertunes_query.get_user_id(session['name'])
    project_records = panthertunes_query.get_all_projects(user_id)
    for row in project_records:
      user_projects.insert(0, jsonize_project(row))
    user = jsonize_user(panthertunes_query.get_user(user_id))
  for i in range(0, len(genres_queuer)):
    genres_queuer[i] = '#' + genres_queuer[i]
  genres_queuer = ', '.join(genres_queuer)
  for i in range(0, len(helplist_queuer)):
    helplist_queuer[i] = '#' + helplist_queuer[i]
  helplist_queuer = ', '.join(helplist_queuer)
  return render_template("home.html", len=len(Posts), Posts=Posts, len_projects = len(user_projects), Projects=user_projects, genres_queuer=genres_queuer, helplist_queuer=helplist_queuer, user=user)

@app.route("/about")
def about():
  update()
  return render_template("about.html")

@app.route("/contact")
def contact():
  update()
  return render_template("contact.html")

@app.route("/profile", methods=['GET','POST'])
@app.route("/profile")
def profile():
  update()
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    user_id = panthertunes_query.get_user_id(session['name'])
    records = panthertunes_query.get_all_posts(user_id)
    user_posts = []
    total_likes = 0
    for row in records:
      post = jsonize_post(row)
      user_posts.insert(0, post)
      total_likes += post['likes']
    records = panthertunes_query.get_saved(user_id)
    user_saved = []
    for row in records:
      post = jsonize_post(row)
      user_saved.insert(0, post)
    notifications = []
    records = panthertunes_query.get_notifications_from_user(user_id)
    for row in records:
      notifications.insert(0, jsonize_notification(row))
    panthertunes_query.read_all_notifications(user_id)
    row = panthertunes_query.get_user(user_id)
    user = jsonize_user(row)
    return render_template("profile.html", len=len(user_posts), user_posts=user_posts, user_saved=user_saved, notifications=notifications, total_likes=total_likes, sort='newest', user=user)
  if request.method == 'POST':
    try:
      data = json.loads(request.data)
      user_id = panthertunes_query.get_user_id(session['name'])
      result = ''
      if data['action'] == 'edit-bio':
        result = panthertunes_query.update_bio_from_user(user_id, data['bio'])
      elif data['action'] == 'update-social':
        result = panthertunes_query.update_social_from_user(user_id, data['social'], data['handle'])
      if result == 'done':
        return json.dumps({'state':'success', 'id':data['social']})
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})

@app.route("/profile-notifications", methods=['GET','POST'])
@app.route("/profile-notifications")
def profile_notifications():
  update()
  if not session['name']:
    return redirect('/sign-in')
  user_id = panthertunes_query.get_user_id(session['name'])
  notifications = []
  records = panthertunes_query.get_notifications_from_user(user_id)
  for row in records:
    notifications.insert(0, jsonize_notification(row))
  panthertunes_query.read_all_notifications(user_id)
  row = panthertunes_query.get_user(user_id)
  user = jsonize_user(row)
  bio = user['bio']
  return render_template("profile-notifications.html", notifications=notifications, bio=bio, user=user)

@app.route("/profile-posts", methods=['GET','POST'])
@app.route("/profile-posts")
def profile_posts():
  update()
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    user_id = panthertunes_query.get_user_id(session['name'])
    records = panthertunes_query.get_all_posts(user_id)
    user_posts = []
    total_likes = 0
    for row in records:
      post = jsonize_post(row)
      user_posts.insert(0, post)
      total_likes += post['likes']
    records = panthertunes_query.get_saved(user_id)
    row = panthertunes_query.get_user(user_id)
    user = jsonize_user(row)
    return render_template("profile-posts.html", len=len(user_posts), user_posts=user_posts, total_likes=total_likes, sort='newest', user=user)
  if request.method == 'POST':
    try:
      data = json.loads(request.data)
      user_id = panthertunes_query.get_user_id(session['name'])
      result = ''
      if data['action'] == 'like':
        result = panthertunes_query.like_post(user_id, data['post_id'], 1)
      elif data['action'] == 'unlike':
        result = panthertunes_query.like_post(user_id, data['post_id'], -1)
      elif data['action'] == 'save':
        result = panthertunes_query.save_post(user_id, data['post_id'], 1)
      elif data['action'] == 'unsave':
        result = panthertunes_query.save_post(user_id, data['post_id'], -1)
      elif data['action'] == 'delete':
        result = panthertunes_query.delete_post(data['post_id'])
      elif data['action'] == 'post-sort':
        records = panthertunes_query.get_all_posts(user_id, data['sort'])
        return str(records)
      if result == 'done':
        return json.dumps({'state':'success'})
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})

@app.route("/profile-posts/sort/<sort>", methods=['GET','POST'])
@app.route("/profile-posts/sort/<sort>")
def profile_posts_sort(sort):
  update()
  print(sort)
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    user_id = panthertunes_query.get_user_id(session['name'])
    records = panthertunes_query.get_all_posts(user_id, sort)
    user_posts = []
    total_likes = 0
    for row in records:
      post = jsonize_post(row)
      user_posts.insert(0, post)
      total_likes += post['likes']
    notifications = []
    records = panthertunes_query.get_notifications_from_user(user_id)
    for row in records:
      notifications.insert(0, jsonize_notification(row))
    panthertunes_query.read_all_notifications(user_id)
    row = panthertunes_query.get_user(user_id)
    user = jsonize_user(row)
    bio = user['bio']
    return render_template("profile-posts.html", len=len(user_posts), user_posts=user_posts, notifications=notifications, total_likes=total_likes, bio=bio, sort=sort, user=user)
  if request.method == 'POST':
    try:
      data = json.loads(request.data)
      user_id = panthertunes_query.get_user_id(session['name'])
      result = ''
      if data['action'] == 'like':
        result = panthertunes_query.like_post(user_id, data['post_id'], 1)
      elif data['action'] == 'unlike':
        result = panthertunes_query.like_post(user_id, data['post_id'], -1)
      elif data['action'] == 'delete':
        result = panthertunes_query.delete_post(data['post_id'])
      elif data['action'] == 'edit-bio':
        result = panthertunes_query.update_bio_from_user(user_id, data['bio'])
      elif data['action'] == 'post-sort':
        records = panthertunes_query.get_all_posts(user_id, data['sort'])
        return str(records)
      if result == 'done':
        return json.dumps({'state':'success'})
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})

@app.route("/profile-saved", methods=['GET','POST'])
@app.route("/profile-saved")
def profile_saved():
  update()
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    user_id = panthertunes_query.get_user_id(session['name'])
    records = panthertunes_query.get_saved(user_id)
    user_saved = []
    for row in records:
      post = jsonize_post(row)
      user_saved.insert(0, post)
    row = panthertunes_query.get_user(user_id)
    user = jsonize_user(row)
    return render_template("profile-saved.html", user_saved=user_saved, user=user)
  if request.method == 'POST':
    try:
      data = json.loads(request.data)
      user_id = panthertunes_query.get_user_id(session['name'])
      result = ''
      if data['action'] == 'like':
        result = panthertunes_query.like_post(user_id, data['post_id'], 1)
      elif data['action'] == 'unlike':
        result = panthertunes_query.like_post(user_id, data['post_id'], -1)
      elif data['action'] == 'save':
        result = panthertunes_query.save_post(user_id, data['post_id'], 1)
      elif data['action'] == 'unsave':
        result = panthertunes_query.save_post(user_id, data['post_id'], -1)
      if result == 'done':
        return json.dumps({'state':'success'})
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})

@app.route("/profile/<username>", methods=['GET','POST'])
@app.route("/profile/<username>")
def profile_outside(username):
  update()
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    elif session['name'] == username:
      return redirect('/profile')
    user_id = panthertunes_query.get_user_id(username)
    records = panthertunes_query.get_all_posts(user_id)
    user_posts = []
    total_likes = 0
    for row in records:
      post = jsonize_post(row)
      user_posts.insert(0, post)
      total_likes += post['likes']
    row = panthertunes_query.get_user(user_id)
    user = jsonize_user(row)
    bio = user['bio']
    return render_template("profile-outside.html", len=len(user_posts), user_posts=user_posts, total_likes=total_likes, username=username, bio=bio, sort='newest')

@app.route("/profile/<username>/sort/<sort>", methods=['GET','POST'])
@app.route("/profile/<username>/sort/<sort>")
def profile_outside_sort(username, sort):
  update()
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    elif session['name'] == username:
      return redirect('/profile')
    user_id = panthertunes_query.get_user_id(username)
    records = panthertunes_query.get_all_posts(user_id, sort)
    user_posts = []
    total_likes = 0
    for row in records:
      post = jsonize_post(row)
      user_posts.insert(0, post)
      total_likes += post['likes']
    row = panthertunes_query.get_user(user_id)
    user = jsonize_user(row)
    bio = user['bio']
    return render_template("profile-outside.html", len=len(user_posts), user_posts=user_posts, total_likes=total_likes, username=username, bio=bio, sort=sort)

@app.route("/create-post", methods=['GET','POST'])
def create_post():
  update()
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    user_projects = []
    if 'name' in session and session['name'] and session['name'] != '':
      user_id = panthertunes_query.get_user_id(session['name'])
      project_records = panthertunes_query.get_all_projects(user_id)
      for row in project_records:
        user_projects.insert(0, jsonize_project(row))
    return render_template("create-post.html", Projects=user_projects)
  if request.method == 'POST':
    try:
      #data = json.loads(request.data)
      now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      post_id = random.randint(1000000, 9999999)      
      user_id = panthertunes_query.get_user_id(session['name'])
      panthertunes_query.update_posts_from_user(user_id, post_id)
      if request.form.get('project') == 'create-new':
        project_id = random.randint(1000000, 9999999)
        panthertunes_query.add_project(project_id, session['name'], request.form.get('project-title'), request.form.get('project-desc'), post_id, random.randint(1000000, 9999999))
        panthertunes_query.update_projects_from_user(user_id, project_id)
      elif request.form.get('project') != 'no-collab':
        project_id = int(request.form.get('project'))
        panthertunes_query.update_posts_from_project(project_id, post_id)
      else:
        project_id = 0
      image_file = request.files['image']
      audio_file = request.files['audio']
      video_file = request.files['video']
      img = 0
      audio = 0
      video = 0
      if image_file.filename != '':
        img = 1
        image_file.save(os.path.join(app.config['UPLOAD_PATH'], 'img' + str(post_id) + '.jpg'))
      if audio_file.filename != '':
        audio = 1
        audio_file.save(os.path.join(app.config['UPLOAD_PATH'], 'audio' + str(post_id) + '.mp3'))
      if video_file.filename != '':
        video = 1
        video_file.save(os.path.join(app.config['UPLOAD_PATH'], 'video' + str(post_id) + '.mp4'))
      result = panthertunes_query.add_post(post_id, project_id, session['name'], now, request.form.get('title'), request.form.get('desc'), request.form.get('genre'), request.form.get('help-needed'), img, audio, video)
      os.mkdir(app.config['UPLOAD_PATH'] + '/Proj' + str(project_id))
      if result == 'done':
        return redirect('/post/' + str(post_id))
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except Exception as e:
      print(e)
      return json.dumps({'state':'Internal server error - 1'})

@app.route("/uploads/<filename>")
def upload(filename):
  return send_from_directory(app.config['UPLOAD_PATH'], filename)

@app.route("/uploadproj/<int:project_id>/<filename>")
def upload_proj(project_id, filename):
  return send_from_directory(app.config['UPLOAD_PATH'] + '/Proj' + str(project_id), filename)

@app.route("/deleteuploadedproj/<int:project_id>/<filename>")
def delete_uploaded_proj(project_id, filename):
  try:
    os.remove(app.config['UPLOAD_PATH'] + '/Proj' + str(project_id) + '/' + filename)
  except:
    print('deletion error')
  return redirect('/project/' + str(project_id))

@app.route("/apply/<int:post_id>", methods=['GET','POST'])
def apply(post_id):
  update()
  if request.method == 'GET':
    post_row = panthertunes_query.get_post(post_id)
    row = panthertunes_query.get_project(post_row[1])
    if (row == '404'):
      return redirect('/404')
    project = jsonize_project(row)
    return render_template("apply.html", project=project, post_id=post_id)
  if request.method == 'POST':
    try:
      data = json.loads(request.data)
      now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      application_id = random.randint(1000000, 9999999)
      result = panthertunes_query.add_application(application_id, panthertunes_query.get_post(post_id)[1], session['name'], data['pitch'], now)
      if result == 'done':
        return json.dumps({'state':'success'})
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})

@app.route("/contest/<int:project_id>", methods=['GET','POST'])
def contest(project_id):
  update()
  if request.method == 'GET':
    row = panthertunes_query.get_project(project_id)
    if row == '404':
      row = panthertunes_query.get_deleted_project(project_id)
    if row == '404':
      return redirect('/404-contest')
    project = jsonize_project(row)
    return render_template("contest.html", project=project)
  if request.method == 'POST':
    try:
      data = json.loads(request.data)
      now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      contest_id = random.randint(1000000, 9999999)
      result = panthertunes_query.add_contest(contest_id, panthertunes_query.get_user_id(session['name']), project_id, data['desc'], now)
      if result == 'done':
        return json.dumps({'state':'success'})
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})

@app.route("/sign-in", methods=['GET','POST'])
def sign_in():
  update()
  if request.method == 'GET':
    return render_template("sign-in.html")
  if request.method == 'POST':
      #search for user and passwd in database
      try:
        data = json.loads(request.data)
        return_data = {"user_token": "0",
          'username':'na',
          "error_code": "1",
          'log':'0'}
        valid_user = panthertunes_query.check_valid_username(data['username'])
        return_data['log'] = '1'

        if (valid_user):
          authenticated = panthertunes_query.check_for_password(data['username'], data['password'])
          return_data['log'] = '2'

          if (authenticated):
            return_data['log'] = '3'
            #create token for our newly authenticated user id
            user_id = panthertunes_query.get_user_id(data['username'])
            return_data['log'] = '4'
           
            rand_token = panthertunes_query.create_token_and_table(user_id)
            return_data['log'] = '5'
            return_data['user_token'] = rand_token
            return_data['username'] = panthertunes_query.get_username(user_id)
            return_data['log'] = '6'
            #update last_accessed date to now
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            panthertunes_query.update_last_accessed_date(now, user_id)
            return_data['log'] = '7'
            panthertunes_query.update_num_accessed(user_id)
            return_data['log'] = '8'
            return_data['error_code'] = '0'
            session['name'] = data['username']

      except:
        #check email?
        return_data['error_code'] = '2'

      return json.dumps(return_data)

@app.route("/sign-up", methods=['GET','POST'])
def sign_up():
  update()
  if request.method == 'GET':
    return render_template("sign-up.html")
  if request.method == 'POST':#create an account
    try:
        data = json.loads(request.data)
        #if data['username'] != '' and data['password'] != '' and data['email'] != '':#if the user has inputted everything
        result = panthertunes_query.add_user(data['username'],data['password'],data['email'])
        if result == 'done':#if we added the user succesfully sign the user in
            user_id = panthertunes_query.get_user_id(data['username'])
            rand_token = panthertunes_query.create_token_and_table(user_id)
            session['name'] = data['username']
            return json.dumps({'state':result,'token':rand_token,'username':data['username']})
        else:
            return json.dumps({'state':result})
        #else:
        #    return json.dumps({'state':'Server error - invalid input'})
    except:
        return json.dumps({'state':'Internal server error'})
  return 'no'

@app.route('/sign-in/sign-out',methods=['GET','POST'])
def signout():
    if request.method == 'GET':
        return redirect('/')
    if request.method == 'POST':
        data = json.loads(request.data)
        try:
            hashed_token = panthertunes_query.hash_hex(data['user_token'])
            panthertunes_query.delete_by_token(hashed_token)
            return json.dumps({'state':'done'})
        except:#even if it fails we still return done because it is most likely the reason we failed
            return json.dumps({'state':'done'})#to sign out is because the token has already been deleted

@app.route("/logout")
def logout():
  signout()
  session['name'] = ''
  return redirect('/')

@app.route("/post/<int:post_id>", methods=['GET','POST'])
@app.route("/post/<int:post_id>")
def post(post_id):
  update()
  if request.method == 'GET':
    post = panthertunes_query.get_post(post_id)
    if post == '404':
      return redirect('/404')
    original_post = jsonize_post(post)
    linked_project = {}
    can_apply = False
    if original_post['project_id'] != 0:
      row = panthertunes_query.get_project(original_post['project_id'])
      if row != '404':
        linked_project = jsonize_project(row)
      else:
        original_post['project_id'] = 0
      if 'name' in session and session['name']:
        can_apply = not panthertunes_query.application_exists(original_post['project_id'], session['name'])
    #panthertunes_query.add_table('forums', post_id)
    post_comments = []
    records = panthertunes_query.get_all_comments(post_id)
    records.reverse()
    for row in records:
      post_comments.insert(0, jsonize_comment(row))
    comments_liked = ''
    posts_liked = ''
    if 'name' in session and session['name']:
      user_id = panthertunes_query.get_user_id(session['name'])
      all_liked = panthertunes_query.get_all_liked(user_id)
      comments_liked = all_liked['comments']
      posts_liked = all_liked['posts']
    user_projects = []
    if 'name' in session and session['name'] and session['name'] != '':
      user_id = panthertunes_query.get_user_id(session['name'])
      project_records = panthertunes_query.get_all_projects(user_id)
      for row in project_records:
        user_projects.insert(0, jsonize_project(row))
    img_file = 'img' + str(post_id) + '.jpg'
    audio_file = 'audio' + str(post_id) + '.mp3'
    video_file = 'video' + str(post_id) + '.mp4'
    return render_template("post.html", len=len(post_comments), len_projects=len(user_projects), original_post=original_post, post_comments=post_comments, Projects=user_projects, comments_liked=comments_liked, posts_liked=posts_liked, linked_project=linked_project, can_apply=can_apply, img_file=img_file, audio_file=audio_file, video_file=video_file)
  if request.method == 'POST':
    try:
      data = json.loads(request.data)
      user_id = panthertunes_query.get_user_id(session['name'])
      result = ''
      if data['action'] == 'delete_post':
        post_id = data['post_id']
        result = panthertunes_query.delete_post(post_id)
      elif data['action'] == 'comment':
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = panthertunes_query.add_comment(random.randint(1000000, 9999999), session['name'], data['comment'], post_id, data['reply_id'], now)
      elif data['action'] == 'like':
        result = panthertunes_query.like_comment(user_id, post_id, data['comment_id'], 1)
      elif data['action'] == 'unlike':
        result = panthertunes_query.like_comment(user_id, post_id, data['comment_id'], -1)
      elif data['action'] == 'like-post':
        result = panthertunes_query.like_post(user_id, post_id, 1)
      elif data['action'] == 'unlike-post':
        result = panthertunes_query.like_post(user_id, post_id, -1)
      if result == 'done':
        return json.dumps({'state':'success'})
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})

@app.route("/project/<int:project_id>", methods=['GET','POST'])
@app.route("/project/<int:project_id>")
def project(project_id):
  update()
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    row = panthertunes_query.get_project(project_id)
    if row == '404':
      return redirect('/404')
    project = jsonize_project(row)
    if session['name'] not in project['usernames']:
      return redirect('/404')
    records = panthertunes_query.get_updates_from_project(project_id)
    updates = []
    for row in records:
      updates.insert(0, jsonize_update(row))
    files = os.listdir(app.config['UPLOAD_PATH'] + '/Proj' + str(project_id))
    return render_template("project.html", project=project, updates=updates, files=files)
  if request.method == 'POST':
    try:
      result = ''
      if request.data:
        data = json.loads(request.data)
        if data['action'] == 'update':
          now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          result = panthertunes_query.add_update_to_project(project_id, session['name'], data['update'], now)
      else:
        print(request.files['file'])
        file = request.files['file']
        file.save(os.path.join(app.config['UPLOAD_PATH'] + '/Proj' + str(project_id), file.filename))
        result = 'done-redirect'
      if result == 'done':
        return json.dumps({'state':'success'})
      elif result == 'done-redirect':
        return redirect('/project/' + str(project_id))
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})

@app.route("/project/applications/<int:project_id>", methods=['GET','POST'])
@app.route("/project/applications/<int:project_id>")
def project_application(project_id):
  update()
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    row = panthertunes_query.get_project(project_id)
    if row == '404':
      return redirect('/404')
    project = jsonize_project(row)
    if session['name'] not in project['usernames']:
      return redirect('/404')
    applications = []
    records = panthertunes_query.get_applications_from_project(project_id)
    for row in records:
      applications.insert(0, jsonize_application(row))
    return render_template("project-application.html", project_id=project_id, project=project, applications=applications)
  if request.method == 'POST':
    try:
      data = json.loads(request.data)
      if data['action'] == 'accept':
        result = panthertunes_query.decide_application(int(data['application_id']), True)
      elif data['action'] == 'deny':
        result = panthertunes_query.decide_application(int(data['application_id']), False)
      if result == 'done':
        return json.dumps({'state':'success'})
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})

@app.route("/project/chat/<int:project_id>", methods=['GET','POST'])
@app.route("/project/chat/<int:project_id>")
def project_chat(project_id):
  update()
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    row = panthertunes_query.get_project(project_id)
    if row == '404':
      return redirect('/404')
    project = jsonize_project(row)
    if session['name'] not in project['usernames']:
      return redirect('/404')
    records = panthertunes_query.get_chats_from_project(project_id)
    all_chats = []
    for row in records:
      all_chats.append(jsonize_chat(row))
    user_id = panthertunes_query.get_user_id(session['name'])
    panthertunes_query.read_all_chats(project_id, user_id)
    return render_template("project-chat.html", project=project, all_chats=all_chats)
  if request.method == 'POST':
    try:
      data = json.loads(request.data)
      post_id = data['post_id']
      result = panthertunes_query.delete_post(post_id)
      if result == 'done':
        return json.dumps({'state':'success'})
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})

@app.route("/project/posts/<int:project_id>", methods=['GET','POST'])
@app.route("/project/posts/<int:project_id>")
def project_posts(project_id):
  update()
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    row = panthertunes_query.get_project(project_id)
    if row == '404':
      return redirect('/404')
    project = jsonize_project(row)
    if session['name'] not in project['usernames']:
      return redirect('/404')
    records = panthertunes_query.get_posts_from_projects(project_id)
    if records == '404':
      return redirect('/404')
    project_posts = []
    for row in records:
      project_posts.insert(0, jsonize_post(row))
    return render_template("project-posts.html", project=project, len=len(project_posts), project_posts=project_posts, user=jsonize_user(panthertunes_query.get_user(panthertunes_query.get_user_id(session['name']))))
  '''if request.method == 'POST':
    try:
      data = json.loads(request.data)
      post_id = data['post_id']
      result = panthertunes_query.delete_post(post_id)
      if result == 'done':
        return json.dumps({'state':'success'})
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})'''
  if request.method == 'POST':
    try:
      data = json.loads(request.data)
      if not session['name'] or session['name'] == '':
        return redirect('/sign-in')
      user_id = panthertunes_query.get_user_id(session['name'])
      result = ''
      if data['action'] == 'like':
        result = panthertunes_query.like_post(user_id, data['post_id'], 1)
      elif data['action'] == 'unlike':
        result = panthertunes_query.like_post(user_id, data['post_id'], -1)
      elif data['action'] == 'save':
        result = panthertunes_query.save_post(user_id, data['post_id'], 1)
      elif data['action'] == 'unsave':
        result = panthertunes_query.save_post(user_id, data['post_id'], -1)
      if result == 'done':
        return json.dumps({'state':'success'})
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})

@app.route("/project/settings/<int:project_id>", methods=['GET','POST'])
@app.route("/project/settings/<int:project_id>")
def project_settings(project_id):
  update()
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    row = panthertunes_query.get_project(project_id)
    if row == '404':
      return redirect('/404')
    project = jsonize_project(row)
    if session['name'] not in project['usernames']:
      return redirect('/404')
    is_owner = session['name'] == project['usernames'][0]
    return render_template("project-settings.html", project=project, usernames=project['usernames'], is_owner=is_owner)
  if request.method == 'POST':
    try:
      data = json.loads(request.data)
      action = data['action']
      print(action)
      result = ''
      #user_id = panthertunes_query.get_user_id(data['member'])
      if action == 'remove':
        result = panthertunes_query.remove_member(data['member'], project_id)
      elif action == 'upgrade':
        result = panthertunes_query.upgrade_member(data['member'], project_id)
      elif action == 'leave':
        result = panthertunes_query.remove_member(session['name'], project_id, is_self=True)
      elif action == 'request':
        result = panthertunes_query.request_member(data['member'], project_id)
      elif action == 'delete':
        result = panthertunes_query.delete_project(project_id)
      if result == 'done':
        return json.dumps({'state':'success'})
      elif result == 'invalid':
        return json.dumps({'state':'Invalid username'})
      elif result == 'in-project':
        return json.dumps({'state':'Already member of project'})
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})

def messageReceived(methods=['GET', 'POST']):
  print('message was received!!!')

@app.route('/get-activity/<int:project_id>')
def get_activity(project_id):
  row = panthertunes_query.get_project(project_id)
  project = jsonize_project(row)
  if not session['name']:
    return redirect('/sign-in')
  if session['name'] not in project['usernames']:
    return redirect('/404')
  return project['active']

@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
  print('received my event: ' + str(json))
  if 'username' in json:
    print('MSG:', json['username'], json['message'])
    panthertunes_query.add_chat(json['project_id'], json['username'], json['message'])
    socketio.emit('my response', json, callback=messageReceived, room=json['project_id'])

@socketio.on('join')
def join(project_id):
  print('joined ' + str(project_id))
  session['prev-update'] = datetime.datetime.now()
  panthertunes_query.update_activity_from_project(project_id, session['name'], True)
  join_room(project_id)

@socketio.on('leave')
def leave(project_id):
  leave_room(project_id)

@socketio.on('update')
def get_update(project_id):
  now = datetime.datetime.now()
  delta = now - session['prev-update']
  print(delta)
  session['prev-update'] = now
  if (delta.total_seconds() > 10):
    print(session['name'] + ' is no longer active')
    panthertunes_query.update_activity_from_project(project_id, session['name'], False)
    return
  panthertunes_query.update_activity_from_project(project_id, session['name'], True)
  time.sleep(20)
  now = datetime.datetime.now()
  delta = now - session['prev-update']
  if (delta.total_seconds() > 10):
    print(session['name'] + ' is no longer active')
    panthertunes_query.update_activity_from_project(project_id, session['name'], False)
    return

@app.route("/acceptproject/<int:project_id>")
def accept_project(project_id):
  result = panthertunes_query.accept_project(session['name'], project_id)
  if result == 'done':
    return redirect('/project/' + str(project_id))
  else:
    return redirect('/404')

@app.route("/404")
def error():
  update()
  return render_template("404.html")

@app.route("/404-contest")
def error_contest():
  update()
  return render_template("404-contest.html")

@app.errorhandler(404)
def nonexistent_url(error):
  update()
  #print(error)
  return render_template("404.html")

if __name__ == "__main__":
  socketio.run(app, port=1601, debug=True)
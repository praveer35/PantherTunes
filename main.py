from flask import Flask, render_template, request, redirect, session
from flask_session.__init__ import Session
import json
import datetime
import random

import panthertunes_query

app = Flask(__name__)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
#app.config['SECRET'] = 'secret'
#app.config['SESSION_TYPE'] = 'filesystem'

Session(app)
#socketio = SocketIO(app, manage_session=False)

Posts = []
Projects = []

def reformat_paragraph(para):
  lines = para.split('\n')
  newline_counter = 0
  index = 0
  for _ in range(0, len(lines)):
    if lines[index] == '':
      newline_counter += 1
    else:
      newline_counter = 0
    if newline_counter > 2:
      del lines[index]
      index -= 1
    index += 1
  while len(lines) > 0 and lines[len(lines) - 1] == '':
    del lines[len(lines) - 1]
  return lines

@app.route("/")
def home():
  Posts.clear()
  records = panthertunes_query.get_all_posts()
  for row in records:
    Posts.insert(0, {
      'post_id': row[0],
      'project_id': row[1],
      'username': row[2],
      'timestamp': row[3],
      'title': row[4],
      'post': reformat_paragraph(row[5]),
      'music_genre': row[6],
      'help_needed': row[7],
      'likes': row[8]})
  if session['name'] and session['name'] != '':
    Projects.clear()
    user_id = panthertunes_query.get_user_id(session['name'])
    project_records = panthertunes_query.get_all_projects(user_id)
    for row in project_records:
      Projects.insert(0, {
        'project_id': row[0],
        'usernames': row[1],
        'title': row[2],
        'desc': row[3],
        'post_ids': row[4],
        'chat_id': row[5]})
  return render_template("home.html", len=len(Posts), Posts=Posts, len_projects = len(Projects), Projects=Projects)

@app.route("/search/<query>")
def home_searchquery(query):
  Posts.clear()
  records = panthertunes_query.get_posts_from_query(query)
  for row in records:
    Posts.insert(0, {
      'post_id': row[0],
      'project_id': row[1],
      'username': row[2],
      'timestamp': row[3],
      'title': row[4],
      'post': reformat_paragraph(row[5]),
      'music_genre': row[6],
      'help_needed': row[7],
      'likes': row[8]})
  if session['name'] and session['name'] != '':
    Projects.clear()
    user_id = panthertunes_query.get_user_id(session['name'])
    project_records = panthertunes_query.get_all_projects(user_id)
    for row in project_records:
      Projects.insert(0, {
        'project_id': row[0],
        'usernames': row[1],
        'title': row[2],
        'desc': row[3],
        'post_ids': row[4],
        'chat_id': row[5]})
  return render_template("home.html", len=len(Posts), Posts=Posts, len_projects = len(Projects), Projects=Projects)

@app.route("/search/<genres>/<helplist>")
def home_search(genres, helplist):
  Posts.clear()
  genres_queuer = []
  helplist_queuer = []
  if genres != 'default':
    genres_queuer = genres.split('%')
  if helplist != 'default':
    helplist_queuer = helplist.split('%')
  records = panthertunes_query.get_posts(genres_queuer, helplist_queuer)
  for row in records:
    Posts.insert(0, {
      'post_id': row[0],
      'project_id': row[1],
      'username': row[2],
      'timestamp': row[3],
      'title': row[4],
      'post': reformat_paragraph(row[5]),
      'music_genre': row[6],
      'help_needed': row[7],
      'likes': row[8]})
  if session['name'] and session['name'] != '':
    Projects.clear()
    user_id = panthertunes_query.get_user_id(session['name'])
    project_records = panthertunes_query.get_all_projects(user_id)
    for row in project_records:
      Projects.insert(0, {
        'project_id': row[0],
        'usernames': row[1],
        'title': row[2],
        'desc': row[3],
        'post_ids': row[4],
        'chat_id': row[5]})
  for i in range(0, len(genres_queuer)):
    genres_queuer[i] = '#' + genres_queuer[i]
  genres_queuer = ', '.join(genres_queuer)
  for i in range(0, len(helplist_queuer)):
    helplist_queuer[i] = '#' + helplist_queuer[i]
  helplist_queuer = ', '.join(helplist_queuer)
  return render_template("home.html", len=len(Posts), Posts=Posts, len_projects = len(Projects), Projects=Projects, genres_queuer=genres_queuer, helplist_queuer=helplist_queuer)

@app.route("/about")
def about():
  return render_template("about.html")

@app.route("/contact")
def contact():
  return render_template("contact.html")

@app.route("/profile", methods=['GET','POST'])
@app.route("/profile")
def profile():
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    user_id = panthertunes_query.get_user_id(session['name'])
    records = panthertunes_query.get_all_posts(user_id)
    user_posts = []
    for row in records:
      user_posts.insert(0, {
        'post_id': row[0],
        'project_id': row[1],
        'username': row[2],
        'timestamp': row[3],
        'title': row[4],
        'post': reformat_paragraph(row[5]),
        'music_genre': row[6],
        'help_needed': row[7],
        'likes': row[8]})
    return render_template("profile.html", len=len(user_posts), user_posts=user_posts)
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

@app.route("/create-post", methods=['GET','POST'])
def create_post():
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    return render_template("create-post.html", Projects=Projects)
  if request.method == 'POST':
    try:
      data = json.loads(request.data)
      now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      post_id = random.randint(1000000, 9999999)      
      user_id = panthertunes_query.get_user_id(session['name'])
      panthertunes_query.update_posts_from_user(user_id, post_id)
      if data['project_option'] == 'create-new':
        project_id = random.randint(1000000, 9999999)
        panthertunes_query.add_project(project_id, session['name'], data['project_title'], data['project_desc'], post_id, random.randint(1000000, 9999999))
        panthertunes_query.update_projects_from_user(user_id, project_id)
      elif data['project_option'] != 'no-collab':
        project_id = int(data['project_option'])
        panthertunes_query.update_posts_from_project(project_id, post_id)
      else:
        project_id = 0
      result = panthertunes_query.add_post(post_id, project_id, session['name'], now, data['title'], data['desc'], data['genre'], data['help_needed'])
      if result == 'done':
        return json.dumps({'state':'success'})
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})

@app.route("/apply/<int:post_id>", methods=['GET','POST'])
def apply(post_id):
  if request.method == 'GET':
    post_row = panthertunes_query.get_post(post_id)
    row = panthertunes_query.get_project(post_row[1])
    project = {
        'project_id': row[0],
        'usernames': row[1],
        'title': row[2],
        'desc': row[3],
        'post_ids': row[4],
        'chat_id': row[5]}
    return render_template("apply.html", project=project, post_id=post_id)
  if request.method == 'POST':
    try:
      data = json.loads(request.data)
      now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      application_id = random.randint(1000000, 9999999)
      print('we get here')
      result = panthertunes_query.add_application(application_id, panthertunes_query.get_post(post_id)[1], session['name'], data['pitch'], now)
      if result == 'done':
        return json.dumps({'state':'success'})
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})

@app.route("/sign-in", methods=['GET','POST'])
def sign_in():
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
  if request.method == 'GET':
    post = panthertunes_query.get_post(post_id)
    if post == '404':
      return redirect('/404')
    original_post = {
      'post_id': post[0],
      'project_id': post[1],
      'username': post[2],
      'timestamp': post[3],
      'title': post[4],
      'post': reformat_paragraph(post[5]),
      'music_genre': post[6],
      'help_needed': post[7],
      'likes': post[8]}
    linked_project = {}
    can_apply = False
    if original_post['project_id'] != 0:
      row = panthertunes_query.get_project(original_post['project_id'])
      linked_project = {
        'project_id': row[0],
        'usernames': row[1],
        'title': row[2],
        'desc': row[3],
        'post_ids': row[4],
        'chat_id': row[5]}
      if session['name']:
        can_apply = not panthertunes_query.application_exists(original_post['project_id'], session['name'])
    panthertunes_query.add_table(post_id)
    post_comments = []
    records = panthertunes_query.get_all_comments(post_id)
    records.reverse()
    for row in records:
      post_comments.insert(0, {
        'comment_id': row[0],
        'username': row[1],
        'comment': reformat_paragraph(row[2]),
        'reply_id': row[3],
        'timestamp': row[4],
        'likes': row[5],
        'position': row[6]})
    comments_liked = ''
    if session['name']:
      user_id = panthertunes_query.get_user_id(session['name'])
      comments_liked = panthertunes_query.get_comments_liked(user_id)
    return render_template("post.html", len=len(post_comments), len_projects = len(Projects), original_post=original_post, post_comments=post_comments, Projects=Projects, comments_liked=comments_liked, linked_project=linked_project, can_apply=can_apply)
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
      if result == 'done':
        return json.dumps({'state':'success'})
      else:
        return json.dumps({'state':'Internal server error - 2'})
    except:
      return json.dumps({'state':'Internal server error - 1'})

@app.route("/project/<int:project_id>", methods=['GET','POST'])
@app.route("/project/<int:project_id>")
def project(project_id):
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    row = panthertunes_query.get_project(project_id)
    if row == '404':
      return redirect('/404')
    project = {
      'project_id': row[0],
      'usernames': row[1],
      'title': row[2],
      'desc': row[3],
      'post_ids': row[4],
      'chat_id': row[5]}
    records = panthertunes_query.get_posts_from_projects(project_id)
    if records == '404':
      return redirect('/404')
    project_posts = []
    for row in records:
      project_posts.insert(0, {
        'post_id': row[0],
        'project_id': row[1],
        'username': row[2],
        'timestamp': row[3],
        'title': row[4],
        'post': reformat_paragraph(row[5]),
        'music_genre': row[6],
        'help_needed': row[7],
        'likes': row[8]})
    return render_template("project.html", project=project, len=len(project_posts), project_posts=project_posts)
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

@app.route("/project/chat/<int:project_id>", methods=['GET','POST'])
@app.route("/project/chat/<int:project_id>")
def project_chat(project_id):
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    row = panthertunes_query.get_project(project_id)
    if row == '404':
      return redirect('/404')
    project = {
      'project_id': row[0],
      'usernames': row[1],
      'title': row[2],
      'desc': row[3],
      'post_ids': row[4],
      'chat_id': row[5]}
    records = panthertunes_query.get_posts_from_projects(project_id)
    if records == '404':
      return redirect('/404')
    project_posts = []
    for row in records:
      project_posts.insert(0, {
        'post_id': row[0],
        'project_id': row[1],
        'username': row[2],
        'timestamp': row[3],
        'title': row[4],
        'post': reformat_paragraph(row[5]),
        'music_genre': row[6],
        'help_needed': row[7],
        'likes': row[8]})
    return render_template("project-chat.html", project=project, len=len(project_posts), project_posts=project_posts)
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

@app.route("/project/applications/<int:project_id>", methods=['GET','POST'])
@app.route("/project/applications/<int:project_id>")
def project_application(project_id):
  if request.method == 'GET':
    if not session['name']:
      return redirect('/sign-in')
    row = panthertunes_query.get_project(project_id)
    if row == '404':
      return redirect('/404')
    project = {
      'project_id': row[0],
      'usernames': row[1],
      'title': row[2],
      'desc': row[3],
      'post_ids': row[4],
      'chat_id': row[5]}
    applications = []
    records = panthertunes_query.get_applications_from_project(project_id)
    for row in records:
      applications.insert(0, {
        'application_id': row[0],
        'project_id': row[1],
        'username': row[2],
        'pitch': row[3],
        'timestamp': row[4]})
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

@app.route("/404")
def error():
  return render_template("404.html")

@app.errorhandler(404)
def nonexistent_url(error):
  print(error)
  return render_template("404.html")

if __name__ == "__main__":
  app.run(port=1601, debug=True)
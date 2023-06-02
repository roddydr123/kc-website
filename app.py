from flask import (Flask, flash, jsonify,
                   redirect, render_template, request, session)
from flask_session.__init__ import Session
from pymethods import (login_required, check_reg, apology,
                       dbs, dbss, getAdjective, getElapsedTime, genName)
from werkzeug.security import check_password_hash, generate_password_hash
from tempfile import mkdtemp
from datetime import datetime
from os import path



app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/index", methods=['GET'])
@app.route("/", methods=['GET'])
@app.route("/clubfish", methods=['GET', 'POST'])
def clubfish():
    if request.method == 'GET':
        return render_template("clubfish.html", title="Club Fish",
                               foot="7 Seas Media Group")

    else:
        uname = request.form['username']

        # route for registering
        if 'register' in request.form:

            pword = request.form['password']
            # check info is correct format
            if not check_reg(uname, pword):
                flash("invalid username or password")
                return redirect("/clubfish")

            # check if username already exists
            query = ''' SELECT * FROM users WHERE username = ? '''
            # query database
            results = dbs(query, [uname])

            if len(results) != 0:
                flash("username already exists")
                return redirect("/clubfish")

            # hash password to store
            hashed = generate_password_hash(pword)
            entities = (uname, hashed)
            # add username and password to database
            query = ''' INSERT INTO users(username,password)
                        VALUES(?, ?) '''
            # add user to database
            dbs(query, entities)
            flash("successful registration")
            return redirect('/clubfish')

        # route for logging in
        else:

            # check if username and password in database correctly
            query = ''' SELECT password, id
            FROM users
            WHERE username = ? '''

            details = dbss(query, [uname], 'password', 'user_id')
            pword = request.form['password']
            if len(details) != 1:
                flash("username does not exist")
                return redirect("/clubfish")
            details = details[0]
            if not check_password_hash(details['password'], pword):
                flash("incorrect password")
                return redirect("/clubfish")
            session['user_id'] = details['user_id']
            session['username'] = uname
            session['respected'] = []
            session['disrespected'] = []
            return redirect("/fishhome")


@app.route("/apology/<reason>")
def apo(reason):
    return apology(reason)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/clubfish")


@app.route("/fishhome")
@login_required
def fishhome():

    user_id = session['user_id']
    # connect to database and write query to find the user's fish
    query = ''' SELECT *
                FROM fish
                WHERE user_id = ?
                ORDER BY fish_id DESC
                LIMIT 20 '''

    fishinfo = dbss(query, [user_id], 'fish_id', 'species', 'user_id', 'birth',
                    'name', 'respect', 'image')

    # check if user has made a fish previously
    if fishinfo == []:
        # if they haven't
        message = "You don't have a fish yet, create one?"
    else:
        # if they have, set image to the tyoe of fish
        # make sure the image name is fishtype.jpg
        message = None
        # find the age of the fish
        now = datetime.now()
        a = 0

        # get an adjective
        ROOT = path.dirname(path.realpath(__file__))
        file1 = open(path.join(ROOT, "static/adjects2.txt"), "r")
        adjs = [line.strip() for line in file1 if line.strip()]
        file1.close()

        for fish in fishinfo:
            created = datetime.strptime(fish["birth"], '%Y-%m-%d %H:%M:%S.%f')
            age = now - created
            age = age.days
            fish["age"] = age
            fish["first"] = False
            if a == 0:
                fish["first"] = True
            if a % 2 == 0:
                fish["pron1"] = "She"
                fish["pron2"] = "her"
            else:
                fish["pron1"] = "He"
                fish["pron2"] = "his"
            a += 1
            fish["adjective"] = adjs[getAdjective(adjs, fish["fish_id"],
                                                  fish["respect"])]

        return render_template("fishhome.html", message=message,
                               dicts=fishinfo)
    return render_template("fishhome.html", message=message)


@app.route("/myfish", methods=['GET', 'POST'])
@login_required
def myfish():

    if request.method == 'GET':
        return render_template("myfish.html")

    # submitting a newly designed fish
    else:

        user_id = session['user_id']

        if "mergebutton" in request.form:
            fish1_id = request.form["mother"]
            fish2_id = request.form["father"]
            query = ''' SELECT name, species, user_id, fish_id, image
                        FROM fish
                        WHERE fish_id = ?
                        OR fish_id = ? '''

            entities = (fish1_id, fish2_id)
            bothfish = dbss(query, entities, "name",
                            "species", "user_id", "fish_id", "image")
            species = bothfish[1]["species"]
            newname = genName(bothfish[0]["name"], bothfish[1]["name"])
            species = bothfish[0]["species"]
            time = datetime.now()

            # insert new fish to database
            query = ''' INSERT INTO fish (species, user_id, time, name, image,
                                          mother_id, father_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?) '''
            entities = (species, user_id, time, newname, species, fish1_id,
                        fish2_id)
            dbss(query, entities)

            # log this action
            if bothfish[0]["user_id"] == user_id:
                actee_id = bothfish[1]["user_id"]
                fish_id = bothfish[1]["fish_id"]
            else:
                actee_id = bothfish[0]["user_id"]
                fish_id = bothfish[0]["fish_id"]
            action = f"made another fish called {newname} with"
            query = ''' INSERT INTO actions (actor_id, actee_id, action, time, fish_id)
                        VALUES (?, ?, ?, ?, ?) '''
            entities = (user_id, actee_id, action, time, fish_id)
            dbs(query, entities)

            return redirect("/fishhome")
        else:
            fishtype = request.form.getlist('fishoptions')
            fishname = request.form.get('fishname')
            # fishname is string
            # fishtype is list with 'minnow' as only element

            if not fishtype or not fishname:
                flash("please fill in fields")
                return redirect("/myfish")

            # make sure the name is a string
            try:
                int(fishname)
                flash("choose a nicer name")
                return redirect("/myfish")
            except ValueError:
                pass

            if len(fishname) > 25:
                flash("not as long pls")
                return redirect("/myfish")

            # insert fish choice into fish database
            now = datetime.now()
            entities = (fishtype[0], user_id, now, fishname, fishtype[0])
            query = ''' INSERT INTO fish (species, user_id, time, name, image)
                        VALUES (?, ?, ?, ?, ?) '''
            dbss(query, entities)

            return redirect("/fishhome")


@app.route("/addcomment", methods=["POST"])
@login_required
def addcomment():

    user_id = session["user_id"]
    fish_id = request.form["fish_id"]
    commentstr = request.form["commentstr"]
    time = datetime.now()
    username = session["username"]
    if not commentstr or commentstr == "":
        return redirect("/rivalfish")
    if len(commentstr) > 150:
        flash("comment too long")
        return redirect("/rivalfish")

    query = ''' INSERT INTO comments (fish_id, user_id, comment, time)
                VALUES (?, ?, ?, ?) '''

    entities = (fish_id, user_id, commentstr, time)
    dbss(query, entities)

    # get owner id of fish commented on
    query = ''' SELECT users.id
                FROM users
                JOIN fish ON users.id = fish.user_id
                WHERE fish_id = ? '''
    actee_id = dbss(query, [fish_id], "actee_id")[0]["actee_id"]

    # log this interaction
    actor_id = session["user_id"]
    time = datetime.now()
    action = "commented on"
    query = ''' INSERT INTO actions (actor_id, actee_id, action, time, fish_id)
                VALUES (?, ?, ?, ?, ?) '''
    entities = (actor_id, actee_id, action, time, fish_id)
    dbs(query, entities)

    response = {
        "commentstr": commentstr,
        "username": username
    }

    return jsonify(response)


@app.route("/rivalfish", methods=["GET"])
@login_required
def rivalfish():

    user_id = session['user_id']
    # search database for most recent new fish as rivals
    query = ''' SELECT species, name, username, fish_id, respect, image
                FROM fish
                JOIN users ON fish.user_id = users.id
                WHERE NOT user_id=(?)
                ORDER BY fish_id DESC
                LIMIT 3 '''
    threerivs = dbss(query, [user_id], 'species', 'name', 'username',
                     'fish_id', 'respect', 'image')
    allcom = []
    othercom = []
    for fish in threerivs:
        fish_id = fish["fish_id"]
        if str(fish['fish_id']) in session['respected']:
            fish['respected'] = "RESPECTED"
        elif str(fish['fish_id']) in session['disrespected']:
            fish['respected'] = "DISRESPECTED"
        # get comments
        query = ''' SELECT comment, time, username, fish_id
                    FROM comments
                    JOIN users ON comments.user_id = users.id
                    WHERE fish_id = ?
                    ORDER BY time DESC '''
        comments = dbss(query, [fish_id],
                        'comment', 'time', 'username', 'fish_id')
        for comment in comments:
            comment["time"] = getElapsedTime(comment["time"])

        allcom.append(comments[:3])
        othercom.append(comments)

    return render_template("rivalfish.html", dicts=threerivs, allcom=allcom,
                           othercom=othercom)


@app.route("/respect", methods=['POST'])
@login_required
def respect_incr():

    fish_id = request.form['fishid']
    done = False
    # check if user has already respected a fish
    if fish_id in session['respected']:
        done = True
    elif fish_id in session['disrespected']:
        done = True

    # get the fishes current respect value
    query = ''' SELECT respect FROM fish
                WHERE fish_id=(?) '''
    info = dbss(query, [fish_id], 'respect')[0]
    respectval = info['respect']

    # add dis/respected fish to session list so it cant be done again
    if done is False:
        if request.form["type"] == "resp":
            respectval += 1
            session['respected'].append(fish_id)
            action = "respected"
        elif request.form["type"] == "diss":
            respectval -= 1
            session['disrespected'].append(fish_id)
            action = "disrespected"
        else:
            # some weird button was used
            flash("prob")

    # update the fishes respect value
    entities = (respectval, fish_id)
    query = ''' UPDATE fish
                SET respect=?
                WHERE fish_id=? '''
    dbs(query, entities)

    # get the user_id this fish belongs to
    query = ''' SELECT users.id
                FROM users
                JOIN fish ON users.id = fish.user_id
                WHERE fish_id = ? '''
    actee_id = dbss(query, [fish_id], "actee_id")[0]["actee_id"]

    # log this interaction
    actor_id = session["user_id"]
    time = datetime.now()
    query = ''' INSERT INTO actions (actor_id, actee_id, action, time, fish_id)
                VALUES (?, ?, ?, ?, ?) '''
    entities = (actor_id, actee_id, action, time, fish_id)
    dbs(query, entities)

    response = {"respect": respectval, "done": done}
    # return respect value fetched from db
    return jsonify(response)


@app.route("/lookup", methods=['GET', 'POST'])
@login_required
def lookup():

    if request.method == 'GET':
        # get the most repected fish
        query = ''' SELECT name, username, respect, species, fish_id, image
                    FROM fish
                    JOIN users ON fish.user_id = users.id
                    ORDER BY respect DESC '''
        entities = (None)
        winners = dbss(query, entities, 'name', 'username', 'respect',
                       'species', 'fish_id', 'image')
        last = len(winners) - 1
        winnerids = []

        # get adjectives
        ROOT = path.dirname(path.realpath(__file__))
        file1 = open(path.join(ROOT, "static/adjects2.txt"), "r")
        adjs = [line.strip() for line in file1 if line.strip()]
        file1.close()

        file2 = open(path.join(ROOT, "static/nouns.txt"), "r")
        nouns = [line.strip() for line in file2 if line.strip()]
        file2.close()
        # check which fish have been respected this session
        for fish in winners:
            if str(fish['fish_id']) in session['respected']:
                fish['respected'] = "RESPECTED"
            elif str(fish['fish_id']) in session['disrespected']:
                fish['respected'] = "DISRESPECTED"
            winnerids.append(fish["fish_id"])
            fish["adjective"] = adjs[getAdjective(adjs, fish["fish_id"],
                                                  fish["respect"])]
            fish["noun"] = nouns[getAdjective(nouns, fish["fish_id"],
                                              fish["respect"])]

        lost = winners[last]
        winners = [winners[0], winners[1], winners[2]]
        entities = (winnerids[0], winnerids[1], winnerids[2], lost["fish_id"])

        # get all the other fish
        query = ''' SELECT name, username, respect, species, fish_id, image
                    FROM fish
                    JOIN users ON fish.user_id = users.id
                    WHERE (fish_id != ?) AND (fish_id != ?) AND (fish_id != ?)
                    AND (fish_id != ?)
                    ORDER BY name
                    LIMIT 100 '''
        losers = dbss(query, entities, 'name', 'username', 'respect',
                      'species', 'fish_id', 'image')

        for fish in losers:
            if str(fish['fish_id']) in session['respected']:
                fish['respected'] = "RESPECTED"
            elif str(fish['fish_id']) in session['disrespected']:
                fish['respected'] = "DISRESPECTED"
            fish["adjective"] = adjs[getAdjective(adjs, fish["fish_id"],
                                                  fish["respect"])]
            fish["noun"] = nouns[getAdjective(nouns, fish["fish_id"],
                                              fish["respect"])]

        if winners is [] or losers is []:
            flash("big error, probs cant reach database or something")
            return redirect("/fishhome")

        return render_template("lookup.html", search_fren=False,
                               winners=winners, losers=losers,
                               last=lost, comments=[])

    else:
        # user can search for a friend
        username = request.form.get('username')

        query = ''' SELECT name, respect, species, time, username, image
                    FROM fish
                    JOIN users ON fish.user_id = users.id
                    WHERE username=?
                    ORDER BY respect DESC '''
        info = dbss(query, [username], 'name', 'respect',
                    'species', 'birth', 'username')
        if info == []:
            flash("check your spelling")
            return redirect("/lookup")

        return render_template("lookup.html", search_fren=True,
                               info=info)


@app.route("/viewcomments", methods=["POST"])
@login_required
def viewcomments():
    fish_id = request.form["fish_id"]
    query = ''' SELECT comment, time, username, fish_id
                    FROM comments
                    JOIN users ON comments.user_id = users.id
                    WHERE fish_id = ?
                    ORDER BY time DESC '''
    comments = dbss(query, [fish_id],
                    'comment', 'time', 'username', 'fish_id')
    for comment in comments:
        comment["time"] = getElapsedTime(comment["time"])

    return jsonify(comments)


@app.route("/notifications", methods=["GET", "POST"])
@login_required
def notifications():
    user_id = session["user_id"]
    if request.method == "GET":
        query = ''' SELECT username, action, actions.time, name
                    FROM actions
                    JOIN users ON users.id = actions.actor_id
                    JOIN fish ON actions.fish_id = fish.fish_id
                    WHERE actee_id = ?
                    AND NOT actions.fish_id = ?
                    ORDER BY actions.id DESC '''
        entities = (user_id, -1)
        notifications = dbss(query, entities,
                             "username", "action", "time", "name")
        for notif in notifications:
            notif["time"] = getElapsedTime(notif["time"])
        # checking notifications is an action
        time = datetime.now()
        query = ''' INSERT INTO actions(actor_id, actee_id, action, time, fish_id)
                    VALUES (?, ?, ?, ?, ?) '''
        entities = (user_id, -1, "opened notifications", time, -1)
        dbs(query, entities)
        return render_template("notifications.html",
                               notifications=notifications)

    else:
        # find last time they checked notifications
        query = ''' SELECT time
                    FROM actions
                    WHERE actor_id = ?
                    AND actee_id = ?
                    ORDER BY id DESC
                    LIMIT 1 '''
        entities = (user_id, -1)
        lasttime = dbss(query, entities, "time")[0]["time"]

        query = ''' SELECT time
                    FROM actions
                    WHERE actions.actee_id = ?
                    AND time > ? '''
        entities = (user_id, lasttime)
        result = dbss(query, entities, "time")

        if len(result) == 0:
            return jsonify({"new": "none"})
        else:
            return jsonify({"new": "some"})


@app.route("/babyfish", methods=["GET", "POST"])
@login_required
def babyfish():
    user_id = session["user_id"]
    # they're just viewing the page
    if request.method == "GET":
        # get their fish
        query = ''' SELECT fish_id, species, user_id, time, name, respect, image
                    FROM fish
                    WHERE user_id = ? '''
        myschool = dbss(query, [user_id], "fish_id", "species", "user_id",
                        "time", "name", "respect", "image")
        for fish in myschool:
            fish["time"] = getElapsedTime(fish["time"])

        # get all other fish
        query = ''' SELECT fish_id, species, user_id, time, name, respect, image
                    FROM fish
                    WHERE NOT user_id = ? '''
        otherfish = dbss(query, [user_id], "fish_id", "species", "user_id",
                         "time", "name", "respect", "image")
        for fish in otherfish:
            fish["time"] = getElapsedTime(fish["time"])

        return render_template("babyfish.html", myschool=myschool,
                               otherfish=otherfish)

    else:
        query = ''' SELECT fish_id, species, user_id, time, name, respect, image
                    FROM fish
                    WHERE user_id = ?
                    ORDER BY id DESC
                    LIMIT 1 '''
        fish = dbss(query, [user_id], "fish_id", "species", "user_id",
                    "time", "name", "respect", "image")
        return render_template("babyfish.html", newfish=fish)


@app.route("/idfish", methods=["POST"])
@login_required
def idfish():
    fish_id = request.form["fish_id"]
    query = ''' SELECT username, species, user_id, time, name, respect, image
                FROM fish
                JOIN users ON users.id = fish.user_id
                WHERE fish_id = ? '''
    fish = dbss(query, [fish_id], "username", "species", "user_id",
                "time", "name", "respect", "image")[0]
    fish["time"] = getElapsedTime(fish["time"])
    return jsonify(fish)


@app.route("/deletefish", methods=["POST"])
@login_required
def deletefish():
    fish_id = request.form["fish_id"]
    query = ''' DELETE FROM fish
                WHERE fish_id = ? '''
    dbss(query, [fish_id])
    session["deleted"] = True
    flash("fish deleted :(")
    return redirect("/fishhome")

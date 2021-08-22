from flask import render_template, session, redirect, flash
from functools import wraps
import sqlite3
from sqlite3 import Error
from os import path
from datetime import datetime
import random


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            flash("Please log in")
            return redirect('/clubfish')
        return f(*args, **kwargs)
    return decorated_function


def check_reg(uname, pword):
    if uname is None or pword is None:
        return False

    if len(uname) < 4:
        return False

    if len(pword) < 4:
        return False
    return True


def dbs(query, entities):
    try:
        ROOT = path.dirname(path.realpath(__file__))
        con = sqlite3.connect(path.join(ROOT, "clubfish.db"))
    except Error:
        print(Error)
        return apology("database connection error")
    cur = con.cursor()
    if entities is not None:
        cur.execute(query, entities)
    else:
        cur.execute(query)
    con.commit()
    return cur.fetchall()


def dbss(query, entities, *args):
    try:
        ROOT = path.dirname(path.realpath(__file__))
        con = sqlite3.connect(path.join(ROOT, "clubfish.db"))
    except Error:
        print(Error)
        return apology("database connection error")
    cur = con.cursor()
    if entities is not None:
        cur.execute(query, entities)
    else:
        cur.execute(query)
    result = cur.fetchall()
    con.commit()
    allfish = []
    for fish in result:
        i = 0
        fishdict = {}
        for arg in args:
            fishdict[arg] = fish[i]
            i += 1
        allfish.append(fishdict)
    return allfish


def apology(reason):
    return render_template("apology.html", reason=reason)


def getAdjective(listt, fish_id, respect):
    index = fish_id % len(listt)
    try:
        x = ((fish_id * ord(listt[index][0]))
             - (ord(listt[index-1][-1]) * respect))
    except IndexError:
        x = fish_id * 112981292
    return x % len(listt)


def getElapsedTime(time):
    try:
        created = datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f')
        diff = datetime.now() - created
        if diff.days == 0 and diff.seconds / 3600 < 1:
            if round(diff.seconds / 60) == 0:
                result = "just now"
            elif round(diff.seconds / 60) == 1:
                result = "1 minute ago"
            else:
                result = str(round(diff.seconds / 60)) + " mins ago"
        elif round(diff.seconds / 3600) == 1 and diff.days == 0:
            result = "about an hour ago"
        elif diff.seconds / 3600 > 1 and diff.days == 0:
            result = str(round(diff.seconds / 3600))+" hours ago"
        elif diff.days == 1:
            result = "1 day ago"
        else:
            result = str(diff.days) + " days ago"
    except (ValueError, TypeError):
        result = "a while ago"

    return result


def genName(name1, name2):
    ROOT = path.dirname(path.realpath(__file__))
    with open(path.join(ROOT, "static/name-suffix.txt"), "r") as file1:
        suffixes = file1.read().splitlines()
    with open(path.join(ROOT, "static/species-prefix.txt"), "r") as file2:
        prefixes = [line.split(',') for line in file2 if line.split()][0]
    print(prefixes)
    print(suffixes)
    ran1 = random.randint(0, 50)
    ran2 = random.randint(0, 50)
    if ord(name1[-3]) % 2 == 0:
        suffix = suffixes[getAdjective(suffixes, ran1, ran2)]
    else:
        suffix = ""

    if ord(name1[-3]) % 2 != 0:
        prefix = prefixes[getAdjective(prefixes, ran1, ran2)]
    else:
        prefix = ""
    print(prefix, suffix)
    newname = f'{prefix}{name1[:round(len(name1)/2)]}{name2[round(len(name2)/2):]}{suffix}'
    return newname

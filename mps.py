#! /usr/bin/env python3

import os
import subprocess
import sqlite3

import cherrypy

def load_templates(template_dir):
    templates = [template.split('.html')[0] for template in os.listdir(path=template_dir)]
    html = dict()
    for template in templates:
        with open(template_dir + '/' + template + '.html') as f:
            html[template] = f.read()
    return html

def pdftotext(data):
    return subprocess.check_output(['pdftotext', '-', '-'], input=data).decode()

html = load_templates('templates')

class MealplanDatabase(object):
    def __init__(self):
        self.dbfile = 'mps.db'
        self.fields = ('plan_type', 'date', 'filename', 'content', 'rowid')

    def new_db(self):
        conn = sqlite3.connect(self.dbfile)
        conn.execute('create virtual table mealplans using fts4(plan_type, date, filename, content, notindexed=date)')
        conn.commit()
        conn.close()

    def add(self, plan_type, date, filename, content):
        conn = sqlite3.connect(self.dbfile)
        conn.execute('insert into mealplans values(?, ?, ?, ?)', (plan_type, date, filename, content))
        conn.commit()
        conn.close()

    def remove(self, rowid):
        conn = sqlite3.connect(self.dbfile)
        conn.execute('delete from mealplans where rowid=?', (rowid,))
        conn.commit()
        conn.close()

    def get(self, rowid):
        conn = sqlite3.connect(self.dbfile)
        record = conn.execute('select *,rowid from mealplans where rowid=?', (rowid,)).fetchone()
        conn.close()
        return record

    def search(self, query):
        conn = sqlite3.connect(self.dbfile)
        records = conn.execute('select *,rowid from mealplans where mealplans match ?', (query,)).fetchall()
        conn.close()
        out = [dict(zip(self.fields, record)) for record in records]
        return out

mealplan_db = MealplanDatabase()

class Root(object):
    @cherrypy.expose
    def index(self):
        if not os.path.isfile(mealplan_db.dbfile):
            out = 'Database does not exist. Creating new.'
            mealplan_db.new_db()
        else:
            out = html['search']
        return html['template'].format(content=out)

    @cherrypy.expose
    def search(self, query):
        out = ''
        for record in mealplan_db.search(query):
            out += html['record'].format(**record)
        return html['template'].format(content=out)

    @cherrypy.expose
    def add(self, pdf_file=None, plan_type=None, date=None):
        out = ''
        if pdf_file and plan_type and date:
            filename = pdf_file.filename
            content = pdftotext(pdf_file.file.read())
            content = ' '.join(content.split())
            mealplan_db.add(plan_type, date, filename, content)
        else:
            out += html['add']
        return html['template'].format(content=out)

cherrypy.config.update('server.conf')

if __name__ == '__main__':
    cherrypy.quickstart(Root(), '/', 'app.conf')

#! /usr/bin/env python3

import os
import sqlite3

import cherrypy

def load_templates(template_dir):
    templates = [template.split('.html')[0] for template in os.listdir(path=template_dir)]
    html = dict()
    for template in templates:
        with open(template_dir + '/' + template + '.html') as f:
            html[template] = f.read()
    return html

html = load_templates('templates')

class MealplanDatabase(object):
    def __init__(self):
        self.dbfile = 'mps.db'

    def new_db(self):
        conn = sqlite3.connect(self.dbfile)
        conn.execute('create virtual table mealplans using fts4(plan_type, date, content, notindexed=date)')
        conn.commit()
        conn.close()

    def add(self, plan_type, date, content):
        conn = sqlite3.connect(self.dbfile)
        conn.execute('insert into mealplans values(?, ?, ?)', (plan_type, date, content))
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
        return records

class Root(object):
    @cherrypy.expose
    def index(self):
        out = html['search']
        return html['template'].format(content=out)

cherrypy.config.update('server.conf')

if __name__ == '__main__':
    cherrypy.quickstart(Root(), '/', 'app.conf')

# admin.py
# modify this for additional administrative views

from flask import abort, g, render_template, redirect, session

# adding flask_admin
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.peewee import ModelView

import models

# flask-admin setup
class MyAdminView(AdminIndexView):
    @expose('/')
    def index(self):
        try:
            if session.get('is_admin'):
                # return render_template('admin/index.html')
                return redirect('/admin/user') # just a simple redirect to user admin, can be improved
        except Exception as e:
            print(e)
            pass # silently fail for unauthorized trying to access admin space

        abort(403)

def initialize(app):
    admin = Admin(app, template_mode='bootstrap3', index_view=MyAdminView())
    admin.add_view(ModelView(models.User))

    # ADD YOUR ADDITIONAL ADMIN VIEWS BELOW (use User model as a template)

    admin.add_view(ModelView(models.Group))
    admin.add_view(ModelView(models.UserMembership))
    admin.add_view(ModelView(models.Page))
   
    return admin
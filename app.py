import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime as dt
from flask import (abort, flash, Flask, g, redirect, render_template, request, session, url_for)
from flask_bootstrap import Bootstrap
import sys
import forms
import models
import admin
from utils import login_required, get_object_or_404, get_object_or_None

# basic Flask setup
app = Flask(__name__)
app.secret_key = 'Y7&8*2NCLka@F0OpEdfn^6'

# add some Bootstrap handling needed by WTForms
Bootstrap(app)

# set up logging
log_handler = RotatingFileHandler('./log/info.log', maxBytes=2000, backupCount=1)
log_format = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(log_format)
app.logger.setLevel(logging.INFO)
app.logger.addHandler(log_handler) 

# set up admin
admin.initialize(app)

def setup():
    setattr(g,"brand","FlaskPress")
    setattr(g,"brand_logo", "/static/fplogo/fp_logo_3.png")
    setattr(g,"brand_alt", "FlaskPress: a minimalist CMS based on Flask")
    
# request handlers
@app.before_request
def before_request():
    setup()
    g.db = models.DATABASE
    try:
        g.db.connect()
    except Exception as e:
        app.logger.error('ERROR: DB connect @ {}'.format(dt.now()))
        app.logger.error('ERROR = {}'.format(e))

@app.after_request
def after_request(response):
    try:
        g.db.close()
    except Exception as e:
        app.logger.error('ERROR: attempt to close DB @'.format(dt.now()))
        app.logger.error('ERROR = {}'.format(e))
    return response



@app.route('/cms/pages', strict_slashes=False)
@app.route('/cms/pages/<int:user_id>')
@login_required
def user_pages(user_id=None):
    """show all the pages associated with this user_id, if user_id=None, get ALL pages"""
    s = request.args.get('s')
    if s:
        return redirect( url_for('search', s=s) )
    
    if user_id:
        pages = models.Page.select().where(models.Page.owner==user_id)
        user = get_object_or_404(models.User, user_id)
        title = "Pages by {}".format(user.canonical_name())
    else:
        pages = models.Page.select()
        title = "Pages by ALL users"
        
    return render_template('cms/default/pages_view.html', pages=pages, title=title)

@app.route('/cms/page/<int:page_id>')
def page_view(page_id):
    """view page by its id, this is not the public route"""
    page = get_object_or_404(models.Page, page_id)
    if not(page.is_published) and not(session.get('is_authenticated')):
        abort(404)
    return render_template('cms/default/page_view.html', page=page)

@app.route('/cms/page/new', methods=['GET','POST'])
@app.route('/cms/page/<int:page_id>/edit', methods=['GET','POST'])
@login_required
def page_edit(page_id=None):
    """edit an existing page, or create a page if page_id is None"""
    # if page_id = None, then we are creating a new page.
    
    # possible errors, we use this in the validation process
    errors = {'title':'', 'title_category':'', 'content':'', 'content_category':''}
    
    if page_id:
        # get existing page by page_id or 404
        page = get_object_or_404(models.Page, page_id)
    else:
        # empty page for the form
        page = models.Page()

    error_flag = False
    # see if we were called POST
    if request.method == 'POST':
        title = request.form.get('title')
        if not(title):
            errors['title'] = 'Title cannot be blank'
            errors['title_category'] = 'is-danger'
            error_flag = True
        show_title = request.form.get('show_title') == 'on'
        show_nav = request.form.get('show_nav') == 'on'
        slug = request.form.get('slug')
        is_published = request.form.get('is_published') == 'on'
        content = request.form.get('content')
        if not(content):
            errors['title'] = 'Title cannot be blank'
            errors['title_category'] = 'is-danger'
            error_flag = True
        parent = request.form.get('parent')
        
        # if no errors get around to creating or saving new page.
        # implement later, maybe always create a new row for page, old page marked as not published, revision timestamp.
        if not(error_flag):
            try:
                # ensure parent is int or None
                parent = int(parent)
            except:
                parent = None
                
            if page_id is None:
                page = models.Page.create(owner=session['user_id'], title=title, slug=slug, parent=parent,
                                          show_title=show_title, show_nav=show_nav,
                                          content=content, is_published=is_published)
            else:
                page.title = title
                page.show_title = show_title
                page.show_nav = show_nav
                page.slug = slug
                page.content = content
                page.is_published = is_published
                page.parent = parent
            # if slug was left blank, we can make a slug based on page
            if page.slug == '':    
                page.generate_slug()
            page.save()
            #return redirect( url_for('page_view', page_id=page.id) )
            return redirect(page.url())
        else:
            flash('There were errors on the page', category='danger')
    
    # build a list of potential parents for the FORM select field    
    pages = models.Page.select()
    parents=[("","None")] # a None parent is allowed.
    for p in pages:
        parents.append((p.id, p.title))
        
    return render_template('cms/default/page_edit.html', errors=errors, page=page, parents=parents)
    
@app.route('/profile')
@app.route('/profile/<int:user_id>')
@login_required
def user_profile(user_id=None):
    s = request.args.get('s')
    if s:
        return redirect( url_for('search', s=s) )
    
    if user_id is None:
        user_id = session['user_id']
    user = get_object_or_404(models.User, user_id)
    return render_template('cms/default/profile.html', user=user)

@app.route("/login", methods=('GET','POST'))
def login():
    error=""
    help=""
    form = forms.LoginForm(request.form)
    if request.method == 'POST':
        try:
            user = models.User.get(models.User.username==form.username.data)
            
            if user.authenticate(form.password.data):
                if user.is_admin:
                    session['is_admin'] = True
                session['user_id'] = user.id
                session['is_authenticated'] = True
                return redirect(url_for('user_profile', user_id=user.id))
            else:
                raise ValueError("Incorrect Password")
        except Exception as e:
            app.logger.error("login failed for %s" % form.username.data)
            error_message = "username or password is incorrect"
            error = "is-danger"
            help=error_message
        
    return render_template('cms/default/login.html',form=form, error=error, help=help)

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You are logged out.", category="warning")
    return redirect(url_for('index'))

@app.route("/cms/search")
def search():
    search_term = request.args.get('s')
    pages = models.Page.select().where(models.Page.content.contains(search_term))
    return render_template('cms/default/search.html', pages=pages, search_term=search_term)

@app.route('/test')
def test():
    return render_template("test.html")

# this is the general route "catchment"
@app.route("/")
@app.route("/<path:path>")
def index(path=None):
    s = request.args.get('s')
    if s:
        return redirect( url_for('search', s=s) )
    
    if path is None:
        # try to find the default page with no parent
        page = models.Page.select().where(models.Page.slug=='default', models.Page.parent==None)
        if len(page)==0:
            return "Default Page"
        return render_template('cms/default/page_view_public.html', page=page[0], breadcrumbs=[])
    
    # path is broken into sequential slugs
    slugs = path.split('/')
    
    parent = None # top level pages have NO parent
    page = None # the page we are looking for
    breadcrumbs = []
    url = ''
    for slug in slugs:
        if parent:
            url += '/{}'.format(parent.slug)
            breadcrumbs.append((parent.slug, url))

        # query match for "slug" AND "parent"
        slug_match = models.Page.select().where(models.Page.slug==slug, models.Page.parent==parent)
            
        if len(slug_match):
            # first result is the page which matches the slug
            page = slug_match[0]
        else:
            # no matching slug found
            page = None
            break
        
        parent = page # if there are more slugs, make this the parent
    
    if page:         
        return render_template('cms/default/page_view_public.html', page=page, breadcrumbs=breadcrumbs)
    else:
        abort(404) # page not found, might want a custom 404.

def main():
    if '--initdatabase' in sys.argv:
        # initialize database
        app.logger.info("initialize database")
        models.init_database(sys.argv)
        sys.exit(0)
    elif '--createadmin' in sys.argv or '--createsuperuser' in sys.argv:
        # creating an admin user from command line
        success, msg = models.create_admin_cli(sys.argv)
        if success:
            app.logger.info('creating admin user "{}"'.format(msg))
            print("success")
        else:
            app.logger.error('problems creating admin user {}')
            print("failed: {}".format(msg))
            sys.exit(1)
        sys.exit(0)
    else:
        # check if the user wants to set port and host from command line
        port = 5000
        host = '127.0.0.1'
        debug = False
        for arg in sys.argv:
            if 'port=' in arg.lower():
                port = int(arg.replace('port=',''))
            if 'host=' in arg.lower():
                host = arg.replace('host=','').split(':')
                if len(host) > 1:
                    port = int(host[1])
                host = host[0]
            if 'debug=true' in arg.lower():
                debug=True
                
        app.logger.info("starting app on host={} port={} debug={}".format(host,port,debug))
        app.run(host=host, port=port, debug=debug)    
    
if __name__ == '__main__':
    main()
    
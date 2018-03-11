import re
from functools import wraps
from flask import abort, redirect, request, session, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #if g.user is None:
        if not(session.get('is_authenticated')):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def get_object_or_404(cls, object_id):
    try:
        return cls.get(cls.id==object_id)
    except:
        abort(404)
        
def get_object_or_None(cls, object_id):
    try:
        return cls.get(cls.id==object_id)
    except:
        return None

def slugify(s):
    """
    Simplifies ugly strings into something URL-friendly.
    >>> print slugify("[Some] _ Article's Title--")
    some-articles-title
    CREDIT - Dolph Mathews (http://blog.dolphm.com/slugify-a-string-in-python/)
    """

    # "[Some] _ Article's Title--"
    # "[some] _ article's title--"
    s = s.lower()

    # "[some] _ article's_title--"
    # "[some]___article's_title__"
    for c in [' ', '-', '.', '/']:
        s = s.replace(c, '_')

    # "[some]___article's_title__"
    # "some___articles_title__"
    s = re.sub('\W', '', s)

    # "some___articles_title__"
    # "some   articles title  "
    s = s.replace('_', ' ')

    # "some   articles title  "
    # "some articles title "
    s = re.sub('\s+', ' ', s)

    # "some articles title "
    # "some articles title"
    s = s.strip()

    # "some articles title"
    # "some-articles-title"
    s = s.replace(' ', '-')

    return s
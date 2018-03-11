from peewee import *
from playhouse.migrate import *
from flask_bcrypt import generate_password_hash, check_password_hash
import datetime
from utils import slugify

DATABASE = SqliteDatabase("minicms.db")

class BaseModel(Model):
    class Meta:
        database = DATABASE

class Group(BaseModel):
    """Group is not implemented but may have classes perhaps: Editor, Contributor, Reader"""
    name = CharField()
    
class User(BaseModel):
    """Basic User model"""
    username = CharField(unique=True)
    displayname = CharField(default="")
    email = CharField(default="")
    password = CharField()
    bio = TextField(default="")
    avatar = CharField(default="")
    is_active = BooleanField(default=True)
    is_admin = BooleanField(default=False)
    created_on = DateTimeField(default=datetime.datetime.now)
    
    def __repr__(self):
        """representation is just a username"""
        return self.username
    
    def canonical_name(self):
        """For users, return displayname if set, else username"""
        if self.displayname:
            return self.displayname
        return self.username
    
    def authenticate(self, password, enforce_encryption=True):
        """authenticate plain-text password, return True is matched"""
        # pretty much, you should never override enforce_encryption
        try:
            # an unencrypted password will throw an error
            password_match = check_password_hash(self.password, password)
        except:
            # a little extra work to ensure password database is encrypted!
            if enforce_encryption:
                self.encrypt_password()
                password_match = check_password_hash(self.password, password)
            else:
                password_match = self.password == password
            
        return password_match
    
    def encrypt_password(self, commit=True):
        self.password = generate_password_hash(self.password)
        if commit:
            self.save()    
    
class UserMembership(BaseModel):
    """User can belong to a group"""
    user = ForeignKeyField(User, related_name='user')
    group = ForeignKeyField(Group, related_name='group')

class Template(BaseModel):
    """a style template, located in templates/cms/<folder>"""
    name = CharField()
    folder = CharField()
    
    def __repr__(self):
        return self.name
    
class Page(BaseModel):
    """Page is the basis object for the CMS, it has ONE content area.  A template may potentially create other content areas"""
    owner = ForeignKeyField(User, related_name='owner')
    title = CharField()
    show_title = BooleanField(default=True)
    show_nav = BooleanField(default=True)
    parent = ForeignKeyField('self', null=True, related_name='children')
    template = ForeignKeyField(Template, null=True, related_name='template')
    slug = CharField(default="")
    is_published = BooleanField(default=True)
    content = TextField(default="")
    timestamp = DateTimeField(default=datetime.datetime.now)
    
    def __repr__(self):
        return self.title
    
    def url(self):
        """return the URL for the page"""
        this_url = '/' + self.slug
        if self.parent:
            this_url = self.parent.url() + "/" + self.slug
        return this_url
            
    
    def generate_slug(self):
        """call the utility to slugify the title"""
        # should write an automatic trigger in the future
        self.slug = slugify(self.title)
        
def init_database(args):
    DATABASE.connect()
    DATABASE.create_tables([User, Group, UserMembership, Template, Page], safe=True)
    create_default_page()
    create_default_user()
    
    # a migration example when I added show_title and show_nav to Page model
    #if '--migrate' in args:
        #migrator = SqliteMigrator(DATABASE)
        #migrate(
            #migrator.add_column('page', 'show_title', BooleanField(default=True)),
            #migrator.add_column('page', 'show_nav', BooleanField(default=True)),
        #)
        
def create_default_user():
    try:
        User.create(username="DefaultUser", password="DefaultPassword")
    except Exception as e:
        print(e)
        
def create_default_page():
    content="""
    <p>
    FlaskPress is an open-source micro-CMS (content management system).  It is our hope it will be useful to
    community members that have learned or are discovering the excellence of Python and the Flask web framework.
    </p>
    <p>
    FlaskPress leverages several Flask plugins and the simple and expressive PeeWee ORM by Charles Leifer.
    In addition, we use the Bulma CSS framework and Bootstrap under the hood.
    We look forward to community involvement to add more to the project.
    </p>"""
    try:
        page = Page.select().where(Page.slug=='default', Page.parent==None)
        if len(page)==0:
            Page.create(owner=1, title="Welcome to FlaskPress", slug="default", content=content)
    except Exception as e:
        print(e)
    
def create_admin_cli(args):
    """Allows the creation of an administrative user from CLI"""
    import getpass, sys
    username = raw_input("Enter username: ")
    password = getpass.getpass()
    if username:
        if password=='':
            print("ABORT: Blank passwords not permitted")
            sys.exit(0)
        try:
            user = User.create(username=username, password=password, is_admin=True)
            user.encrypt_password()
            return True, username
        except Exception as e:
            return False, e
    
    
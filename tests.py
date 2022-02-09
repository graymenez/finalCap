from unittest import TestCase

from app import app
from models import db,User

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///ems_gps_db_test'
app.config['SQLALCHEMY_ECHO'] = False

app.config['TESTING'] = True

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

db.drop_all()
db.create_all()

class UserViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        user = User(first_name='Corey',last_name='Jimenez',title='Paramedic',email='coreyjimenez1@gmail.com',password='1')
        db.session.add(user)
        db.session.commit()

        self.user_id = user.id
        self.first_name = user.first_name
        self.last_name = user.last_name
        self.title =user.title
        self.email=user.email
        self.password = user.password

    def tearDown(self):
        db.session.rollback()
    
    def test_create_user(self):
        with app.test_client() as client:
            d = {'first_name':"TestUser","last_name":"TestUserLast",'title':'TestUserTitle','email':'TestUserEmail','pwd':'TestUserPwd'}
            resp = client.post("/register",data=d,follow_redirects=True)
            html=resp.get_data(as_text=True)

            self.assertEqual(resp.status_code,200)

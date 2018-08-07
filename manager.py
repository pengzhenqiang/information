

from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand
from infor import Creat_app,db
from infor import models
from infor.models import User

"""
manager.py文件是入口程序
"""

# 用manger操作app
app = Creat_app("develop")
manager = Manager(app)
# 数据库迁移
Migrate(app,db)

manager.add_command("mysql",MigrateCommand)

@manager.option('-n', '-name', dest='name')
@manager.option('-p', '-password', dest='password')
def create_super_admin(name,password):
    user = User()
    user.mobile = name
    user.nick_name = name
    user.password = password
    user.is_admin = True

    db.session.add(user)
    db.session.commit()



if __name__ == '__main__':
    manager.run()

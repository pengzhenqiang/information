from flask import Blueprint
from flask import redirect
from flask import request
from flask import session

admin_blue = Blueprint("admin",__name__,url_prefix="/admin")

from . import  views

#检查是否是管理员
#在用户登陆之前判断一下，当前登陆的用户到底是不是管理员，如果不是，就不能进入主页
#g钩子，在用户登陆前就验证
#init可以算是views的父类，所以这个检查功能要写在最外面，
@admin_blue.before_request
def check_admin():

    #获取到session里面的数据,默认is_admin是False
    is_admin = session.get("is_admin",False)
    #如果不是管理员，就不能进入到后台系统，并且也不能让你请求后台的url地址，admin/login
    if not is_admin and not request.url.endswith("/admin/login"):
        return redirect("/")

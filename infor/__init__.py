import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask import g
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from config import config_map
import redis

from flask_wtf.csrf import generate_csrf

# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG) # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)

db = SQLAlchemy()
redis_store = None  #type: redis.StrictRedis
def Creat_app(config_name):
    app = Flask(__name__)


    config_class = config_map.get(config_name)
    app.config.from_object(config_class)

    db.init_app(app)
    # 创建redis对象(存储验证码，存储短信验证码和图片验证码)
    global redis_store
    redis_store = redis.StrictRedis(host=config_class.REDIS_HOST,port=config_class.REDIS_PORT,decode_responses=True)
    # 导入session：目的，用来进行持久化操作，不需要每次都让用户进行登陆，我们需要吧session存储到redis当中
    Session(app)
    # 开启CSRF保护
    CSRFProtect(app)
    # 使用请求钩子，在每次请求服务器的数据时候，那么我们吧返回的值添加一个csrf_token
    # 在程序运行完在运行的钩子里面,后续的函数必须由个返回值的参数
    @app.after_request
    def after_request(response):
        # 这个就是生成csrf_token
        csrf_token = generate_csrf()
        # 吧这个csrf_token，通过存储到cookie里面发送到前端，
        response.set_cookie("csrf_token",csrf_token)
        return response
    #设置全局的404报错
    from infor.utils.common import user_login_data
    @app.errorhandler(404)
    @user_login_data
    def errno_404_handler(error):
        user =g.user
        data={
            "user_info":user.to_dict() if user else None
        }
        return render_template("news/404.html",data=data)
    # 添加过滤器到系统
    from infor.utils.common import do_index_claas
    # 添加过滤器，第一个参数是过滤器的函数，第二个是过滤器名称
    app.add_template_filter(do_index_claas,"indexClass")

    from infor.index import index_blue
    # 注册首页蓝图
    app.register_blueprint(index_blue)
    #注册登陆注册的蓝图
    from  infor.passport import passport_blue
    app.register_blueprint(passport_blue)
    #注册新闻详情蓝图
    from  infor.news import news_blue
    app.register_blueprint(news_blue)
    #个人主页注册蓝图
    from  infor.user import user_blue
    app.register_blueprint(user_blue)
    #注册后台蓝图
    from  infor.admin import admin_blue
    app.register_blueprint(admin_blue)

    return app
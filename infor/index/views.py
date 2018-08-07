from flask import request,jsonify
from flask import session

from infor.models import User, News, Category
from infor.utils.response_code import RET
from . import index_blue
from flask import render_template, current_app

"""
新闻列表数据
"""
@index_blue.route("/news_list")
def new_list():
    # 获取分类id，是哪块的内容
    cid = request.args.get("cid",1)
    #页数，不传就是获取第一页,获取到前端页面传递过来的数据，表示第几页，第二参数表示默认从第一页开始
    page = request.args.get("page",1)
    # 每页多少条数据，如果不传，就是默认10条，第二条参数是默认每页10条
    per_page = request.args.get("per_page",10)
    try:
        page = int(page)
        cid = int(cid)
        per_page = int(per_page)
    except Exception as e:
        page = 1
        cid = 1
        per_page = 10

    filter = [News.reason == 0]
    if cid != 1:
        filter.append(News.category_id == cid)

    # if cid ==1:
    #     #News.create_time:表示获取新闻发布时间
    #     # paginate表示分页，第一个参数是提示，从什么页面开始，第二个参数表示，每页展示多少数据，第三个数据表示，是否需要警告
    #     paginate = News.query.order_by(News.create_time.desc()).paginate(page,per_page,False)
    # else:
    #     # News.category_id == cid新闻的外键，category_id等于分类的id，就能判断到这些新闻就是这个分类的
    paginate = News.query.filter(*filter).order_by(News.create_time.desc()).paginate(page,per_page,False)
    # 获取到当前页面需要展示的数据
    items = paginate.items
    #表示当前页面
    current_page = paginate.page
    #表示总页数
    total_page = paginate.pages

    news_list = []

    for item in items:
        news_list.append(item.to_dict())

    data={
        "current_page":current_page,
        "total_page":total_page,
        "news_dict_li":news_list
    }
    return jsonify(errno=RET.OK,errmsg="ok",data=data)


"""
current_app 代理对象，代理的就是app对象
@index_blue.route = @app.route()
"""


@index_blue.route("/favicon.ico")
def send_favicon():
    #     发送图标到浏览器
    return current_app.send_static_file("news/favicon.ico")


@index_blue.route("/")
def index():
    """判断当前的用户是否登陆成功"""
    # 因为在登陆的时候，我们吧数据存储到session里面，所以从session里面获取到当前登陆的用户
    # 这个session.get("user_id")这个获取的是User类里面的id值
    user_id = session.get("user_id")
    user = None
    # 需要判断当前用户是否登陆，
    if user_id:
        # 通过user_id
        user = User.query.get(user_id)


    # 获取到右边的热门点击新闻，limit(10)获取前十条新闻
    news = News.query.order_by(News.clicks.desc()).limit(10)
    news_list = []
    for new_mode in news:
        news_list.append(new_mode.to_dict())


    # 获取新闻分类
    categorys = Category.query.all()
    category_list = []
    for category in categorys:
        category_list.append(category.to_dict())

    data = {
        "user_info": user.to_dict() if user else None,
        "click_news_list": news_list,
        "categories":category_list
    }

    return render_template("news/index.html", data=data)

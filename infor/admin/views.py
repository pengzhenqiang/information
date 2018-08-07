from datetime import datetime, timedelta
import time

from flask import current_app
from flask import g, jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from infor import db
from infor.utils.common import user_login_data

from infor.models import User, News, Category
from infor.utils.response_code import RET
from . import admin_blue
from infor.utils.image_storage import storage
from infor import constants
"""
修改分类，增加分类
"""
@admin_blue.route("/add_category",methods=["GET","POST"])
def add_category():
    cid = request.json.get("id")
    name = request.json.get("name")
    #如果有id就表示修改标题
    #如果没有id就是表示增加
    if cid:
        category = Category.query.get(cid)
        category.name = name
    else:
        category=Category()
        category.name = name
        db.session.add(category)

    db.session.commit()
    return jsonify(errno=RET.OK,errmsg="保存成功")

"""
新闻分类
"""
@admin_blue.route("/news_type")
def news_type():
    categorys=Category.query.all()
    category_list =[]
    for category in categorys:
        category_list.append(category.to_dict())

    category_list.pop(0)
    data={
        "categories":category_list
    }
    return render_template("admin/news_type.html",data=data)
"""
编辑详情页面
"""
@admin_blue.route("/news_edit_detail",methods=["GET","POST"])
def news_edit_detail():
    if request.method=="GET":
        news_id=request.args.get("news_id")
        news=News.query.get(news_id)
        categorys=Category.query.all()
        category_list = []

        for category in categorys:
            category_list.append(category.to_dict())
        category_list.pop(0)
        data={
            "news":news.to_dict(),
            "categories":category_list

        }
        return render_template("admin/news_edit_detail.html",data=data)

    news_id = request.form.get("news_id")
    title = request.form.get("title")
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")
    category_id = request.form.get("category_id")
    if not all([title,digest,content,category_id]):
        return jsonify(errno=RET.PARAMERR,errmsg="数据错误")
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        return jsonify(errno=RET.NODATA,errmsg="未查到新闻数据")

    try:
        index_image = index_image.read()
        key = storage(index_image)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg="第三方系统错误")
    news.title = title
    news.digest = digest
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX+key
    news.category_id = category_id
    db.session.commit()

    return jsonify(errno=RET.OK,errmsg="OK")



"""
新闻编辑里面的所有内容的展示
"""
@admin_blue.route("/news_edit")
def news_edit():
    page = request.args.get("p",1)
    try:
        page = int(page)
    except Exception as e:
        page = 1

    paginate = News.query.order_by(News.create_time.desc()).paginate(page,10,False)

    items = paginate.items
    current_page = paginate.page
    total_page=paginate.pages

    items_list = []
    for item in items:
        items_list.append(item.to_review_dict())

    data={
        "news_list":items_list,
        "current_page":current_page,
        "total_page":total_page
    }
    return render_template("admin/news_edit.html",data=data)




"""
新闻审核详情
"""
@admin_blue.route("/news_review_detail",methods=["GET","POST"])
def news_review_detail():

    if request.method == "GET":
        news_id = request.args.get("news_id")
        news = News.query.get(news_id)
        data={
            "news":news.to_dict()

        }
        return render_template("admin/news_review_detail.html",data=data)
    #获取前端发送的操作指令
    action = request.json.get("action")
    #新闻id
    news_id = request.json.get("news_id")
    news = News.query.get(news_id)
    if action == "accept":
        #表示通过
        news.status =0
    else:
        #拒绝的原因
        reason =request.json.get("reason")
        #如果审核不通过，必须告诉我拒绝的理由
        if not reason:
            return jsonify(errno=RET.PARAMERR,errmsg="参数错误")
        news.status = -1
        news.reason = reason

    db.session.commit()
    return jsonify(errno=RET.OK,errmsg="OK")


"""
新闻审核
"""

@admin_blue.route("/news_review")
def news_review():
    #以分页的形式展示
    #要分页paginate
    #要排序
    #展示哪些带审核的和为审核的
    page = request.args.get("p",1)
    #这个是在页面搜索的时候用的
    keywords = request.args.get("keywords")
    try:
        page = int(page)
    except Exception as e:
        page=1

    filter = [News.status != 0]
    if keywords:
        #这个意思是，判断输入的，是否被包含在标题里面，contains被包含的功能
        filter.append(News.title.contains(keywords))
    #查询未审核和审核不通过的新闻，按照创建时间来倒叙，分页
    paginate = News.query.filter(*filter).order_by(News.create_time.desc()).paginate(page,10,False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    items_list = []
    for item in items:
        items_list.append(item.to_review_dict())

    data={
        "news_list":items_list,
        "current_page":current_page,
        "total_page":total_page
    }
    return render_template("admin/news_review.html",data=data)


"""
获取所有注册信息
"""
@admin_blue.route("/user_list")
def user_list():
    #获取当前页面
    page=request.args.get("p",1)
    try:
        page = int(page)
    except Exception as e:
        page = 1
    #获取所有不是管理员的用户,且按照最近登陆时间，倒叙，切分页
    paginate = User.query.filter(User.is_admin == False).order_by(User.last_login.desc()).paginate(page,10,False)
    #当页数据
    items = paginate.items
    #当前页数
    current_page = paginate.page
    #总页数
    total_page = paginate.pages

    items_list = []
    for item in items:
        items_list.append(item.to_admin_dict())
    data={
         "users":items_list,
         "current_page":current_page,
         "total_page":total_page
     }
    return render_template("admin/user_list.html",data=data)

"""
用户统计
"""
@admin_blue.route("/user_count")
def user_count():
    # 总人数
    total_count = 0
    # 每个月人数
    mon_count = 0
    # 每天增加的人数
    day_count = 0
    # 获取总人数
    total_count = User.query.filter(User.is_admin == False).count()
    # 当前日期时间
    # 2018-08-01 00:00:00
    t = time.localtime()
    # 获取当月的第一天的2018-08-01
    mon_begin = "%d-%02d-01" % (t.tm_year, t.tm_mon)
    # 这个是获取当月的第一天的2018-08-01 00:00:00
    mon_begin_date = datetime.strptime(mon_begin, "%Y-%m-%d")

    # 获取到本月人数
    mon_count = User.query.filter(User.is_admin == False, User.create_time >= mon_begin_date).count()

    # 这个是当月当前的时间
    t = time.localtime()
    day_begin = "%d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday)
    day_begin_date = datetime.strptime(day_begin, "%Y-%m-%d")
    # 获取今天人数
    day_count = User.query.filter(User.is_admin == False, User.create_time >= day_begin_date).count()

    #获取31天活跃用户数量，
    #获取当前时间
    t = time.localtime()
    #获取到今天的日期
    today_begin = "%d-%02d-%02d"%(t.tm_year,t.tm_mon,t.tm_mday)
    # 这个是吧今天的时间，后面加上零点零时00:00:00
    today_begin_date = datetime.strptime(today_begin,"%Y-%m-%d")
    #活跃用户
    active_count = []
    #时间列表
    active_time = []
    for i in range(0,30):
        #获取今天的开始时间
        begin_date = today_begin_date - timedelta(days=i)
        #获取今天结束时间,
        end_date = today_begin_date-timedelta(days=(i-1))
        #获取今天人数
        count = User.query.filter(User.is_admin == False,User.create_time>=begin_date,User.create_time<end_date).count()
        active_count.append(count)
        active_time.append(begin_date.strftime("%Y-%m-%d"))

    #吧数据顺序反转
    active_time.reverse()
    active_count.reverse()


    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_time":active_time,
        "active_count":active_count
    }

    return render_template("admin/user_count.html", data=data)


"""
主页
"""


@admin_blue.route("/index")
@user_login_data
def admin_index():
    user = g.user

    return render_template("admin/index.html", user=user.to_dict())

"""
登陆
"""
@admin_blue.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        #先要获取数据，
        user_id = session.get("user_id",None)
        is_admin = session.get("is_admin",False)
        #判断。如果用户已经登陆了，那么就不需要每次登陆，就直接跳转到首页
        if user_id and is_admin:
            return redirect(url_for("admin.admin_index"))
        return render_template("admin/login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    user = User.query.filter(User.mobile == username, User.is_admin == True).first()
    if not user:
        return render_template("admin/login.html", errmsg="没有这个用户")
    if not user.check_password(password):
        return render_template("admin/login.html", errmsg="密码错误")

    session["user_id"] = user.id
    session["nice_name"] = user.nick_name
    session["mobile"] = user.mobile
    session["is_admin"] = user.is_admin
    # 登陆成功，回调到主页面
    return redirect(url_for("admin.admin_index"))

from flask import current_app
from flask import request, jsonify

from infor import db
from infor.utils.response_code import RET
from . import user_blue
from flask import render_template, g, redirect
from infor.utils.common import user_login_data
from infor.utils.image_storage import storage
from infor import constants
from infor.models import Category, News, User

@user_blue.route("/other_news_list")
def other_news_list():
    page = request.args.get("p",1)
    user_id = request.args.get("user_id")
    try:
        page= int(page)
    except Exception as e:

        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    user = User.query.get(user_id)
    paginate = News.query.filter(News.user_id==user.id).paginate(page,2,False)
    #当前页面数据
    news_li = paginate.items

    current_page = paginate.page
    total_page = paginate.pages

    news_dict_li=[]
    for news_item in news_li:
        news_dict_li.append(news_item.to_review_dict())
    data={
        "news_list":news_dict_li,
        "current_page":current_page,
        "total_page":total_page
    }
    return jsonify(errno=RET.OK,errmsg="ok",data=data)




"""
关注的作者信息
"""
@user_blue.route("/other_info")
@user_login_data
def other_info():
    user = g.user

    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg="请登陆")
    #获取作者id
    other_id = request.args.get("id")
    #查询到作者
    other = User.query.get(other_id)

    #表示我关注了哪些人，默认情况，第一次进来，我们是没有关注的
    is_followed = False
    #我想关注别人，新闻必须由作者
    if other and user:
        if other in user.followed:
            is_followed = True

    data={
        "user_info":user.to_dict(),
        "other_info":other.to_dict(),
        "is_followed":is_followed
    }
    return render_template("news/other.html",data=data)

"""
用户的关注
"""
@user_blue.route("/follow")
@user_login_data
def follow():
    page = request.args.get("p",1)
    user = g.user
    try:
        page = int(page)
    except Exception as e:
        page = 1
    paginate = user.followed.paginate(page,4,False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages
    items_list=[]
    for item in items:
        items_list.append(item.to_dict())
    data = {
        "users":items_list,
        "current_page":current_page,
        "total_page":total_page
    }
    return render_template("news/user_follow.html",data=data)
"""
用户新闻列表
"""


@user_blue.route("/news_list")
@user_login_data
def news_list():
    user = g.user
    page = request.args.get("p", 1)

    try:
        page = int(page)
    except Exception as e:
        page = 1

    paginate = News.query.filter(News.user_id == user.id).paginate(page, 2, False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    items_list = []
    for item in items:
        items_list.append(item.to_review_dict())

    data = {
        "news_list": items_list,
        "current_page": current_page,
        "total_page": total_page
    }
    return render_template("news/user_news_list.html", data=data)


"""
用户发布新闻
"""


@user_blue.route("/news_release", methods=["GET", "POST"])
@user_login_data
def news_release():
    user = g.user
    if request.method == "GET":
        categorys = Category.query.all()
        category_list = []
        for category in categorys:
            category_list.append(category.to_dict())
        category_list.pop(0)
        data = {
            "categories": category_list
        }
        return render_template("news/user_news_release.html", data=data)
    # 新闻标题
    title = request.form.get("title")
    # 新闻分类id
    category_id = request.form.get("category_id")
    # 新闻摘要
    digest = request.form.get("digest")
    # 所以图片
    index_image = request.files.get("index_image").read()
    # 新闻内容
    content = request.form.get("content")
    # 发布种类，是个人还别的
    source = "个人发布"
    if not all([title, category_id, digest, index_image, content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
    key = storage(index_image)

    news = News()

    news.title = title
    # 新闻来源
    news.source = source
    news.category_id = category_id
    # 新闻摘要
    news.digest = digest
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
    news.content = content
    news.user_id = user.id
    news.status = 1

    db.session.add(news)
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="发布成功")
    # return render_template("news/user_news_list.html",errno=RET.OK, errmsg="发布成功")

"""
新闻收藏
"""


@user_blue.route("/collection", methods=["GET", "POST"])
@user_login_data
def collection():
    user = g.user

    # 收藏是分页的，先获取页数,默认是第一页
    page = request.args.get("p", 1)

    try:
        page = int(page)
    except Exception as e:
        page = 1
    # paginate()这个是分页功能，第一个参数是在哪个页面，第二个参数是每页的收藏数量，第三个参数是是否警告，一般就False
    paginate = user.collection_news.paginate(page, 3, False)
    # 获取当前页面内容
    items = paginate.items
    # 获取当前页数
    current_page = paginate.page
    # 获取总页数
    total_page = paginate.pages
    items_list = []
    for item in items:
        items_list.append(item.to_dict())

    data = {
        "collections": items_list,
        "current_page": current_page,
        "total_page": total_page
    }
    return render_template("news/user_collection.html", data=data)


"""
修改密码
"""


@user_blue.route("/pass_info", methods=["GET", "POST"])
@user_login_data
def pass_info():
    user = g.user
    if request.method == "GET":
        data = {
            "user_info": user.to_dict() if user else None
        }

        return render_template("news/user_pass_info.html", data=data)
    # 获取前端反馈的旧密码
    old_password = request.json.get("old_password")
    # 获取前端填写的新密码
    new_password = request.json.get("new_password")
    if not user.check_password(old_password):
        return jsonify(errno=RET.PWDERR, errmsg="密码错误")
    user.password = new_password
    db.session.commit()

    return jsonify(errno=RET.OK, errmsg="修改成功")


"""
用户上传头像
"""


@user_blue.route("/pic_info", methods=["GET", "POST"])
@user_login_data
def pic_info():
    user = g.user
    if request.method == "GET":
        data = {
            "user_info": user.to_dict() if user else None
        }

        return render_template("news/user_pic_info.html", data=data)
    # 获取传过来的头像参数
    avatar = request.files.get("avatar").read()
    # 变成七牛的key
    key = storage(avatar)

    user.avatar_url = key
    db.session.commit()
    data = {
        "avatar_url": constants.QINIU_DOMIN_PREFIX + key
    }
    return jsonify(errno=RET.OK, errmsg="上传成功", data=data)


"""
个人中心的基本资料
"""


@user_blue.route("/base_info", methods=["GET", "POST"])
@user_login_data
def base_info():
    user = g.user
    if request.method == "GET":
        data = {
            "user_info": user.to_dict() if user else None
        }

        return render_template("news/user_base_info.html", data=data)
    # 昵称
    nick_name = request.json.get("nick_name")
    # 签名
    signature = request.json.get("signature")
    # 性别
    gender = request.json.get("gender")
    if not all([nick_name, signature, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg="请填写数据")

    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender

    db.session.commit()

    from flask import session
    # 吧个性签名保存到session里面
    # session["nick_name"] = nick_name
    return jsonify(errno=RET.OK, errmsg="ok")


"""
个人中心主页
"""


@user_blue.route("/info")
@user_login_data
def get_user_info():
    user = g.user
    if not user:
        return redirect("/")
    data = {
        "user_info": user.to_dict() if user else None
    }

    return render_template("news/user.html", data=data)

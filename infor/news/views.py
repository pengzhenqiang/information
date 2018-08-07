from flask import request, jsonify
from flask import session
from flask import g

from infor import db
from infor.models import User, News, Comment, CommentLike
from infor.utils.response_code import RET
from . import news_blue
from flask import render_template
from infor.utils.common import user_login_data

"""
关注作者,这个是逻辑，吧关注数据保存到
"""
@news_blue.route("/followed_user",methods=["GET","POST"])
@user_login_data
def followed_user():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg="请登陆")
    #我关注的那个人的id
    user_id = request.json.get("user_id")
    #有关注和取消关注
    action =request.json.get("action")
    """
    关注和取消关注，
    1，必须是用户行为
    2，根据我关注的那个人id，查询出我需要关注的那个人信息
    3，判断当前动作是关注还是取消关注
    """
    other = User.query.get(user_id)

    if action == "follow":
        #关注
        #如果是关注动作，说明我之前没有关注，如果之前关注了，就提示已经关注了
        if other not in user.followed:
            user.followed.append(other)
        else:
            return jsonify(errno=RET.PARAMERR,errmsg="已经关注了")

    else:
        if other in user.followed:
            user.followed.remove(other)

        else:
            return jsonify(errno=RET.PARAMERR,errmsg="没有关注")

    db.session.commit()

    return jsonify(errno=RET.OK,errmsg="ok")



"""
评论点赞
"""


@news_blue.route("/comment_like", methods=["GET","POST"])
@user_login_data
def comment_like():
    # 所有的点赞操作都是基于评论的，所以需要评论
    # 所有的点赞操作都是基于用户行为的，所以需要登陆
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="请登陆")
    # 评论的ID
    comment_id = request.json.get("comment_id")
    # 新闻id
    news_id = request.json.get("news_id")
    # 点赞操作类型add点赞，remove取消点赞
    action = request.json.get("action")

    """
    评论点赞，我们需要根据评论id查询出评论，是因为点赞操作基于评论
    我们的点赞也需要基于当前新闻，所以需要查询出当前新闻
    """
    # 查询评论
    comment = Comment.query.get(comment_id)

    if action == "add":
        # 如果是add说明需要点赞，
        # 如果之前没有点赞，那么点击一下就可以，由点赞了，就不用点击
        # 这个是查处前端反馈的评论id和用户是否在这个评论里面点赞了
        comment_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                                CommentLike.user_id == user.id).first()

        # 判断查询出来的点赞是否有值，没有的时候才可以点赞
        if not comment_like:
            comment_like = CommentLike()
            comment_like.comment_id = comment_id
            comment_like.user_id = user.id
            db.session.add(comment_like)
            comment.like_count += 1

    else:
        # 就取消点赞
        # 如果是add操作,说明想进行点赞
        # 如果之前没有点赞,那么点击一下就可以进行点赞,如果之前已经点赞了,那么我们就不能点赞
        # 如果已经点赞了，那么在点，就会取消点赞
        comment_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                                CommentLike.user_id == user.id).first()
        if comment_like:
            db.session.delete(comment_like)
            comment.like_count -= 1

    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="点赞成功")

"""
新闻评论
"""


@news_blue.route("/news_comment", methods=["GET", "POST"])
@user_login_data
def news_comment():

    user = g.user
    # 获取前端传过来的新闻ID
    news_id = request.json.get("news_id")


    # 获取评论内容
    comment_str = request.json.get("comment")
    # 回复评论的ID
    parent_id = request.json.get("parent_id")
    """
    用户评论
    用户如果在登录的情况下，可以进行评论，未登录，点击评论弹出登录框
    用户可以直接评论当前新闻，也可以回复别人发的评论
     1:用户必须先登陆才能进行评论，如果不登陆，直接返回
     2:如果需要评论，那么就需要知道当前评论的是哪条新闻，如果想知道是哪条 新闻，那么就可以通过news_id 查询出来新闻
    3:如果评论成功之后，那么我们需要把用户的评论信息存储到数据库，为了方 便下次用户在进来的时候可以看到评论

    """

    # 获取新闻
    news = News.query.get(news_id)

    print(news)

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="请登陆")
    # 新闻评论是一个用户行为，所以需要用户登陆

    # 新闻评论，实际是吧评论内容添加数据库
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news.id
    comment.content = comment_str

    # 因为不可能所有的评论都有父评论,所以在赋值的时候,需要判断
    if parent_id:
        comment.parent_id = parent_id
    db.session.add(comment)
    # db.session.add(comment)
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="评论成功", data=comment.to_dict())


"""
新闻收藏
"""


@news_blue.route("/news_collect", methods=["GET", "POST"])
@user_login_data
def new_collect():
    user = g.user
    # 因为骁yao勇收藏新闻，所以骁yao勇获取新闻的id
    news_id = request.json.get("news_id")
    # 我们需要收藏新闻，如果不把动作告诉我们，我们不知道是收藏还是取消
    action = request.json.get("action")

    """
     新闻收藏：     
    １：我们必须得知道，当前用户收藏的是哪条新闻，如果想知道用户收藏的是哪条 新闻，那么直接通过news_id进行查询
    2:如果想收藏新闻，那么用户必须登陆，所以判断用户是否已经登陆就可以
    3:判断用户的动作，到底是想收藏，还是想取消收藏
    4:如果用户是收藏新闻的动作，那么直接把新闻丢到用户的收藏列表当中

    """

    # 因为需要收藏新闻，肯定要吧新闻弄出来
    news = News.query.get(news_id)

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="没有这条新闻")

    # 收藏是用户行为，所以必须判断当前用户是否登陆了，登陆才能收藏

    if not user:
        return jsonify(errno=RET.NODATA, errmsg="没有登陆用户")

    if action == "collect":
        # 说明想收藏
        user.collection_news.append(news)
    else:
        # 说明需要取消收藏
        user.collection_news.remove(news)

    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="收藏成功")


@news_blue.route("/<int:news_id>")
# 装饰器方法引入user
@user_login_data
def news_detail(news_id):
    # 引入user用户，可以用调用函数，也可以y用装饰器
    user = g.user
    # user = user_login_data()

    # 获取新闻详情内容
    news = News.query.get(news_id)
    """
    新闻收藏：
    1，通过一个变量进行控制是否已经收藏，is_collected = True,表示收藏了 is_collected=False表示没有收藏
    2，如果需要收藏新闻，那么收藏新闻是一个用户的动作，必须用户登陆才行
    如果user有值，哪就说明客户登陆了
    3，判断当前是否由这条新闻，如果由新闻才能收藏，没有新闻，肯定收藏不了
    4，判断当前的这条新闻是否在我的收藏的新闻列表中，如果在就是被收藏了，如果被收藏了，那么我们就
    可以is_collected = True
    """
    # 默认进来是没有收藏的，
    is_collected = False
    if user:
        if news in user.collection_news:
            is_collected = True

    # 新闻的右侧排行榜
    news_model = News.query.order_by(News.clicks.desc()).limit(10)
    news_list = []
    for news_dict in news_model:
        news_list.append(news_dict.to_dict())

    """
    获取新闻列表，
    1 :我们需要查询新闻评论表，在查询的时候，直接通过新闻id就可以查询，因为 所有的评论都是针对新闻产生
    """
    comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    comment_list = []
    comment_like_ids= []
    comment_likes = []

    if user:
        #取出所有的用户点过的赞
        comment_likes = CommentLike.query.filter(CommentLike.user_id==user.id)
        #取出点过的赞里面的所有comment_id
        comment_like_ids = [comment_like.comment_id for comment_like in comment_likes]


    for comment in comments:
        #取出评论的字典
        comment_dict = comment.to_dict()
        #第一次进来，肯定所有评论都没点赞
        comment_dict["is_like"] = False
        if comment.id in comment_like_ids:
            comment_dict["is_like"] = True
        comment_list.append(comment.to_dict())

    #表示我关注了哪些人，默认情况下，第一次进来，我们谁都没关注，所以设置成false
    #必须登陆，判断user是否有值
    #必须有作者，因为如果是爬虫爬过来的数据，那么就没有新闻作者
    #如果当前新闻有作者，并且在我关注的人的列表里面，就说明我是新闻作者的粉丝，所以设置true
    #用is_followed来判断是否关注过作者
    # 当前登陆的用户，是否关注新闻作者
    #这个是关注的展示
    is_followed = False

    if user:
        if news.user in user.followed:
            is_followed = True


    data = {
        "user_info": user.to_dict() if user else None,
        "news": news.to_dict(),
        "click_news_list": news_list,
        "is_collected": is_collected,
        "comments": comment_list,
        "is_followed":is_followed
    }

    return render_template("news/detail.html", data=data)

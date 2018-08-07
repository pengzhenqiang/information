# 自定义过滤器
from flask import session

from infor.models import User
from flask import g
import functools


def do_index_claas(index):
    if index == 0:
        return "first"
    elif index == 1:
        return "second"
    elif index == 2:
        return "third"
    else:
        return ""


# 定义装饰器
# 第一种方法
def user_login_data(f):
    # 封装的内容
    # 这个是为了能让user返回出来
    @functools.wraps(f)
    def wrapper(*args,**kwargs):
        """
                        判断当前的用户是否登陆成功
                        """
        # 因为在登陆的时候,我们把数据存储到session里面,所以从session里面获取到当前登陆的用户
        user_id = session.get("user_id")
        user = None
        # 判断是否登陆了，用来查看是哪个用户
        if user_id:
            # 通过user_id查询是否有当前这个用户
            user = User.query.get(user_id)

        g.user = user

        return f(*args,**kwargs)

    return wrapper

# 第二种方法
# def user_login_data():
#     """
#     #                         判断当前的用户是否登陆成功
#     #                         """
#     #         # 因为在登陆的时候,我们把数据存储到session里面,所以从session里面获取到当前登陆的用户
#     user_id = session.get("user_id")
#     user = None
#     # 判断是否登陆了，用来查看是哪个用户
#     if user_id:
#         # 通过user_id查询是否有当前这个用户
#         user = User.query.get(user_id)
#
#     return user

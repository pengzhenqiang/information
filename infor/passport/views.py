from datetime import datetime
import random
import re
from flask import request,make_response,current_app
from flask import jsonify

from flask import session
from infor.models import User
from infor.passport import passport_blue
from infor.utils.captcha.captcha import captcha
from infor import redis_store
from infor.utils.response_code import RET
from infor import constants
from infor.libs.yuntongxun.sms import CCP
from infor import db

"""
退出
"""
@passport_blue.route("/logout")
def logout():
    """
    退出就是清楚之前保存的登陆信息
    :return:
    """
    # session.pop()删除
    session.pop("user_id",None)
    session.pop("nick_name",None)
    session.pop("mobile",None)
    session.pop("is_admin",None)

    return jsonify(errno=RET.OK,errmsg="成功退出")


"""
用户登陆
"""
@passport_blue.route("/login",methods = ["GET","POST"])
def login():
    # 获取客户端输入的号码
    mobile = request.json.get("mobile")
    # 获取输入的密码
    password = request.json.get("password")
    # 后续要核实密码和账户
    try:
        # 通过电话号码，查找这个用户
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        # 吧错误信息存储到log日志
        current_app.logger.error(e)


    #判断用户是否由
    #
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="请注册")
    # 通过系统源码判断密码是否正确
    if not user.check_password(password):
        return jsonify(errno=RET.PWDERR,errmsg="密码错误")
    # 对用户进行状态保持,跟网易新闻一样,session进行实现,保持用户信息到session里面
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    # 更新登陆时间
    user.last_login = datetime.now()
#     吧数据存储到数据库
    db.session.commit()

    return jsonify(errno=RET.OK,errmsg="登陆成功")


"""
用户注册
"""
@passport_blue.route("/register",methods = ["GET","POST"])
def register():
    # 获取手机号码
    mobile = request.json.get("mobile")
    # 用户在客户端输入的验证码
    smscode = request.json.get("smscode")
    # 用户在里面输入的密码
    password = request.json.get("password")
    # 获取系统里面存储的短信验证码
    real_sms_code = redis_store.get("sms_code_"+mobile)

    if not real_sms_code:
        return jsonify(errno=RET.NODATA,errmsg = "短信验证码已经过期")

    if smscode != real_sms_code:
        return jsonify(errno =RET.PARAMERR,errmsg="请输入正确的短信验证码")
    # 创建一个用户对象用来注册用户
    user = User()
    user.mobile = mobile
    user.password = password
    user.nick_name = mobile
    # 获取当前的时间，用来注册
    user.last_login = datetime.now()

    db.session.add(user)
    db.session.commit()
    return jsonify(errno=RET.OK,errmsg="注册成功")


"""
短信验证：
发送短信实现流程
    接收前端发送过来的请求参数
    检查参数是否已经全部传过来
    判断手机号码是否正确
    检查图片验证码是否正确，若不正确则返回
    生成随机短信验证码
    使用第三方SDK发送短信
"""
@passport_blue.route("/sms_code",methods = ["GET","POST"])
def sms_code():
    # 手机号
    mobile = request.json.get("mobile")
    # 用户输入的图片验证码内容
    image_code = request.json.get("image_code")
    # 真实图片验证码编号
    image_code_id = request.json.get("image_code_id")
    # 检查传递过来的参数是否全部有值
    if not all([mobile,image_code,image_code_id]):
        return jsonify(errno = RET.PARAMERR,errmsg = "请输入参数")
    if not re.match(r"1[3456789]\d{9}",mobile):
        return jsonify(errno = RET.PARAMERR,errmsg = "请输入正确号码")
    #获取到redis里面的图片验证码
    real_image_code = redis_store.get("image_id_"+image_code_id)
    # 判断验证码是否过期，过期了就拿不到，就是空的
    if not real_image_code:
        return jsonify(errno = RET.NODATA,errmsg="图片验证码过期了")
    # 如果没过期，判断用户输入的验证码，转换成小写的进行判断用lower()
    if image_code.lower() != real_image_code.lower():
        return jsonify(errno=RET.PARAMERR,errmsg="请输入正确验证码")
    # 通过随机生成一个六位数的验证码，用占位符%d
    random_sms_code = "%06d" %random.randint(0,999999)
    # 在服务器的redis里面存储短信验证码，用来给用户进行检验操作
    # 第一个参数，是电话号码作为key，
    # 第二个参数是短信验证码
    # 第三个参数是有效时间
    redis_store.set("sms_code_"+mobile,random_sms_code,constants.SMS_CODE_REDIS_EXPIRES)

    print("短信验证码内容="+random_sms_code)
    # 发送短信

    statuCode = CCP().send_template_sms(mobile,[random_sms_code,5],1)
    if statuCode != 0:
        return jsonify(errno = RET.THIRDERR,errmsg ="短信发送失败")

    return jsonify(errno=RET.OK,errmsg="发送短信成功")



@passport_blue.route("/image_code")
def image_code():
    print("q前段请求的url地址="+ request.url)
    #获取前段传递过来的一个验证码
    code_id = request.args.get("code_id")
    # name 图片验证码的名字
    # text 表示图片验证码内容
    # image表示图片
    #生成图片验证
    name,text,image = captcha.generate_captcha()
    print("图片验证内容="+ text)
    # 第一个参数是存储才key
    # 第二个参数是存储的验证内容
    # 第三个参数是有效期限
    redis_store.set("image_id_"+code_id,text,5000)
    # make_response表示响应体对象，这个对象参数表示图片
    # 返回给页面的响应提是验证图片
    resp = make_response(image)
    # 告诉系统我们当前展示的是图片
    resp.headers['Content-Type'] = 'image/jpg'

    return resp
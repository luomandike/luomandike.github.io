# ====================图形验证码
# 1.引入第三方包，用于绘制图形验证码
# 2.调用包中的函数，生成验证码文本、图片数据
# 3.接收客户端的唯一标识，将验证码文本保存到redis中
# 4.将图片数据构造响应对象，返回给浏览器
import re, random

from flask import current_app
from flask import make_response, jsonify
from flask import request
from flask import session

from info.models import User
from info.response_code import RET
from . import passport_blueprint
# 1.引入第三方包，用于绘制图形验证码
from libs.captcha.captcha import captcha
from info import redis_store, db
from info import constants

@passport_blueprint.route('/image_code')
def image_code():
    code_id = request.args.get("code_id")
    # 2.调用包中的函数，生成验证码文本、图片数据
    text, code, image = captcha.generate_captcha()
    # 3.接收客户端的唯一标识，将验证码文本保存到redis中
    redis_store.setex(code_id, constants.IMAGE_CODE_REDIS_EXPIRES, code)
    # 4.将图片数据构造响应对象，返回给浏览器
    response = make_response(image)
    response.headers["Content-Type"] = "image/png"
    return response

# ====================短信验证码
@passport_blueprint.route('/sms_code', methods=['POST'])
def sms_code():
    # 1.接收
    # 	手机号
    # 	图形验证码
    # 	图形唯一标识
    mobile = request.json.get("mobile")
    image_code = request.json.get("image_code")
    image_code_id = request.json.get("image_code_id")
    # 2.验证
    # 	图形验证码是否正确
    # 	手机号格式
    # 	手机号是否存在
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.NODATA, errmsg="数据错误。")
    redis_image = redis_store.get(image_code_id).decode()
    if redis_image != image_code:
        return jsonify(errno=RET.NODATA, errmsg="验证码错误。")
    re_mobile = re.match(r"1[35678]\d{9}", mobile)
    if not re_mobile:
        return jsonify(errno=RET.NODATA, errmsg="请输入正确的手机号。")
    user = User()
    mobile_flag = user.query.filter_by(mobile=mobile).first()
    if mobile_flag:
        return jsonify(errno=RET.NODATA, errmsg="手机号已经存在，请登录。")
    # user.
    # 3.处理
    # 	生成6位随机数
    # 	发短信
    # 	保存到redis
    random_num = random.randint(100000, 999999)
    # 	发短信...........

    redis_store.setex(mobile, constants.SMS_CODE_REDIS_EXPIRES, random_num)
    return jsonify(errno=RET.OK, errmsg="")


# ====================注册

@passport_blueprint.route('/register', methods=['POST'])
def register():
    # 1.接收：手机号、短信验证码、密码
    mobile = request.json.get("mobile")
    smscode = request.json.get("smscode")
    password = request.json.get("password")
    # 2.验证：非空，短信验证码
    if not all([mobile, smscode, password]):
        return jsonify(errno=RET.NODATA, errmsg="数据错误。")
    redis_sms_code = redis_store.get(mobile).decode()
    if redis_sms_code != smscode:
        return jsonify(errno=RET.NODATA, errmsg="短信验证码错误或失效。")
    user = User()
    user.nick_name = mobile
    user.mobile = mobile
    user.password = password
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as result:
        db.session.rollback()
        current_app.logger.error(result)
        return jsonify(errno=RET.NODATA, errmsg="数据库保存失败。")


    # 3.处理：新建User对象，属性赋值，保存
    # 4.响应：返回json
    return jsonify(errno=RET.OK, errmsg="")

# ====================登录
# 业务逻辑：根据手机号与密码，到用户表中查询数据，如果查到则成功，否则失败

@passport_blueprint.route('/login', methods=['POST'])
def login():
    # 1.接收：手机号，密码
    mobile = request.json.get("mobile")
    password = request.json.get("password")
    # 2.验证：正则表达式验证
    re_mobile = re.match(r"1[35678]\d{9}", mobile)
    if not re_mobile:
        return jsonify(errno=RET.NODATA, errmsg="请输入正确的手机号。")
    # user = User()
    # 3.处理：查询
    mysql_data = User.query.filter_by(mobile=mobile).first()
    if not mysql_data:
        return jsonify(errno=RET.NODATA, errmsg="此手机号未注册。")
    if not mysql_data.check_password(password):
        return jsonify(errno=RET.NODATA, errmsg="密码错误。")
    # 4.响应：json
    session["user_id"] = mysql_data.id
    session["nick_name"] = mysql_data.nick_name
    # session["mobile"] = user.mobile
    return jsonify(errno=RET.OK, errmsg="")

@passport_blueprint.route('/logout', methods=['POST'])
def logout():
    session.pop("user_id")
    session.pop("nick_name")
    return jsonify(errno=RET.OK, errmsg="")









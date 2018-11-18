import logging
import os
from logging.handlers import RotatingFileHandler

from flask import render_template,g

from info.config import config_dict
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect
from flask_session import Session

db = SQLAlchemy()

redis_store = None


def setup_log(config_name):
    """配置日志"""
    dir_file=os.path.abspath(__file__)
    dir_info=os.path.dirname(dir_file)
    dir_base=os.path.dirname(dir_info)
    dir_log=os.path.join(dir_base,'logs/log')

    # 设置日志的记录等级
    logging.basicConfig(level=config_dict[config_name].LOG_LEVEL)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler(dir_log, maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_str):
    app = Flask(__name__)

    # 根据参数，从字典中获取类，加载配置
    app.config.from_object(config_dict[config_str])
    # 启动日志
    setup_log(config_str)
    # 初始化mysql数据库连接
    db.init_app(app)
    # 初始化redis数据库连接
    global redis_store
    redis_store = StrictRedis(
        host=app.config.get("REDIS_HOST"),
        port=app.config.get("REDIS_PORT"),
        db=app.config.get("REDIS_DB")
    )
    # CSRF保存
    # CSRFProtect(app)
    # 使用redis保存session
    Session(app)
    # 注册蓝图
    from info.modules.index.views import index_blueprint
    app.register_blueprint(index_blueprint)
    # 注册passport
    from info.modules.passport.views import passport_blueprint
    app.register_blueprint(passport_blueprint)
    # 注册新闻页面
    from info.modules.news.views import news_blueprint
    app.register_blueprint(news_blueprint)

    # 注册个人中心
    from info.modules.profile.views import profile_blueprint
    app.register_blueprint(profile_blueprint)

    # 注册404
    from info.modules.utils.common import login_wraps
    @app.errorhandler(404)
    @login_wraps
    def error_404(e):
        user = g.user
        if user is None:
            user = None
        else:
            user = user.to_login_dict()
        data = {
            "user": user
        }
        return render_template("news/404.html", data=data)

    # 返回app
    return app





from flask import current_app
from flask import g, jsonify
from flask import request

from info import constants
from info import db
from info.models import User, News
from info.modules.utils.image_store import storage
from info.response_code import RET
from . import profile_blueprint
from flask import render_template
from info.modules.utils.common import login_wraps

@profile_blueprint.route('/info')
@login_wraps
def info():
    data = {
        "user":g.user.to_login_dict() if g.user else None
    }
    return render_template("news/user.html", data=data)

@profile_blueprint.route('/user_base_info', methods=['GET', 'POST'])
@login_wraps
def user_base_info():
    if request.method == "GET":
        data = {
            "user": g.user.to_login_dict()
        }
        return render_template("news/user_base_info.html", data=data)
    signature = request.json.get("signature")
    nick_name = request.json.get("nick_name")
    gender = request.json.get("gender")
    user = g.user
    user.gender = gender
    user.signature = signature
    user.nick_name = nick_name
    db.session.commit()

    return jsonify(errno=RET.OK, errmsg="完成。")


@profile_blueprint.route('/user_pic_info', methods=['GET', 'POST'])
@login_wraps
def user_pic_info():
    if request.method == "GET":
        data = {
            "user": g.user.to_login_dict()
        }
        return render_template("news/user_pic_info.html", data=data)
    file = request.files.get("avatar")
    try:
        image_url = storage(file.read())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(error=RET.THIRDERR, errmsg="七牛连接失败")
    g.user.avatar_url = image_url
    db.session.commit()
    data = {
        "user":g.user.to_login_dict()
    }
    return jsonify(errno=RET.OK, errmsg="成功", data=data)

@profile_blueprint.route('/user_follow')
@login_wraps
def user_follow():
    try:
        page = int(request.args.get("page", 1))
    except Exception as e:
        page = 1
    try:
        pagination = g.user.authors.order_by(User.id.desc()).paginate(page, constants.USER_FOLLOWED_MAX_COUNT, False)
        data = {
            "author_list": [author.to_dict() for author in pagination.items],
            'page':page,
            'total_pages':pagination.pages
        }
    except Exception as e:
        data = {
            "author_list": [],
            'page': 1,
            'total_pages': 0
        }
    return render_template("news/user_follow.html", data=data)


# @profile_blueprint.route('/followed_user', methods=['POST'])
# @login_wraps
# def followed_user():
#     action = request.json.get("action")
#     author_id = request.json.get("user_id")
#     if not all([action, author_id]):
#         return jsonify(error=RET.DATAERR, errmsg="非法的请求。")
#     if action not in ["follow", "unfollow"]:
#         return jsonify(error=RET.DATAERR, errmsg="非法的请求。")
#     user = g.user
#     author = User.query.get(author_id)
#     if action == "unfollow":
#         user.authors.append(author)
#     else:
#         user.authors.remove(author)
#     db.session.commit()
#     return jsonify(errno=RET.OK, errmsg='')


@profile_blueprint.route('/user_pass_info', methods=['GET', 'POST'])
@login_wraps
def user_pass_info():
    if request.method == "GET":
        return render_template("news/user_pass_info.html")
    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")
    new_password2 = request.json.get("new_password2")
    if not all([old_password, new_password, new_password2]):
        return jsonify(error=RET.DATAERR, errmsg="非法的请求。")
    if new_password != new_password2 or old_password == new_password:
        return jsonify(error=RET.DATAERR, errmsg="请确认要修改的密码。")
    status = g.user.check_password(old_password)
    if not status:
        return jsonify(error=RET.DATAERR, errmsg="请确认原始密码。")
    g.user.password = new_password
    db.session.commit()
    new_status = g.user.check_password(new_password)
    if not new_status:
        return jsonify(error=RET.DBERR, errmsg="更新密码失败。")
    return jsonify(error=RET.OK, errmsg="成功。")


@profile_blueprint.route('/user_collection')
@login_wraps
def user_collection():
    page = request.args.get("page", 1)
    pagination = g.user.collection_news.order_by(News.id.desc()).\
                 paginate(int(page), constants.HOME_PAGE_MAX_NEWS, False)
    news_list = pagination.items
    news_info = [news.to_index_dict() for news in news_list]
    data = {
        "total_pages": pagination.pages,
        "page":page,
        "news_info": news_info
    }
    return render_template("news/user_collection.html", data=data)


@profile_blueprint.route('/user_news_release', methods=['GET', 'POST'])
@login_wraps
def user_news_release():
    if request.method == "GET":
        return render_template("news/user_news_release.html")

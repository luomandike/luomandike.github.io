from flask import current_app
from flask import render_template, g, jsonify
from flask import request

from info import constants
from info import db
from info.models import News,Comment, CommentLike, User
from info.modules.utils.common import login_wraps
from info.response_code import RET
from . import news_blueprint



@news_blueprint.route('/<int:news_id>')
@login_wraps
def detail(news_id):

    news = News.query.get_or_404(news_id)
    news.clicks += 1
    db.session.commit()
    # 点击排行
    news_rank_list1 = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    news_rank_list2 = [news_rank_list.to_click_dict() for news_rank_list in news_rank_list1]
    # 查询当前新闻是否被当前用户收藏
    if g.user and news in g.user.collection_news:
        is_collected = True
    else:
        is_collected = False

    comment_list1 = news.comments.filter_by(parent_id=None).order_by(Comment.id.desc())
    comment_list2 = [comment.to_dict() for comment in comment_list1]
    comment_count = len(comment_list2)

    if not (g.user is None):
        comment_ids = [comment.id for comment in comment_list1]
        likes = CommentLike.query. \
            filter_by(user_id=g.user.id). \
            filter(CommentLike.comment_id.in_(comment_ids))
        likes_ids = [like.comment_id for like in likes]
        for comment in comment_list2:
            comment['is_like'] = comment.get('id') in likes_ids
    if g.user:
        is_follow = g.user.authors.filter_by(id=news.user_id).all()
    else:
        is_follow = None
    if is_follow:
        is_follow = True
    else:
        is_follow = False
    data = {
        "user":g.user.to_login_dict() if g.user else None,
        "news":news,
        "is_collected":is_collected,
        'news_list': news_rank_list2,
        "comment_count":comment_count,
        "comment_list": comment_list2,
        "is_follow": is_follow
    }
    return render_template("news/detail.html", data=data)


@news_blueprint.route('/news_collect', methods=["POST"])
@login_wraps
def news_collect():
    news_id = request.json.get("news_id")
    action = request.json.get("action")
    if not all([news_id, action]):
        return  jsonify(errno=RET.DATAERR, errmsg="数据错误。")
    news = News.query.get(news_id)
    if not news:
        return jsonify(errno=RET.DATAERR, errmsg="数据错误。")
    if action not in ('collect', 'cancel_collect'):
        return jsonify(errno=RET.DATAERR, errmsg="数据错误。")
    if g.user is None:
        return jsonify(errno=RET.DATAERR, errmsg="用户未登录。")
    user = g.user
    if action == "collect":
        try:
            user.collection_news.append(news)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DATAERR, errmsg="数据库连接错误。")
    else:
        try:
            user.collection_news.remove(news)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DATAERR, errmsg="数据库连接错误。")
    db.session.commit()
    return jsonify(errno=RET.OK, error="连接成功。")


@news_blueprint.route('/news_comment', methods=['POST'])
@login_wraps
def news_comment():
    news_id = request.json.get("news_id")
    comment = request.json.get("comment")
    user = g.user
    if user is None:
        return jsonify(errno=RET.DATAERR, errmsg="请先登录")
    else:
        user = user.to_login_dict()
    if not all([news_id, comment]):
        return jsonify(errno=RET.DATAERR, errmsg="请求数据错误")
    news = News.query.get(news_id)
    if not news:
        return jsonify(errno=RET.DATAERR, errmsg="无对应新闻错误")
    comment_class = Comment()
    comment_class.news_id = news_id
    comment_class.user_id = user.get("id")
    comment_class.content = comment
    db.session.add(comment_class)
    db.session.commit()
    data = comment_class.to_dict()
    return jsonify(errno=RET.OK, errmsg="操作成功", data=data)


@news_blueprint.route('/comment_add', methods=['POST'])
@login_wraps
def comment_add():
    news_id = request.json.get("news_id")
    msg = request.json.get("comment")
    parent_id = request.json.get("parent_id")
    user = g.user
    if user is None:
        return jsonify(errno=RET.DATAERR, errmsg="请登录。")
    else:
        user = user.to_login_dict()
    if not all([news_id, msg, parent_id]):
        return jsonify(errno=RET.DATAERR, errmsg="请求数据错误")
    news = News.query.get(news_id)
    if not news:
        return jsonify(errno=RET.DATAERR, errmsg="无对应新闻id")
    comment = Comment()
    comment.news_id = int(news_id)
    comment.user_id = int(user.get("id"))
    comment.content = msg
    comment.parent_id = int(parent_id)
    db.session.add(comment)
    db.session.commit()
    backdata = {
        "user": user.get("nick_name"),
        "back": msg
    }
    return jsonify(errno=RET.OK, errmsg="请求成功。", backdata=backdata)


@news_blueprint.route('/comment_like', methods=['POST'])
@login_wraps
def comment_like():
    comment_id = request.json.get("comment_id")
    action = request.json.get("action")

    user = g.user
    if user is None:
        return jsonify(errno=RET.DATAERR, errmsg="请登录。")
    else:
        user = user.to_login_dict()
    if (not all([comment_id, action])) or (action not in ["add", "remove"]) :
        return jsonify(errno=RET.DATAERR, errmsg="请求数据错误")
    if action == "add":
        commentlike = CommentLike()
        commentlike.comment_id = int(comment_id)
        commentlike.user_id = int(user.get("id"))
        db.session.add(commentlike)
        db.session.commit()
        comment_like_count = Comment.query.get(commentlike.comment_id)
        comment_like_count.like_count += 1
        db.session.commit()
    else:
        commentlike = CommentLike.query.filter_by(comment_id=comment_id,user_id=user.get("id")).first()

        db.session.delete(commentlike)
        db.session.commit()
        comment_like_count = Comment.query.get(commentlike.comment_id)
        comment_like_count.like_count -= 1
        db.session.commit()

    return jsonify(errno=RET.OK, errmsg="请求成功。")


@news_blueprint.route('/followed_user', methods=['POST'])
@login_wraps
def followed_user():
    action = request.json.get("action")
    author_id = request.json.get("user_id")
    if not all([action, author_id]):
        return jsonify(error=RET.DATAERR, errmsg="非法的请求。")
    if action not in ["follow", "unfollow"]:
        return jsonify(error=RET.DATAERR, errmsg="非法的请求。")
    user = g.user
    if user is None:
        return jsonify(error=RET.DATAERR, errmsg="请登录。")
    author = User.query.get(author_id)
    if action == "follow":
        user.authors.append(author)
    else:
        user.authors.remove(author)
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg='')
    pass


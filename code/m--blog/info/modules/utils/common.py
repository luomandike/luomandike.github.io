import functools

from flask import redirect
from flask import request
from flask import session, g
from flask import url_for

from info import constants
from info.models import User, News


def get_click_rank():
    rang_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    rank_list = [rank.to_rank_dict() for rank in rang_list]
    return rank_list


def login_wraps(view):
    @functools.wraps(view)
    def func(*args, **kwargs):
        if "user_id" in session:
            g.user = User.query.get(session.get('user_id'))
        else:
            g.user = None
            if request.path.startswith("/profile"):
                return redirect(url_for("index.index"))
        return view(*args, **kwargs)
    return func


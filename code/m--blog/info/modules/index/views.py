from flask import request, jsonify, g
from flask import session

from info import constants
from info.models import User, Category, News
from info.modules.utils.common import login_wraps
from info.response_code import RET
from . import index_blueprint
from flask import render_template

@index_blueprint.route("/")
@login_wraps
def index():
    user = g.user
    if user is None:
        user = None
    else:
        user = user.to_login_dict()
    # 分类信息
    category_list1 = Category.query.all()
    category_list2 = [category_.to_dict() for category_ in category_list1]
    # 点击排行
    news_rank_list1 = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    news_rank_list2 = [news_rank_list.to_click_dict() for news_rank_list in news_rank_list1]

    data = {
        "user":user,
        'category_list': category_list2,
        'news_list': news_rank_list2
    }
    return render_template("news/index.html", data=data)

@index_blueprint.route('/newslist')
def newslist():
    # 接收
    cid = request.args.get("cid")
    page = request.args.get("page")
    per_page = request.args.get("per_page")
    # 验证
    if not all([cid, page, per_page]):
        return jsonify(errno=RET.NODATA, errmsg="数据不能为空。")
    # 处理
    pagination = News.query
    # if cid != "0":
    #     pagination = pagination.filter_by(category_id=cid)
    # pagination = pagination.order_by(News.id.desc()).paginate(int(cid), int(page), False)
    if int(cid) != 0:
        pagination = pagination.filter_by(category_id=cid)
    pagination = pagination.order_by(News.id.desc()). \
        paginate(int(page), int(per_page), False)
    # 获取当前页的数据
    page_list1 = pagination.items
    # 获取总页数
    total_page = pagination.pages
    news_dict_list = [temp.to_index_dict() for temp in page_list1]
    # 响应
    data = {
        'errno': RET.OK,
        'errmg': '',
        'cid': cid,
        'current_page': page,
        'totalPage': total_page,
        'newsList': news_dict_list
    }
    return jsonify(data)

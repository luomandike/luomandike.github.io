function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(function () {

    $(".base_info").submit(function (e) {
        e.preventDefault()

        var signature = $("#signature").val()
        var nick_name = $("#nick_name").val()
        // var gender = $("#").val()
        var gender = $('input:radio[name="gender"]:checked').val();

        if ((!nick_name) || (!signature)) {
            alert('昵称或签名不允许为空。')
            return
        }
        if (!gender) {
            alert('请选择性别')
        }
        var params = {
                "signature": signature,
                "nick_name": nick_name,
                "gender": gender
            }
        // TODO 修改用户信息接口
        $.ajax({
            url:"/profile/user_base_info",
            type:"post",
            contentType:"application/json",
            headers: {
                    "X-CSRFToken": getCookie("csrf_token")
                },
            data:JSON.stringify(params),
            success:function (resp) {
                if (resp.errno == "0") {
                    alert('修改成功');
                    // 更新父窗口内容
                    $('.user_center_name', parent.document).html("用户:" + params['nick_name'])
                    $('.user_login>a', parent.document).first().html(params['nick_name'])
                    $('.input_sub').blur()
                } else {
                    alert(resp.errmsg)
                }
            }
        })
    })
})
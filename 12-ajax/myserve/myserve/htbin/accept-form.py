from cgikits import *

resp = """Content-Type: text/html

<html lang="en">
<head>
    <meta charset="GBK">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <script src="https://cdn.bootcss.com/jquery/3.2.1/jquery.js"></script>    
    <title>潭州Python服务器</title>
</head>
<body>
    是否是GET请求： {isget} <br>
    是否是POST请求：{ispost} <br>
    是否是AJAX: {isajax} <br>
    GET表单数据： {getdata} <br>
    POST表单数据： {postdata} <br>
    <a href="/htdocs/send-form.html">回到表单</a>
</body>
</html>
"""

isget = is_get()  #判断是不是GET请求
ispost = is_post()  #判断是不是POST请求
isajax = is_xhr()   #判断是不是AJAX请求
getdata = get_form() #返回GET表单数据
postdata = post_form() #返回POST表单数据


print(resp.format(isget=isget,  
                  ispost=ispost,
                  isajax=isajax,
                  getdata=getdata,
                  postdata=postdata))

介绍
欢迎使用今日热榜官方 API 服务。

今日热榜是全网最全面的热榜聚合平台，汇集了各大网站的热榜信息，包括微信、今日头条、百度、知乎、V2EX、微博、贴吧、豆瓣、天涯、虎扑、Github、抖音等，基本囊括所有中文互联网平台榜单。使用今日热榜提供的 API，可快速接入热榜数据，助力追踪全网热点。

入门
本文档描述了构成官方 今日热榜 JSON API 的资源。

如果您有任何问题或请求，请联系我们的 API 团队。

创建帐户
要访问 今日热榜 API，请首先注册加入.

指南和条款
要使用 API，您必须遵守隐私政策条款并遵循用户协议。

全局说明
通用请求
请求域名
https://api.tophubdata.com/
用户认证
请通过 HTTP 授权标头 HEADER 传递应用程序的访问密钥：Authorization: YOUR_ACCESS_KEY

请务必保存好自己的密钥，你可以通过在后台设置中心设置白名单IP来限制请求服务器来源（默认关闭）。

参数名	必选	类型	说明	示例值
Authorization	是	string	用户密钥	e5ff6cf3a14e1c72deefe8a512469af6
错误码
错误码及描述

错误码	描述	说明
200	Success	成功
100101	InvalidParams	缺少参数或无效的参数
100201	Unauthorized	未授权Authorization错误
100202	IpRestricted	请求 IP 受限，检查白名单
100300	InsufficientFunds	账户余额不足
100500	InternalError	内部错误
开放接口
全部榜单列表
描述
获得今日热榜全站全部榜单列表。

地址
https://api.tophubdata.com/nodes
方法
GET

参数
参数名	必选	类型	说明	示例值
p	否	int	翻页页码，每页100条	1
可以递归查询，当返回的条数 <100 的时候中断递归，=100 的时候 p++ 来实现自动翻页获取所有节点。

cURL 请求示例
curl --location 'https://api.tophubdata.com/nodes?p=1' --header 'Authorization: YOUR_ACCESS_KEY'
可以复制上面示例到 Postman 这类型调试工具直接运行。

返回示例
  {
    "error":false,
    "status":200
    "data": [
        {
            "hashid": "KqndgxeLl9",
            "name": "微博",
            "display": "热搜榜",
            "domain": "weibo.com",
            "logo": "********",
            "cid": "1"
        },
        {
            "hashid": "mproPpoq6O",
            "name": "知乎",
            "display": "热榜",
            "domain": "zhihu.com",
            "logo": "********",
            "cid": "1"
        }
        ...
    ]
  }
返回参数说明
参数名	类型	说明	示例值
hashid	varchar	榜单hashid	mproPpoq6O（注意 hashid 严格区分大小写）
name	varchar	网站名称	知乎
display	varchar	内容类型	热榜
domain	varchar	域名	zhihu.com
logo	varchar	图标	**
cid	varchar	int	分类id
分类 cid 对应的类型
英文分类	中文分类	编号
news	综合	1
tech	科技	2
ent	娱乐	3
community	社区	4
shopping	购物	5
finance	财经	6
developer	开发者	7
university	大学	8
organization	政务	9
blog	博客专栏	10
wxmp	微信公众号	11
epaper	电子报	12
design	设计	13
other	其他	0
widget	小工具	-1
提醒：榜单 hashid 是固定不变并且唯一的。并且和今日热榜官网（ https://tophub.today/ ）是保持一致的。例如：https://tophub.today/n/mproPpoq6O URL上面对应的 mproPpoq6O 即为知乎热榜的 hashid。

单个榜单最新详细
描述
获得指定榜单的最新榜单或最新更新的内容列表。数据排序即为最新榜单排序。本接口一次性返回最新榜单全部内容，不用翻页。

地址
https://api.tophubdata.com/nodes/@hashid
@hashid 为全部榜单列表获取到的 hashid，注意 hashid 严格区分大小写。

方法
GET

cURL 请求示例
curl --location 'https://api.tophubdata.com/nodes/mproPpoq6O' --header 'Authorization: YOUR_ACCESS_KEY'
可以复制上面示例到 Postman 这类型调试工具直接运行。

返回示例
  {
    "error":false,
    "status":200
    "data": {
        "hashid": "mproPpoq6O",
        "name": "知乎",
        "display": "热榜",
        "domain": "zhihu.com",
        "logo": "********",
        "items": [
            {
                "extra": "455 万热度",
                "url": "https://www.zhihu.com/question/629047878",
                "thumbnail": "https://pica.zhimg.com/80/v2-00a693d9ac81c601223512d5725cbacd_1440w.png",
                "description": "美联储加息周期终于似要走到尽头了。 ",
                "title": "美元大跳水，10 年期美债收益率大跌，离岸人民币大涨 400 点，美股五连阳，美联储加息周期到头了吗？"
            },
            {
                "extra": "206 万热度",
                "url": "https://www.zhihu.com/question/621684259",
                "thumbnail": "https://pic3.zhimg.com/50/v2-0e599dcb44ad61215462fdfbb58d983e_qhd.jpg",
                "description": "感觉老一辈的亲戚总是不知道一些边界感，每次都无下限的打探我的个人问题和生活，弄得我非常的不适。要怎么样才能有礼貌的进行回应呢？",
                "title": "过节聚餐时总感到亲戚在惯性「侵犯」我的边界，是我太敏感还是「亲戚PTSD」在作祟？"
            }
            ...
        ]
    }
  }
返回参数说明
参数名	类型	说明
hashid	varchar	榜单节点 Hashid
name	varchar	网站名称
display	varchar	内容类型
domain	varchar	域名
logo	varchar	图标
items/title	varchar	标题
items/description	varchar	描叙
items/thumbnail	varchar	缩略图
items/url	varchar	地址
items/extra	unknown	附加内容，可能是任意格式内容
单个榜单历史数据集
描述
获得榜单指定日期当天上榜的所有历史数据集，需要指定日期，一次性返回当天所有上榜数据，排序为上榜时间从先到后，本接口仅用来获取今天以前的历史日期数据，不返回当天数据。本接口一次性返回当天所有内容，不用翻页。

地址
https://api.tophubdata.com/nodes/@hashid/historys
@hashid 为全部榜单列表获取到的 hashid，注意 hashid 严格区分大小写。

方法
GET

参数
参数名	必选	类型	说明	示例值
date	是	String	日期Y-m-d	2023-01-01
cURL 请求示例
curl --location 'https://api.tophubdata.com/nodes/mproPpoq6O/historys?date=2023-11-04' --header 'Authorization: YOUR_ACCESS_KEY'
可以复制上面示例到 Postman 这类型调试工具直接运行。

返回示例
  {
    "error":false,
    "status":200
    "data": [
        {
            "extra": "455 万热度",
            "url": "https://www.zhihu.com/question/629047878",
            "thumbnail": "https://pica.zhimg.com/80/v2-00a693d9ac81c601223512d5725cbacd_1440w.png",
            "description": "美联储加息周期终于似要走到尽头了。 ",
            "title": "美元大跳水，10 年期美债收益率大跌，离岸人民币大涨 400 点，美股五连阳，美联储加息周期到头了吗？",
            "time" : 1699095601
        },
        {
            "extra": "206 万热度",
            "url": "https://www.zhihu.com/question/621684259",
            "thumbnail": "https://pic3.zhimg.com/50/v2-0e599dcb44ad61215462fdfbb58d983e_qhd.jpg",
            "description": "感觉老一辈的亲戚总是不知道一些边界感，每次都无下限的打探我的个人问题和生活，弄得我非常的不适。要怎么样才能有礼貌的进行回应呢？",
            "title": "过节聚餐时总感到亲戚在惯性「侵犯」我的边界，是我太敏感还是「亲戚PTSD」在作祟？",
            "time" : 1699095601
        }
        ...
    ]
  }
返回参数说明
参数名	类型	说明
title	varchar	标题
description	varchar	描叙
thumbnail	varchar	缩略图
url	varchar	地址
extra	unknown	附加内容，可能是任意格式内容
time	int	10位时间戳(上榜时间)
全网热点内容搜索
描述
搜索全站热点或者指定榜单节点内容。

地址
https://api.tophubdata.com/search
方法
GET

参数
参数名	必选	类型	说明	示例值
q	是	String	关键词	苹果
hashid	否	String	搜索限定节点 hashid	mproPpoq6O
p	否	Int	当前页码（每页最多返回50条，默认1）	1
cURL 请求示例
curl --location 'https://api.tophubdata.com/search?q=Apple&hashid=mproPpoq6O&p=1' --header 'Authorization: YOUR_ACCESS_KEY'
可以复制上面示例到 Postman 这类型调试工具直接运行。

返回示例
  {
    "error":false,
    "status":200
    "data": {
        "p": 1,
        "pagesize": 50,
        "totalpage": 2,
        "totalsize": 99,
        "items": [
            {
                "extra": "455 万热度",
                "url": "https://www.zhihu.com/question/629047878",
                "thumbnail": "https://pica.zhimg.com/80/v2-00a693d9ac81c601223512d5725cbacd_1440w.png",
                "description": "美联储加息周期终于似要走到尽头了。 ",
                "title": "美元大跳水，10 年期美债收益率大跌，离岸人民币大涨 400 点，美股五连阳，美联储加息周期到头了吗？",
                "time" : 1699095601
            },
            {
                "extra": "206 万热度",
                "url": "https://www.zhihu.com/question/621684259",
                "thumbnail": "https://pic3.zhimg.com/50/v2-0e599dcb44ad61215462fdfbb58d983e_qhd.jpg",
                "description": "感觉老一辈的亲戚总是不知道一些边界感，每次都无下限的打探我的个人问题和生活，弄得我非常的不适。要怎么样才能有礼貌的进行回应呢？",
                "title": "过节聚餐时总感到亲戚在惯性「侵犯」我的边界，是我太敏感还是「亲戚PTSD」在作祟？",
                "time" : 1699095601
            }
            ...
        ]
    }
  }
返回参数说明
参数名	类型	说明
p	int	当前页码
totalsize	int	总匹配数
pagesize	int	每页返回记录数
totalpage	int	总页数
items/title	varchar	标题
items/description	varchar	描叙
items/thumbnail	varchar	缩略图
items/url	varchar	地址
items/extra	unknown	附加内容，可能是任意格式内容
items/time	int	时间戳
今日热榜榜中榜
描述
获取今日热榜网站实时榜中榜内容，需要指定日期，默认当天，一次性返回当天上榜数据TOP100，不用翻页。当天数据会随时变化，历史日期数据是不变的。

地址
https://api.tophubdata.com/hot
方法
GET

参数
参数名	必选	类型	说明	示例值
date	是	String	日期Y-m-d	2023-01-01
cURL 请求示例
curl --location 'https://api.tophubdata.com/hot?date=2023-11-04' --header 'Authorization: YOUR_ACCESS_KEY'
可以复制上面示例到 Postman 这类型调试工具直接运行。

返回示例
  {
    "error":false,
    "status":200
    "data": [
        {
          "title": "报告称一包烟 0.5 元的烟叶 9 元的税，利润率超六成，烟农毛收入 0.45 元，哪些信息值得关注？",
          "description": "吸烟者每吸一包烟，平均消费0.52元的烟叶，为烟草行业职工发了0.87元工资，为国家缴了9.05元的税。有学者建议到2030年烟草制品应提税至78％。 在中国，吸烟者每吸一包烟，平均消费0.52元的烟叶，为烟草行业职工发了0.87元工资，为国家缴了9.05元的税，也即一包烟的税占比为48.4％。 近日，对外经济贸易大学世界卫生组织烟草控制与经济政策合作中心发布《烟草消费税改革暨烟草行业全产业链研究》（下称“报告”）显示，2020年一包卷烟加权平均的零售价格为18.69元，并进一步剖析了一包卷烟在产业链各环",
          "thumbnail": "https://pic3.zhimg.com/80/v2-f33a654b841726108d6e67af33f80c9c_720w.webp",
          "url": "https://www.zhihu.com/question/628926775",
          "time": "1699026261",
          "domain": "zhihu.com",
          "sitename": "知乎",
          "logo": "https://file.ibmwclub.com/tophub/assets/images/media/zhihu.com.png",
          "views": "2749 万热度"
        },
        ...
        {
          "title": "北大宿舍聊天 婚姻残酷真相",
          "description": "",
          "thumbnail": "",
          "url": "https://s.weibo.com/weibo?q=%E5%8C%97%E5%A4%A7%E5%AE%BF%E8%88%8D%E8%81%8A%E5%A4%A9+%E5%A9%9A%E5%A7%BB%E6%AE%8B%E9%85%B7%E7%9C%9F%E7%9B%B8",
          "time": "1699083604",
          "domain": "s.weibo.com",
          "sitename": "微博",
          "logo": "https://file.ibmwclub.com/tophub/assets/images/media/s.weibo.com.png",
          "views": "740 万热度"
        }
        ...
    ]
  }
返回参数说明
参数名	类型	说明
title	varchar	标题
description	varchar	描叙
thumbnail	varchar	缩略图
url	varchar	地址
time	int	10位时间戳(上榜时间)
domain	varchar	来源网站域名
sitename	varchar	来源网站名称
logo	varchar	LOGO地址
views	varchar	热度值
单个榜单快照列表
描述
获取指定榜单某天的所有快照列表，支持两种模式：

仅获取快照列表（默认，免费）：返回当天所有快照的 ID 和时间戳信息
获取快照详细内容（收费）：一次性返回当天所有快照的完整数据，按快照数量计费
注意：只有榜单类的节点才有快照。

地址
https://api.tophubdata.com/nodes/@hashid/snapshots
@hashid 为全部榜单列表获取到的 hashid，注意 hashid 严格区分大小写。

方法
GET

参数
参数名	必选	类型	说明	示例值
date	否	String	日期Y-m-d（默认当天）	2025-11-11
details	否	Int	是否获取详细内容，默认=0，0=仅列表（免费），1=包含详细内容（收费）	0 或 1
计费说明
仅获取快照列表（details=0 或不传）：免费
获取快照详细内容（details=1）：按快照数量计费，1u/个快照。例如当天有20个快照，则消耗20u
cURL 请求示例
仅获取快照列表（免费）

curl --location 'https://api.tophubdata.com/nodes/mproPpoq6O/snapshots?date=2025-11-11' --header 'Authorization: YOUR_ACCESS_KEY'
获取快照详细内容（收费）

curl --location 'https://api.tophubdata.com/nodes/mproPpoq6O/snapshots?date=2025-11-11&details=1' --header 'Authorization: YOUR_ACCESS_KEY'
可以复制上面示例到 Postman 这类型调试工具直接运行。

返回示例
仅获取快照列表（details=0）

  {
    "error":false,
    "status":200,
    "data": [
        {
            "ssid": 12345,
            "timestamp": 1699095601
        },
        {
            "ssid": 12346,
            "timestamp": 1699099201
        }
        ...
    ]
  }
获取快照详细内容（details=1）

  {
    "error":false,
    "status":200,
    "data": [
        {
            "ssid": 12345,
            "timestamp": 1699095601,
            "items": [
                {
                    "title": "美元大跳水，10 年期美债收益率大跌",
                    "description": "美联储加息周期终于似要走到尽头了。",
                    "thumbnail": "https://pica.zhimg.com/80/v2-00a693d9ac81c601223512d5725cbacd_1440w.png",
                    "url": "https://www.zhihu.com/question/629047878",
                    "extra": "455 万热度"
                }
                ...
            ]
        },
        {
            "ssid": 12346,
            "timestamp": 1699099201,
            "items": [
                {
                    "title": "过节聚餐时总感到亲戚在惯性「侵犯」我的边界",
                    "description": "感觉老一辈的亲戚总是不知道一些边界感...",
                    "thumbnail": "https://pic3.zhimg.com/50/v2-0e599dcb44ad61215462fdfbb58d983e_qhd.jpg",
                    "url": "https://www.zhihu.com/question/621684259",
                    "extra": "206 万热度"
                }
                ...
            ]
        }
        ...
    ]
  }
返回参数说明
仅获取快照列表时：

参数名	类型	说明
ssid	int	快照ID
timestamp	int	10位时间戳（快照时间）
获取快照详细内容时：

参数名	类型	说明
ssid	int	快照ID
timestamp	int	10位时间戳（快照时间）
items	array	快照内容列表
items/title	varchar	标题
items/description	varchar	描述
items/thumbnail	varchar	缩略图
items/url	varchar	地址
items/extra	unknown	附加内容
单个榜单快照详情
描述
根据快照 ID 获取指定快照的详细内容，包含该快照时刻的完整榜单数据。需要先通过快照列表接口获取 ssid，然后使用此接口查询快照详情。

地址
https://api.tophubdata.com/nodes/@hashid/snapshots/@ssid
@hashid 为全部榜单列表获取到的 hashid，@ssid 为快照列表接口返回的快照 ID。

方法
GET

参数
无需额外参数。

cURL 请求示例
curl --location 'https://api.tophubdata.com/nodes/mproPpoq6O/snapshots/12345' --header 'Authorization: YOUR_ACCESS_KEY'
可以复制上面示例到 Postman 这类型调试工具直接运行。

返回示例
  {
    "error":false,
    "status":200
    "data": {
        "ssid": 12345,
        "timestamp": 1699095601,
        "items": [
            {
                "title": "美元大跳水，10 年期美债收益率大跌，离岸人民币大涨 400 点，美股五连阳，美联储加息周期到头了吗？",
                "description": "美联储加息周期终于似要走到尽头了。",
                "thumbnail": "https://pica.zhimg.com/80/v2-00a693d9ac81c601223512d5725cbacd_1440w.png",
                "url": "https://www.zhihu.com/question/629047878",
                "extra": "455 万热度"
            },
            {
                "title": "过节聚餐时总感到亲戚在惯性「侵犯」我的边界，是我太敏感还是「亲戚PTSD」在作祟？",
                "description": "感觉老一辈的亲戚总是不知道一些边界感，每次都无下限的打探我的个人问题和生活，弄得我非常的不适。要怎么样才能有礼貌的进行回应呢？",
                "thumbnail": "https://pic3.zhimg.com/50/v2-0e599dcb44ad61215462fdfbb58d983e_qhd.jpg",
                "url": "https://www.zhihu.com/question/621684259",
                "extra": "206 万热度"
            }
            ...
        ]
    }
  }
返回参数说明
参数名	类型	说明
ssid	int	快照ID
timestamp	int	10位时间戳（快照时间）
items/title	varchar	标题
items/description	varchar	描叙
items/thumbnail	varchar	缩略图
items/url	varchar	地址
items/extra	unknown	附加内容，可能是任意格式内容
热点日历事件
描述
获取指定日期范围内的日历事件数据，支持按天、按周、按月查询，支持按分类筛选。本接口采用分级计费模式，不同查询模式费用不同。支持节气、农历节日、公历节日、纪念日、颁奖典礼、影视上映、重要事件、大型展会、互联网热点营销热点案例集锦。

地址
https://api.tophubdata.com/calendar/events
方法
GET

参数
参数名	必选	类型	说明	示例值
mode	否	String	查询模式：day(按天)、week(按周)、month(按月)，默认day	day
date	否	String	日期Y-m-d，默认当天	2023-11-04
categories	否	String	分类ID，多个用逗号分隔，all表示全部，默认all	1,2,3 或 all
分类说明
分类ID	分类名称	说明
1	节气	二十四节气
2	公历节日	公历节日
3	农历节日	农历节日
4	国际节日	国际节日
5	纪念日	各类纪念日
6	颁奖典礼	各类颁奖典礼
7	影视上映	影视作品上映
8	互联网科技	互联网科技事件
9	展会活动	各类展会活动
10	品牌日	品牌营销日
20	佛历	佛教历法
21	道历	道教历法
22	回历	伊斯兰历法
23	天象历	天文现象
24	跨境日历	跨境电商日历
25	物候	物候现象
计费说明
不同查询模式费用不同：

按天查询（day）：20u/次
按周查询（week）：100u/次
按月查询（month）：300u/次
cURL 请求示例
按天查询

curl --location 'https://api.tophubdata.com/calendar/events?mode=day&date=2023-11-04&categories=all' --header 'Authorization: YOUR_ACCESS_KEY'
按周查询指定分类

curl --location 'https://api.tophubdata.com/calendar/events?mode=week&date=2023-11-04&categories=1,2,3' --header 'Authorization: YOUR_ACCESS_KEY'
按月查询

curl --location 'https://api.tophubdata.com/calendar/events?mode=month&date=2023-11-04&categories=all' --header 'Authorization: YOUR_ACCESS_KEY'
可以复制上面示例到 Postman 这类型调试工具直接运行。

返回示例
  {
    "error":false,
    "status":200,
    "data": {
        "mode": "week",
        "start": "2023-10-30",
        "end": "2023-11-05",
        "categories": "1,2,3",
        "count": 15,
        "events": [
            {
                "cid": 1,
                "start": "2023-11-04",
                "end": "2023-11-04",
                "title": "立冬",
                "description": "二十四节气之一"
            },
            {
                "cid": 2,
                "start": "2023-11-01",
                "end": "2023-11-01",
                "title": "万圣节",
                "description": "西方传统节日"
            },
            {
                "cid": 3,
                "start": "2023-11-03",
                "end": "2023-11-03",
                "title": "寒衣节",
                "description": "农历十月初一"
            }
            ...
        ]
    }
  }
返回参数说明
参数名	类型	说明
mode	string	查询模式
start	string	开始日期
end	string	结束日期
categories	string	查询的分类
count	int	事件总数
events/cid	int	分类ID
events/start	string	事件开始日期
events/end	string	事件结束日期
events/title	string	事件标题
events/description	string	事件描述（可选）
注意事项
按周查询时，会自动计算指定日期所在周的周一到周日
按月查询时，会自动计算指定日期所在月的第一天到最后一天
categories 参数支持多个分类ID，用英文逗号分隔，如：1,2,3
categories 设置为 all 时，返回所有分类的事件
实时回调
Webhook 回调
当我们的系统更新某个网站的榜单时，我们会立即向您指定的 URL 发送一个回调，包含最新的榜单内容。

通过这种方式，您可以实时获取最新的数据，确保您获得的数据与我们的系统高度同步，而且不会遗漏任何信息。

Webhook 通知向您指定的 URL 发送 HTTP POST 请求。请求消息主体是序列化的 JSON 字符串，采用application/json请求头。

请求 POST JSON 数据示例
  {
      "hashid": "mproPpoq6O",
      "name": "知乎",
      "display": "热榜",
      "domain": "zhihu.com",
      "logo": "********",
      "items": [
          {
              "extra": "455 万热度",
              "url": "https://www.zhihu.com/question/629047878",
              "thumbnail": "https://pica.zhimg.com/80/v2-00a693d9ac81c601223512d5725cbacd_1440w.png",
              "description": "美联储加息周期终于似要走到尽头了。 ",
              "title": "美元大跳水，10 年期美债收益率大跌，离岸人民币大涨 400 点，美股五连阳，美联储加息周期到头了吗？"
          },
          {
              "extra": "206 万热度",
              "url": "https://www.zhihu.com/question/621684259",
              "thumbnail": "https://pic3.zhimg.com/50/v2-0e599dcb44ad61215462fdfbb58d983e_qhd.jpg",
              "description": "感觉老一辈的亲戚总是不知道一些边界感，每次都无下限的打探我的个人问题和生活，弄得我非常的不适。要怎么样才能有礼貌的进行回应呢？",
              "title": "过节聚餐时总感到亲戚在惯性「侵犯」我的边界，是我太敏感还是「亲戚PTSD」在作祟？"
          }
          ...
      ]
  }
您的URL应在几秒钟内响应 2xx 状态代码，否则可能会重试 Webhook。对于失败的响应，我们在2分钟内会尝试重试3次（间隔30s），不会无限制重试，请确保响应 URL 一直处于无阻塞状态。

值得注意的是，这个功能仅对我们的大客户开放，以确保服务的质量和效率。您无需逐个调用接口获取数据，而是通过回调即可获得所需的信息。


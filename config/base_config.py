

# 基础配置
PLATFORM = "xhs"
KEYWORDS = "八卦"  # 关键词搜索配置，以英文逗号分隔
LOGIN_TYPE = "cookie"  # qrcode or phone or cookie
COOKIES = "acw_tc=0a00db0d17513719218264585e0b4c07e158404dc2abc331adcaf998e07b0c; abRequestId=6cff03d0-75a6-5690-9c39-09fae5cc097d"
# 具体值参见media_platform.xxx.field下的枚举值，暂时只支持小红书
SORT_TYPE = "popularity_descending"
# 具体值参见media_platform.xxx.field下的枚举值，暂时只支持抖音
PUBLISH_TIME_TYPE = 0
CRAWLER_TYPE = (
    "creator"  # 爬取类型，search(关键词搜索) | detail(帖子详情)| creator(创作者主页数据)
)
# 自定义User Agent（暂时仅对XHS有效）
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0'

# 是否开启 IP 代理 - 暂时启用代理试试看能否解决SSL问题
ENABLE_IP_PROXY = False

# 未启用代理时的最大爬取间隔，单位秒（暂时仅对XHS有效）- 增加间隔避免被限制
CRAWLER_MAX_SLEEP_SEC = 10

# 代理IP池数量
IP_PROXY_POOL_COUNT = 2

# 代理IP提供商名称
IP_PROXY_PROVIDER_NAME = "kuaidaili"

# 设置为True不会打开浏览器（无头浏览器）
# 设置False会打开一个浏览器
# 小红书如果一直扫码登录不通过，打开浏览器手动过一下滑动验证码
# 抖音如果一直提示失败，打开浏览器看下是否扫码登录之后出现了手机号验证，如果出现了手动过一下再试。
HEADLESS = False

# 是否保存登录状态
SAVE_LOGIN_STATE = True

# ==================== CDP (Chrome DevTools Protocol) 配置 ====================
# 是否启用CDP模式 - 使用用户现有的Chrome/Edge浏览器进行爬取，提供更好的反检测能力
# 启用后将自动检测并启动用户的Chrome/Edge浏览器，通过CDP协议进行控制
# 这种方式使用真实的浏览器环境，包括用户的扩展、Cookie和设置，大大降低被检测的风险
# 暂时关闭CDP模式，使用标准模式进行调试
ENABLE_CDP_MODE = False

# CDP调试端口，用于与浏览器通信
# 如果端口被占用，系统会自动尝试下一个可用端口
CDP_DEBUG_PORT = 9222

# 自定义浏览器路径（可选）
# 如果为空，系统会自动检测Chrome/Edge的安装路径
# Windows示例: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
# macOS示例: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CUSTOM_BROWSER_PATH = ""

# CDP模式下是否启用无头模式
# 注意：即使设置为True，某些反检测功能在无头模式下可能效果不佳
CDP_HEADLESS = False

# 浏览器启动超时时间（秒）- 增加超时时间到2分钟
BROWSER_LAUNCH_TIMEOUT = 120

# 是否在程序结束时自动关闭浏览器
# 设置为False可以保持浏览器运行，便于调试
AUTO_CLOSE_BROWSER = True

# 数据保存类型选项配置,支持三种类型：csv、db、json, 最好保存到DB，有排重的功能。
SAVE_DATA_OPTION = "db"  # csv or db or json

# 用户浏览器缓存的浏览器文件配置
USER_DATA_DIR = "%s_user_data_dir"  # %s will be replaced by platform name

# 爬取开始页数 默认从第一页开始
START_PAGE = 1

# 爬取视频/帖子的数量控制 - 减少数量，先测试基本功能
CRAWLER_MAX_NOTES_COUNT = 10

# 并发爬虫数量控制 - 保持单线程，避免过快触发限制
MAX_CONCURRENCY_NUM = 1

# 是否开启爬图片模式, 默认不开启爬图片
ENABLE_GET_IMAGES = False

# 是否开启爬评论模式, 默认开启爬评论
ENABLE_GET_COMMENTS = True

# 爬取一级评论的数量控制(单视频/帖子) - 减少数量，先测试基本功能
CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = 20

# 是否开启爬二级评论模式, 默认不开启爬二级评论
# 老版本项目使用了 db, 则需参考 schema/tables.sql line 287 增加表字段
# 暂时关闭二级评论，先确保一级评论正常工作
ENABLE_GET_SUB_COMMENTS = False

# 已废弃⚠️⚠️⚠️指定小红书需要爬虫的笔记ID列表
# 已废弃⚠️⚠️⚠️ 指定笔记ID笔记列表会因为缺少xsec_token和xsec_source参数导致爬取失败
# XHS_SPECIFIED_ID_LIST = [
#     "66fad51c000000001b0224b8",
#     # ........................
# ]

# 指定小红书需要爬虫的笔记URL列表, 目前要携带xsec_token和xsec_source参数
XHS_SPECIFIED_NOTE_URL_LIST = [
    "https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8?xsec_token=AB3rO-QopW5sgrJ41GwN01WCXh6yWPxjSoFI9D5JIMgKw=&xsec_source=pc_search"
    # ........................
]

# 指定小红书创作者ID列表 - 爬取指定用户的所有帖子
# 用户ID可以从小红书用户主页URL中获取，例如：
# https://www.xiaohongshu.com/user/profile/5ff0e6410000000001005f1a
# 其中 5ff0e6410000000001005f1a 就是用户ID
XHS_CREATOR_ID_LIST = [
    "momo",  # 示例用户ID，请替换为你要爬取的实际用户ID
    # "另一个用户ID",  # 可以添加多个用户ID
    # "第三个用户ID",
]

# 词云相关
# 是否开启生成评论词云图
ENABLE_GET_WORDCLOUD = True
# 自定义词语及其分组
# 添加规则：xx:yy 其中xx为自定义添加的词组，yy为将xx该词组分到的组名。
CUSTOM_WORDS = {
    "零几": "年份",  # 将“零几”识别为一个整体
    "高频词": "专业术语",  # 示例自定义词
}

# 停用(禁用)词文件路径
STOP_WORDS_FILE = "./docs/hit_stopwords.txt"

# 中文字体文件路径
FONT_PATH = "./docs/STZHONGS.TTF"

# 爬取creator粉丝列表时起始爬取页数
START_CONTACTS_PAGE = 1

# 爬取作者粉丝和关注列表数量控制(单作者)
CRAWLER_MAX_CONTACTS_COUNT_SINGLENOTES = 100

# 爬取作者动态数量控制(单作者) - 增加数量以获取更多帖子
CRAWLER_MAX_DYNAMICS_COUNT_SINGLENOTES = 100
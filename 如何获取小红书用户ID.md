# 如何获取小红书用户ID

## 方法一：从用户主页URL获取

1. **打开小红书网页版**：https://www.xiaohongshu.com
2. **搜索并进入目标用户主页**
3. **查看浏览器地址栏**，URL格式如下：
   ```
   https://www.xiaohongshu.com/user/profile/5ff0e6410000000001005f1a
   ```
4. **提取用户ID**：URL中 `/user/profile/` 后面的字符串就是用户ID
   - 例如：`5ff0e6410000000001005f1a`

## 方法二：从手机分享链接获取

1. **在小红书APP中打开用户主页**
2. **点击分享按钮**，选择"复制链接"
3. **分享链接格式**通常为：
   ```
   https://www.xiaohongshu.com/user/profile/5ff0e6410000000001005f1a?xhsshare=xxx
   ```
4. **提取用户ID**：`/user/profile/` 后面 `?` 前面的部分

## 配置步骤

1. **修改爬取类型**：
   ```python
   CRAWLER_TYPE = "creator"
   ```

2. **添加用户ID到配置文件**：
   ```python
   XHS_CREATOR_ID_LIST = [
       "5ff0e6410000000001005f1a",  # 替换为实际的用户ID
       "另一个用户ID",              # 可以添加多个用户
   ]
   ```

3. **调整爬取数量**（可选）：
   ```python
   # 每个用户最多爬取的帖子数量
   CRAWLER_MAX_DYNAMICS_COUNT_SINGLENOTES = 100
   
   # 每个帖子最多爬取的评论数量
   CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = 20
   ```

## 注意事项

- 用户ID是24位的十六进制字符串
- 确保目标用户的主页是公开的，私密账号无法爬取
- 一次可以配置多个用户ID，程序会依次爬取每个用户的帖子
- 爬取过程中会自动去重，避免重复数据

## 运行爬虫

配置完成后，直接运行：
```bash
python main.py
```

程序会：
1. 登录小红书账号
2. 获取每个用户的基本信息
3. 爬取用户的所有帖子
4. 爬取每个帖子的评论
5. 将数据保存到数据库

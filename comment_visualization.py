#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiomysql
import json
from datetime import datetime
from collections import defaultdict
from config.db_config import *

class CommentVisualization:
    """评论可视化展示工具"""
    
    def __init__(self):
        self.conn = None
    
    async def connect_db(self):
        """连接数据库"""
        self.conn = await aiomysql.connect(
            host=RELATION_DB_HOST,
            port=RELATION_DB_PORT,
            user=RELATION_DB_USER,
            password=RELATION_DB_PWD,
            db=RELATION_DB_NAME,
            charset='utf8mb4'
        )
    
    async def close_db(self):
        """关闭数据库连接"""
        if self.conn:
            await self.conn.ensure_closed()
    
    def create_html_visualization(self, comment_tree, note_info):
        """创建HTML可视化"""
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小红书评论树可视化</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #ff6b6b, #feca57);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .note-title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .note-stats {
            font-size: 14px;
            opacity: 0.9;
        }
        .content {
            padding: 30px;
        }
        .comment {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 15px;
            overflow: hidden;
            transition: box-shadow 0.3s;
        }
        .comment:hover {
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .comment-header {
            background: #f8f9fa;
            padding: 15px;
            border-bottom: 1px solid #e0e0e0;
        }
        .comment-author {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .comment-meta {
            font-size: 12px;
            color: #666;
        }
        .comment-content {
            padding: 15px;
            line-height: 1.6;
        }
        .comment-actions {
            background: #f8f9fa;
            padding: 10px 15px;
            font-size: 12px;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }
        .reply {
            margin-left: 40px;
            margin-top: 10px;
            border-left: 3px solid #feca57;
            background: #fffbf0;
        }
        .reply .comment-header {
            background: #fff8e1;
        }
        .like-count {
            color: #ff6b6b;
            font-weight: bold;
        }
        .reply-indicator {
            color: #feca57;
            font-weight: bold;
            margin-right: 5px;
        }
        .stats-bar {
            background: #f0f0f0;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            display: flex;
            justify-content: space-around;
            text-align: center;
        }
        .stat-item {
            flex: 1;
        }
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="note-title">{note_title}</div>
            <div class="note-stats">
                点赞: {liked_count} | 评论: {comment_count} | 分析时间: {analysis_time}
            </div>
        </div>
        <div class="content">
            <div class="stats-bar">
                <div class="stat-item">
                    <div class="stat-number">{total_comments}</div>
                    <div class="stat-label">总评论数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{top_level_comments}</div>
                    <div class="stat-label">顶级评论</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{reply_comments}</div>
                    <div class="stat-label">回复评论</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{max_depth}</div>
                    <div class="stat-label">最大深度</div>
                </div>
            </div>
            {comments_html}
        </div>
    </div>
</body>
</html>
        """
        
        def format_time(timestamp):
            """格式化时间戳"""
            if isinstance(timestamp, int):
                return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M')
            return str(timestamp)
        
        def build_comment_html(comments, is_reply=False):
            """构建评论HTML"""
            html = ""
            for comment in comments:
                reply_class = "reply" if is_reply else ""
                reply_indicator = '<span class="reply-indicator">└─</span>' if is_reply else ""
                
                html += f"""
                <div class="comment {reply_class}">
                    <div class="comment-header">
                        <div class="comment-author">
                            {reply_indicator}{comment.get('nickname', '匿名用户')}
                        </div>
                        <div class="comment-meta">
                            {format_time(comment.get('create_time', ''))}
                        </div>
                    </div>
                    <div class="comment-content">
                        {comment.get('content', '')}
                    </div>
                    <div class="comment-actions">
                        <span class="like-count">❤️ {comment.get('like_count', 0)}</span>
                        <span style="margin-left: 20px;">💬 {len(comment.get('replies', []))}</span>
                    </div>
                    {build_comment_html(comment.get('replies', []), True)}
                </div>
                """
            return html
        
        # 计算统计信息
        def count_comments(tree):
            total = len(tree)
            replies = 0
            max_d = 0
            
            def count_recursive(comments, depth=0):
                nonlocal replies, max_d
                max_d = max(max_d, depth)
                for comment in comments:
                    if depth > 0:
                        replies += 1
                    if comment.get('replies'):
                        count_recursive(comment['replies'], depth + 1)
            
            count_recursive(tree)
            return total, total - replies, replies, max_d
        
        total, top_level, reply_level, max_depth = count_comments(comment_tree)
        
        comments_html = build_comment_html(comment_tree)
        
        return html_template.format(
            note_title=note_info.get('title', '未知标题'),
            liked_count=note_info.get('liked_count', 0),
            comment_count=note_info.get('comment_count', 0),
            analysis_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_comments=total,
            top_level_comments=top_level,
            reply_comments=reply_level,
            max_depth=max_depth,
            comments_html=comments_html
        )
    
    async def generate_visualization_for_note(self, note_id):
        """为指定笔记生成可视化"""
        cursor = await self.conn.cursor()
        
        # 获取笔记信息
        await cursor.execute("""
            SELECT title, liked_count, comment_count 
            FROM xhs_note 
            WHERE note_id = %s
        """, (note_id,))
        
        note_info = await cursor.fetchone()
        if not note_info:
            print(f"❌ 未找到笔记 {note_id}")
            return None
        
        note_data = {
            'title': note_info[0],
            'liked_count': note_info[1],
            'comment_count': note_info[2]
        }
        
        # 获取评论数据
        await cursor.execute("""
            SELECT comment_id, content, nickname, like_count, 
                   create_time, parent_comment_id, sub_comment_count
            FROM xhs_note_comment 
            WHERE note_id = %s
            ORDER BY create_time ASC
        """, (note_id,))
        
        comments_data = await cursor.fetchall()
        
        # 构建评论对象
        comments = []
        for row in comments_data:
            comments.append({
                'comment_id': row[0],
                'content': row[1],
                'nickname': row[2],
                'like_count': int(row[3]) if row[3] else 0,
                'create_time': row[4],
                'parent_comment_id': row[5] if row[5] and row[5] != '0' else None,
                'sub_comment_count': row[6]
            })
        
        # 构建评论树
        comment_tree = self._build_comment_tree(comments)
        
        # 生成HTML
        html_content = self.create_html_visualization(comment_tree, note_data)
        
        # 保存HTML文件
        filename = f'data/comment_visualization_{note_id}.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ 可视化文件已生成: {filename}")
        
        await cursor.close()
        return filename
    
    def _build_comment_tree(self, comments):
        """构建评论树"""
        comments_by_parent = defaultdict(list)
        
        for comment in comments:
            parent_id = comment['parent_comment_id']
            comments_by_parent[parent_id].append(comment)
        
        def build_tree_recursive(parent_id=None):
            tree = []
            for comment in comments_by_parent[parent_id]:
                comment_node = comment.copy()
                comment_node['replies'] = build_tree_recursive(comment['comment_id'])
                tree.append(comment_node)
            return tree
        
        return build_tree_recursive()

async def main():
    """主函数"""
    viz = CommentVisualization()
    
    try:
        await viz.connect_db()
        
        print("🎨 小红书评论可视化工具")
        print("=" * 50)
        
        # 获取热门笔记
        cursor = await viz.conn.cursor()
        await cursor.execute("""
            SELECT DISTINCT n.note_id, n.title, COUNT(c.comment_id) as comment_count
            FROM xhs_note n
            LEFT JOIN xhs_note_comment c ON n.note_id = c.note_id
            GROUP BY n.note_id, n.title
            HAVING comment_count > 0
            ORDER BY comment_count DESC
            LIMIT 5
        """)
        
        hot_notes = await cursor.fetchall()
        
        if not hot_notes:
            print("❌ 未找到有评论的笔记")
            return
        
        print("📊 为以下笔记生成可视化:")
        for note in hot_notes:
            print(f"  - {note[1][:50]}... ({note[2]} 条评论)")
        print()
        
        # 为每个笔记生成可视化
        generated_files = []
        for note in hot_notes:
            note_id = note[0]
            print(f"🎯 生成笔记 {note_id} 的可视化...")
            
            filename = await viz.generate_visualization_for_note(note_id)
            if filename:
                generated_files.append(filename)
        
        print(f"\n🎉 成功生成 {len(generated_files)} 个可视化文件:")
        for file in generated_files:
            print(f"  📄 {file}")
        
        print("\n💡 使用说明:")
        print("  1. 在浏览器中打开 .html 文件查看可视化效果")
        print("  2. 可视化展示了完整的评论树结构和回复关系")
        print("  3. 不同层级的评论用不同的缩进和颜色区分")
        
    except Exception as e:
        print(f"❌ 生成可视化出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await viz.close_db()

if __name__ == '__main__':
    import os
    os.makedirs('data', exist_ok=True)
    
    asyncio.run(main())

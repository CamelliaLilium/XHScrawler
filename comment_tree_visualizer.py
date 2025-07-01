#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiomysql
from typing import Dict, List, Any
from config.db_config import *

class CommentTreeVisualizer:
    """评论树可视化展示器"""
    
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
    
    async def show_comment_tree(self, note_id: str, max_depth: int = 3):
        """展示评论树形结构"""
        cursor = await self.conn.cursor()
        
        # 获取笔记信息
        await cursor.execute("""
            SELECT title, nickname, comment_count
            FROM xhs_note 
            WHERE note_id = %s
        """, (note_id,))
        note_info = await cursor.fetchone()
        
        if not note_info:
            print("❌ 笔记不存在")
            return
        
        print("📝 评论树形结构可视化")
        print("=" * 80)
        print(f"笔记标题: {note_info[0]}")
        print(f"作者: {note_info[1]}")
        print(f"总评论数: {note_info[2]}")
        print("=" * 80)
        
        # 获取所有评论
        await cursor.execute("""
            SELECT comment_id, content, nickname, like_count, 
                   create_time, parent_comment_id, user_id
            FROM xhs_note_comment 
            WHERE note_id = %s
            ORDER BY 
                CASE WHEN parent_comment_id IS NULL OR parent_comment_id = '0' 
                     THEN create_time ELSE 0 END ASC,
                create_time ASC
        """, (note_id,))
        
        all_comments = await cursor.fetchall()
        
        # 构建评论字典
        comments_dict = {}
        root_comments = []
        
        for comment in all_comments:
            comment_id, content, nickname, like_count, create_time, parent_comment_id, user_id = comment
            
            comment_obj = {
                "comment_id": comment_id,
                "content": content,
                "nickname": nickname,
                "like_count": like_count or "0",
                "create_time": create_time,
                "parent_comment_id": parent_comment_id if parent_comment_id and parent_comment_id != '0' else None,
                "user_id": user_id,
                "children": []
            }
            
            comments_dict[comment_id] = comment_obj
            
            if not comment_obj["parent_comment_id"]:
                root_comments.append(comment_obj)
        
        # 构建父子关系
        for comment_id, comment in comments_dict.items():
            if comment["parent_comment_id"]:
                parent_id = comment["parent_comment_id"]
                if parent_id in comments_dict:
                    comments_dict[parent_id]["children"].append(comment)
        
        # 展示评论树
        self._print_comment_tree(root_comments, max_depth)
    
    def _print_comment_tree(self, comments: List[Dict], max_depth: int, current_depth: int = 0, prefix: str = ""):
        """递归打印评论树"""
        if current_depth >= max_depth:
            return
        
        for i, comment in enumerate(comments):
            is_last = i == len(comments) - 1
            current_prefix = "└── " if is_last else "├── "
            next_prefix = "    " if is_last else "│   "
            
            # 格式化评论内容
            content = comment["content"][:60] + "..." if len(comment["content"]) > 60 else comment["content"]
            content = content.replace('\n', ' ').replace('\r', ' ')
            
            # 打印当前评论
            print(f"{prefix}{current_prefix}👤 {comment['nickname']}: {content}")
            print(f"{prefix}{next_prefix}   👍 {comment['like_count']} | 🆔 {comment['comment_id'][:8]}...")
            
            # 递归打印子评论
            if comment["children"] and current_depth < max_depth - 1:
                self._print_comment_tree(
                    comment["children"], 
                    max_depth, 
                    current_depth + 1, 
                    prefix + next_prefix
                )
            elif comment["children"]:
                # 如果还有子评论但达到最大深度，显示提示
                print(f"{prefix}{next_prefix}   📁 还有 {len(comment['children'])} 条回复...")
            
            # 在根评论之间添加分隔线
            if current_depth == 0 and not is_last:
                print(f"{prefix}│")

    async def show_comment_stats_tree(self, note_id: str):
        """展示带统计信息的评论树"""
        cursor = await self.conn.cursor()
        
        print("📊 评论统计树")
        print("=" * 80)
        
        # 获取根评论及其统计信息
        await cursor.execute("""
            SELECT 
                c1.comment_id,
                c1.content,
                c1.nickname,
                c1.like_count,
                COUNT(c2.comment_id) as reply_count,
                SUM(CAST(COALESCE(c2.like_count, '0') AS UNSIGNED)) as total_reply_likes
            FROM xhs_note_comment c1
            LEFT JOIN xhs_note_comment c2 ON c1.comment_id = c2.parent_comment_id
            WHERE c1.note_id = %s 
            AND (c1.parent_comment_id IS NULL OR c1.parent_comment_id = '0')
            GROUP BY c1.comment_id, c1.content, c1.nickname, c1.like_count
            ORDER BY CAST(COALESCE(c1.like_count, '0') AS UNSIGNED) DESC
            LIMIT 10
        """, (note_id,))
        
        root_comments = await cursor.fetchall()
        
        for i, comment in enumerate(root_comments, 1):
            comment_id, content, nickname, like_count, reply_count, total_reply_likes = comment
            
            # 截断内容
            display_content = content[:80] + "..." if len(content) > 80 else content
            display_content = display_content.replace('\n', ' ').replace('\r', ' ')
            
            print(f"{i}. 🌟 【热门根评论】")
            print(f"   👤 作者: {nickname}")
            print(f"   💬 内容: {display_content}")
            print(f"   📊 数据: 👍 {like_count} | 💬 {reply_count}条回复 | 回复总赞数: {total_reply_likes or 0}")
            
            if reply_count > 0:
                # 获取该评论的热门回复
                await cursor.execute("""
                    SELECT content, nickname, like_count
                    FROM xhs_note_comment
                    WHERE parent_comment_id = %s
                    ORDER BY CAST(COALESCE(like_count, '0') AS UNSIGNED) DESC
                    LIMIT 3
                """, (comment_id,))
                
                replies = await cursor.fetchall()
                
                print(f"   └── 🔥 热门回复:")
                for j, reply in enumerate(replies, 1):
                    reply_content, reply_nickname, reply_likes = reply
                    reply_display = reply_content[:50] + "..." if len(reply_content) > 50 else reply_content
                    reply_display = reply_display.replace('\n', ' ').replace('\r', ' ')
                    print(f"       {j}. {reply_nickname}: {reply_display} (👍 {reply_likes})")
            
            print()

async def main():
    """主函数"""
    visualizer = CommentTreeVisualizer()
    await visualizer.connect_db()
    
    try:
        # 获取最新的笔记
        cursor = await visualizer.conn.cursor()
        await cursor.execute("""
            SELECT note_id, title FROM xhs_note 
            ORDER BY last_modify_ts DESC 
            LIMIT 1
        """)
        result = await cursor.fetchone()
        
        if not result:
            print("❌ 没有找到笔记数据")
            return
        
        note_id, title = result
        print(f"🔍 正在分析笔记: {title}")
        print()
        
        # 展示评论树形结构
        await visualizer.show_comment_tree(note_id, max_depth=3)
        
        print("\n" + "="*80 + "\n")
        
        # 展示统计信息树
        await visualizer.show_comment_stats_tree(note_id)
        
    except Exception as e:
        print(f"❌ 展示出错: {e}")
    finally:
        await visualizer.close_db()

if __name__ == '__main__':
    asyncio.run(main())

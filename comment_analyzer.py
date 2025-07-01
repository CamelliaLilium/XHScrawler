#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiomysql
import json
from datetime import datetime
from typing import List, Dict, Any
from config.db_config import *

class CommentTreeAnalyzer:
    """评论树形结构分析器"""
    
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
    
    async def get_note_with_comments(self, note_id: str) -> Dict[str, Any]:
        """获取笔记及其所有评论数据"""
        cursor = await self.conn.cursor()
        
        # 获取笔记信息
        await cursor.execute("""
            SELECT note_id, title, `desc`, nickname, liked_count, 
                   collected_count, comment_count, time, note_url
            FROM xhs_note 
            WHERE note_id = %s
        """, (note_id,))
        note_data = await cursor.fetchone()
        
        if not note_data:
            return {"error": "笔记不存在"}
        
        # 获取所有评论（包括一级和二级评论）
        await cursor.execute("""
            SELECT comment_id, note_id, content, nickname, like_count, 
                   create_time, sub_comment_count, parent_comment_id, 
                   avatar, ip_location, user_id
            FROM xhs_note_comment 
            WHERE note_id = %s
            ORDER BY create_time ASC
        """, (note_id,))
        comments_data = await cursor.fetchall()
        
        # 构建笔记信息
        note_info = {
            "note_id": note_data[0],
            "title": note_data[1],
            "desc": note_data[2][:200] + "..." if note_data[2] and len(note_data[2]) > 200 else note_data[2],
            "author": note_data[3],
            "stats": {
                "liked_count": note_data[4],
                "collected_count": note_data[5],
                "comment_count": note_data[6]
            },
            "publish_time": datetime.fromtimestamp(note_data[7] / 1000).strftime("%Y-%m-%d %H:%M:%S"),
            "note_url": note_data[8]
        }
        
        # 构建评论树
        comments_tree = self._build_comment_tree(comments_data)
        
        return {
            "note_info": note_info,
            "comments_tree": comments_tree,
            "total_comments": len(comments_data),
            "root_comments": len([c for c in comments_data if not c[7] or c[7] == '0']),
            "sub_comments": len([c for c in comments_data if c[7] and c[7] != '0'])
        }
    
    def _build_comment_tree(self, comments_data: List) -> List[Dict[str, Any]]:
        """构建评论树形结构"""
        # 转换为字典格式
        comments_dict = {}
        for comment in comments_data:
            comment_id, note_id, content, nickname, like_count, create_time, \
            sub_comment_count, parent_comment_id, avatar, ip_location, user_id = comment
            
            comment_obj = {
                "comment_id": comment_id,
                "content": content,
                "author": {
                    "nickname": nickname,
                    "user_id": user_id,
                    "avatar": avatar,
                    "ip_location": ip_location
                },
                "stats": {
                    "like_count": like_count or "0",
                    "sub_comment_count": sub_comment_count or 0
                },
                "create_time": datetime.fromtimestamp(create_time / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                "parent_comment_id": parent_comment_id if parent_comment_id and parent_comment_id != '0' else None,
                "replies": []
            }
            comments_dict[comment_id] = comment_obj
        
        # 构建树形结构
        root_comments = []
        for comment_id, comment in comments_dict.items():
            if comment["parent_comment_id"]:
                # 这是一个回复
                parent_id = comment["parent_comment_id"]
                if parent_id in comments_dict:
                    comments_dict[parent_id]["replies"].append(comment)
            else:
                # 这是一个根评论
                root_comments.append(comment)
        
        return root_comments
    
    async def get_hot_comments(self, note_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门评论（按点赞数排序）"""
        cursor = await self.conn.cursor()
        
        await cursor.execute("""
            SELECT comment_id, content, nickname, like_count, create_time, 
                   sub_comment_count, parent_comment_id
            FROM xhs_note_comment 
            WHERE note_id = %s AND (parent_comment_id IS NULL OR parent_comment_id = '0')
            ORDER BY CAST(COALESCE(like_count, '0') AS UNSIGNED) DESC
            LIMIT %s
        """, (note_id, limit))
        
        hot_comments = await cursor.fetchall()
        
        result = []
        for comment in hot_comments:
            result.append({
                "comment_id": comment[0],
                "content": comment[1],
                "author": comment[2],
                "like_count": comment[3] or "0",
                "create_time": datetime.fromtimestamp(comment[4] / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                "sub_comment_count": comment[5] or 0
            })
        
        return result
    
    async def analyze_comment_stats(self, note_id: str) -> Dict[str, Any]:
        """分析评论统计数据"""
        cursor = await self.conn.cursor()
        
        # 评论总数统计
        await cursor.execute("""
            SELECT 
                COUNT(*) as total_comments,
                COUNT(CASE WHEN parent_comment_id IS NULL OR parent_comment_id = '0' THEN 1 END) as root_comments,
                COUNT(CASE WHEN parent_comment_id IS NOT NULL AND parent_comment_id != '0' THEN 1 END) as sub_comments,
                AVG(CAST(COALESCE(like_count, '0') AS UNSIGNED)) as avg_likes,
                MAX(CAST(COALESCE(like_count, '0') AS UNSIGNED)) as max_likes,
                COUNT(DISTINCT user_id) as unique_users
            FROM xhs_note_comment 
            WHERE note_id = %s
        """, (note_id,))
        
        stats = await cursor.fetchone()
        
        # 活跃用户统计
        await cursor.execute("""
            SELECT nickname, COUNT(*) as comment_count,
                   SUM(CAST(COALESCE(like_count, '0') AS UNSIGNED)) as total_likes
            FROM xhs_note_comment 
            WHERE note_id = %s
            GROUP BY user_id, nickname
            ORDER BY comment_count DESC
            LIMIT 5
        """, (note_id,))
        
        active_users = await cursor.fetchall()
        
        # 时间分布统计
        await cursor.execute("""
            SELECT 
                DATE_FORMAT(FROM_UNIXTIME(create_time/1000), '%%Y-%%m-%%d %%H:00:00') as hour_time,
                COUNT(*) as comment_count
            FROM xhs_note_comment 
            WHERE note_id = %s
            GROUP BY hour_time
            ORDER BY hour_time
        """, (note_id,))
        
        time_distribution = await cursor.fetchall()
        
        return {
            "total_stats": {
                "total_comments": int(stats[0] or 0),
                "root_comments": int(stats[1] or 0),
                "sub_comments": int(stats[2] or 0),
                "avg_likes": round(float(stats[3] or 0), 2),
                "max_likes": int(stats[4] or 0),
                "unique_users": int(stats[5] or 0)
            },
            "active_users": [
                {
                    "nickname": str(user[0] or ""),
                    "comment_count": int(user[1] or 0),
                    "total_likes": int(user[2] or 0)
                } for user in active_users
            ],
            "time_distribution": [
                {
                    "time": str(time[0] or ""),
                    "count": int(time[1] or 0)
                } for time in time_distribution
            ]
        }
    
    async def export_comment_tree(self, note_id: str, output_file: str = None):
        """导出评论树到文件"""
        data = await self.get_note_with_comments(note_id)
        stats = await self.analyze_comment_stats(note_id)
        hot_comments = await self.get_hot_comments(note_id)
        
        export_data = {
            "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "note_info": data["note_info"],
            "statistics": {
                "total_comments": data["total_comments"],
                "root_comments": data["root_comments"],
                "sub_comments": data["sub_comments"],
                "detailed_stats": stats
            },
            "hot_comments": hot_comments,
            "full_comment_tree": data["comments_tree"]
        }
        
        if not output_file:
            output_file = f"data/comment_analysis_{note_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return output_file, export_data

async def main():
    """主函数 - 演示评论分析功能"""
    
    analyzer = CommentTreeAnalyzer()
    await analyzer.connect_db()
    
    try:
        # 获取最新的一个笔记ID进行演示
        cursor = await analyzer.conn.cursor()
        await cursor.execute("""
            SELECT note_id FROM xhs_note 
            ORDER BY last_modify_ts DESC 
            LIMIT 1
        """)
        result = await cursor.fetchone()
        
        if not result:
            print("❌ 没有找到笔记数据")
            return
        
        note_id = result[0]
        print(f"📝 分析笔记: {note_id}")
        print("=" * 80)
        
        # 获取完整评论树
        data = await analyzer.get_note_with_comments(note_id)
        
        # 打印笔记信息
        note_info = data["note_info"]
        print(f"📖 标题: {note_info['title']}")
        print(f"👤 作者: {note_info['author']}")
        print(f"📊 点赞: {note_info['stats']['liked_count']} | 收藏: {note_info['stats']['collected_count']} | 评论: {note_info['stats']['comment_count']}")
        print(f"⏰ 发布时间: {note_info['publish_time']}")
        print(f"📝 描述: {note_info['desc']}")
        print()
        
        # 打印评论统计
        print(f"💬 评论统计:")
        print(f"   总评论数: {data['total_comments']}")
        print(f"   一级评论: {data['root_comments']}")
        print(f"   二级评论: {data['sub_comments']}")
        print()
        
        # 获取并显示热门评论
        hot_comments = await analyzer.get_hot_comments(note_id, 5)
        print("🔥 热门评论 TOP 5:")
        print("-" * 60)
        for i, comment in enumerate(hot_comments, 1):
            print(f"{i}. {comment['author']}: {comment['content'][:50]}...")
            print(f"   👍 {comment['like_count']} | 💬 {comment['sub_comment_count']} | {comment['create_time']}")
        print()
        
        # 获取详细统计
        stats = await analyzer.analyze_comment_stats(note_id)
        print("📊 详细统计:")
        print(f"   平均点赞数: {stats['total_stats']['avg_likes']}")
        print(f"   最高点赞数: {stats['total_stats']['max_likes']}")
        print(f"   参与用户数: {stats['total_stats']['unique_users']}")
        print()
        
        print("👥 活跃用户 TOP 5:")
        for user in stats['active_users']:
            print(f"   {user['nickname']}: {user['comment_count']}条评论, {user['total_likes']}总点赞")
        print()
        
        # 导出数据
        output_file, export_data = await analyzer.export_comment_tree(note_id)
        print(f"📁 评论分析数据已导出到: {output_file}")
        
        # 打印评论树结构（前3个根评论）
        print("\n🌳 评论树结构预览 (前3个根评论):")
        print("-" * 80)
        for i, root_comment in enumerate(data["comments_tree"][:3], 1):
            print(f"{i}. 【根评论】{root_comment['author']['nickname']}: {root_comment['content'][:50]}...")
            print(f"   👍 {root_comment['stats']['like_count']} | {root_comment['create_time']}")
            
            # 显示回复
            for j, reply in enumerate(root_comment['replies'][:3], 1):
                print(f"   └─ {j}. 【回复】{reply['author']['nickname']}: {reply['content'][:40]}...")
                print(f"      👍 {reply['stats']['like_count']} | {reply['create_time']}")
            
            if len(root_comment['replies']) > 3:
                print(f"      └─ ... 还有 {len(root_comment['replies']) - 3} 条回复")
            print()
        
    except Exception as e:
        print(f"❌ 分析出错: {e}")
    finally:
        await analyzer.close_db()

if __name__ == '__main__':
    import os
    os.makedirs('data', exist_ok=True)
    
    asyncio.run(main())

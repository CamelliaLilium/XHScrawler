#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiomysql
import json
from datetime import datetime
from collections import defaultdict
from config.db_config import *

class CommentTreeAnalyzer:
    """评论树结构分析器"""
    
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
    
    async def get_comments_by_note(self, note_id):
        """获取指定笔记的所有评论"""
        cursor = await self.conn.cursor()
        await cursor.execute("""
            SELECT comment_id, note_id, content, nickname, like_count, 
                   create_time, sub_comment_count, parent_comment_id, avatar
            FROM xhs_note_comment 
            WHERE note_id = %s
            ORDER BY create_time ASC
        """, (note_id,))
        
        comments = await cursor.fetchall()
        await cursor.close()
        
        return [
            {
                'comment_id': row[0],
                'note_id': row[1],
                'content': row[2],
                'nickname': row[3],
                'like_count': int(row[4]) if row[4] else 0,
                'create_time': row[5],
                'sub_comment_count': int(row[6]) if row[6] else 0,
                'parent_comment_id': row[7] if row[7] != '0' else None,
                'avatar': row[8]
            }
            for row in comments
        ]
    
    def build_comment_tree(self, comments):
        """构建评论树结构"""
        # 按parent_comment_id分组
        comments_by_parent = defaultdict(list)
        comment_map = {}
        
        for comment in comments:
            comment_map[comment['comment_id']] = comment
            parent_id = comment['parent_comment_id']
            comments_by_parent[parent_id].append(comment)
        
        # 构建树结构
        def build_tree_recursive(parent_id=None):
            tree = []
            for comment in comments_by_parent[parent_id]:
                comment_node = comment.copy()
                comment_node['replies'] = build_tree_recursive(comment['comment_id'])
                comment_node['reply_count'] = len(comment_node['replies'])
                tree.append(comment_node)
            return tree
        
        return build_tree_recursive()
    
    def format_comment_tree_text(self, tree, indent=0):
        """格式化评论树为文本显示"""
        result = []
        
        for comment in tree:
            prefix = "  " * indent + ("└─ " if indent > 0 else "")
            
            # 格式化时间
            create_time = comment['create_time']
            if isinstance(create_time, int):
                time_str = datetime.fromtimestamp(create_time / 1000).strftime('%Y-%m-%d %H:%M')
            else:
                time_str = str(create_time)
            
            # 主评论信息
            result.append(f"{prefix}👤 {comment['nickname']}")
            result.append(f"{prefix}💬 {comment['content']}")
            result.append(f"{prefix}❤️ {comment['like_count']} 👥 {comment['reply_count']} ⏰ {time_str}")
            result.append("")
            
            # 递归显示回复
            if comment['replies']:
                result.extend(self.format_comment_tree_text(comment['replies'], indent + 1))
        
        return result
    
    async def analyze_note_comments(self, note_id):
        """分析指定笔记的评论结构"""
        print(f"🔍 分析笔记 {note_id} 的评论结构...")
        
        # 获取评论数据
        comments = await self.get_comments_by_note(note_id)
        
        if not comments:
            print("❌ 未找到评论数据")
            return None
        
        # 构建评论树
        comment_tree = self.build_comment_tree(comments)
        
        # 统计信息
        total_comments = len(comments)
        top_level_comments = len(comment_tree)
        reply_comments = total_comments - top_level_comments
        
        # 计算各层级评论数量
        level_counts = defaultdict(int)
        
        def count_levels(tree, level=0):
            level_counts[level] += len(tree)
            for comment in tree:
                if comment['replies']:
                    count_levels(comment['replies'], level + 1)
        
        count_levels(comment_tree)
        
        # 生成分析报告
        analysis = {
            'note_id': note_id,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'statistics': {
                'total_comments': total_comments,
                'top_level_comments': top_level_comments,
                'reply_comments': reply_comments,
                'max_depth': max(level_counts.keys()) if level_counts else 0,
                'level_distribution': dict(level_counts)
            },
            'comment_tree': comment_tree
        }
        
        return analysis
    
    async def get_hot_notes_with_comments(self, limit=5):
        """获取有评论的热门笔记"""
        cursor = await self.conn.cursor()
        await cursor.execute("""
            SELECT DISTINCT n.note_id, n.title, n.liked_count, n.comment_count, 
                   COUNT(c.comment_id) as actual_comment_count
            FROM xhs_note n
            LEFT JOIN xhs_note_comment c ON n.note_id = c.note_id
            GROUP BY n.note_id, n.title, n.liked_count, n.comment_count
            HAVING actual_comment_count > 0
            ORDER BY CAST(n.liked_count AS UNSIGNED) DESC
            LIMIT %s
        """, (limit,))
        
        notes = await cursor.fetchall()
        await cursor.close()
        
        return [
            {
                'note_id': row[0],
                'title': row[1],
                'liked_count': row[2],
                'comment_count': row[3],
                'actual_comment_count': row[4]
            }
            for row in notes
        ]

async def main():
    """主函数"""
    analyzer = CommentTreeAnalyzer()
    
    try:
        # 连接数据库
        await analyzer.connect_db()
        
        print("🎯 小红书评论结构分析工具")
        print("=" * 60)
        
        # 获取有评论的热门笔记
        hot_notes = await analyzer.get_hot_notes_with_comments(10)
        
        if not hot_notes:
            print("❌ 未找到有评论的笔记数据")
            return
        
        print("📊 热门笔记列表:")
        for i, note in enumerate(hot_notes, 1):
            print(f"{i}. {note['title'][:40]}...")
            print(f"   笔记ID: {note['note_id']}")
            print(f"   点赞: {note['liked_count']} | 评论: {note['actual_comment_count']}")
            print()
        
        # 分析前3个笔记的评论结构
        print("🔍 详细分析前3个笔记的评论结构:")
        print("=" * 60)
        
        for i, note in enumerate(hot_notes[:3], 1):
            print(f"\n📝 笔记 {i}: {note['title'][:30]}...")
            print("-" * 50)
            
            # 分析评论结构
            analysis = await analyzer.analyze_note_comments(note['note_id'])
            
            if analysis:
                stats = analysis['statistics']
                print(f"📊 统计信息:")
                print(f"   总评论数: {stats['total_comments']}")
                print(f"   顶级评论: {stats['top_level_comments']}")
                print(f"   回复评论: {stats['reply_comments']}")
                print(f"   最大深度: {stats['max_depth']}")
                print(f"   各层分布: {stats['level_distribution']}")
                print()
                
                # 显示评论树结构（前10条）
                if analysis['comment_tree']:
                    print("🌲 评论树结构（前10条）:")
                    tree_text = analyzer.format_comment_tree_text(analysis['comment_tree'][:10])
                    for line in tree_text[:50]:  # 限制显示行数
                        print(line)
                    
                    if len(tree_text) > 50:
                        print("... (更多评论省略)")
                
                # 保存详细分析到文件
                filename = f'data/comment_analysis_{note["note_id"]}.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
                print(f"💾 详细分析已保存到: {filename}")
                print()
        
        # 生成总体统计报告
        print("📈 生成总体评论统计报告...")
        
        cursor = await analyzer.conn.cursor()
        
        # 评论总体统计
        await cursor.execute("""
            SELECT 
                COUNT(*) as total_comments,
                COUNT(CASE WHEN parent_comment_id IS NULL OR parent_comment_id = '0' THEN 1 END) as top_level,
                COUNT(CASE WHEN parent_comment_id IS NOT NULL AND parent_comment_id != '0' THEN 1 END) as replies,
                AVG(CAST(like_count AS UNSIGNED)) as avg_likes,
                MAX(CAST(like_count AS UNSIGNED)) as max_likes
            FROM xhs_note_comment
        """)
        
        stats = await cursor.fetchone()
        
        overall_report = {
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overall_statistics': {
                'total_comments': int(stats[0]),
                'top_level_comments': int(stats[1]),
                'reply_comments': int(stats[2]),
                'average_likes': round(float(stats[3] or 0), 2),
                'max_likes': int(stats[4] or 0)
            },
            'hot_notes': hot_notes
        }
        
        # 保存总体报告
        with open('data/comment_overall_report.json', 'w', encoding='utf-8') as f:
            json.dump(overall_report, f, ensure_ascii=False, indent=2, default=str)
        
        print("✅ 总体报告已保存到: data/comment_overall_report.json")
        
        print("\n🎉 评论结构分析完成！")
        print("=" * 60)
        print(f"📊 总评论数: {overall_report['overall_statistics']['total_comments']}")
        print(f"🔝 顶级评论: {overall_report['overall_statistics']['top_level_comments']}")
        print(f"💬 回复评论: {overall_report['overall_statistics']['reply_comments']}")
        print(f"❤️ 平均点赞: {overall_report['overall_statistics']['average_likes']}")
        
    except Exception as e:
        print(f"❌ 分析出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await analyzer.close_db()

if __name__ == '__main__':
    # 确保data目录存在
    import os
    os.makedirs('data', exist_ok=True)
    
    asyncio.run(main())

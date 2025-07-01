#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiomysql
import json
from datetime import datetime
from collections import defaultdict
from config.db_config import *

class DatabaseStructureOptimizer:
    """数据库结构优化和展示工具"""
    
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
    
    async def analyze_comment_structure(self):
        """分析评论表结构"""
        cursor = await self.conn.cursor()
        
        print("📊 小红书评论表结构分析")
        print("=" * 60)
        
        # 查看表结构
        await cursor.execute("DESCRIBE xhs_note_comment")
        columns = await cursor.fetchall()
        
        print("📋 xhs_note_comment 表结构:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]}) {col[3] if col[3] else ''}")
        print()
        
        # 分析parent_comment_id字段的数据分布
        await cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN parent_comment_id IS NULL OR parent_comment_id = '0' THEN 1 END) as top_level,
                COUNT(CASE WHEN parent_comment_id IS NOT NULL AND parent_comment_id != '0' THEN 1 END) as replies
            FROM xhs_note_comment
        """)
        
        stats = await cursor.fetchone()
        
        print("📈 评论层级分布:")
        print(f"  总评论数: {stats[0]}")
        print(f"  顶级评论: {stats[1]} ({stats[1]/stats[0]*100:.1f}%)")
        print(f"  回复评论: {stats[2]} ({stats[2]/stats[0]*100:.1f}%)")
        print()
        
        # 检查是否有实际的回复数据
        await cursor.execute("""
            SELECT parent_comment_id, COUNT(*) as count
            FROM xhs_note_comment 
            WHERE parent_comment_id IS NOT NULL AND parent_comment_id != '0'
            GROUP BY parent_comment_id
            ORDER BY count DESC
            LIMIT 10
        """)
        
        replies = await cursor.fetchall()
        
        if replies:
            print("🔗 回复最多的评论:")
            for reply in replies:
                print(f"  父评论ID: {reply[0]} -> {reply[1]} 条回复")
        else:
            print("⚠️ 当前数据库中没有二级回复数据")
        print()
        
        await cursor.close()
        return stats
    
    async def create_optimized_views(self):
        """创建优化的数据库视图"""
        cursor = await self.conn.cursor()
        
        print("🛠️ 创建优化的数据库视图...")
        
        # 创建评论树视图
        try:
            await cursor.execute("DROP VIEW IF EXISTS comment_tree_view")
            
            await cursor.execute("""
                CREATE VIEW comment_tree_view AS
                SELECT 
                    c1.comment_id,
                    c1.note_id,
                    c1.content,
                    c1.nickname,
                    c1.like_count,
                    c1.create_time,
                    c1.parent_comment_id,
                    c1.sub_comment_count,
                    CASE 
                        WHEN c1.parent_comment_id IS NULL OR c1.parent_comment_id = '0' 
                        THEN 'top_level' 
                        ELSE 'reply' 
                    END as comment_level,
                    c2.nickname as parent_nickname,
                    c2.content as parent_content
                FROM xhs_note_comment c1
                LEFT JOIN xhs_note_comment c2 ON c1.parent_comment_id = c2.comment_id
                ORDER BY c1.note_id, c1.create_time
            """)
            
            print("✅ 创建 comment_tree_view 视图成功")
            
        except Exception as e:
            print(f"❌ 创建视图失败: {e}")
        
        # 创建笔记评论统计视图
        try:
            await cursor.execute("DROP VIEW IF EXISTS note_comment_stats")
            
            await cursor.execute("""
                CREATE VIEW note_comment_stats AS
                SELECT 
                    n.note_id,
                    n.title,
                    n.liked_count,
                    n.comment_count as note_comment_count,
                    COUNT(c.comment_id) as actual_comment_count,
                    COUNT(CASE WHEN c.parent_comment_id IS NULL OR c.parent_comment_id = '0' THEN 1 END) as top_level_comments,
                    COUNT(CASE WHEN c.parent_comment_id IS NOT NULL AND c.parent_comment_id != '0' THEN 1 END) as reply_comments,
                    AVG(CAST(c.like_count AS UNSIGNED)) as avg_comment_likes,
                    MAX(CAST(c.like_count AS UNSIGNED)) as max_comment_likes
                FROM xhs_note n
                LEFT JOIN xhs_note_comment c ON n.note_id = c.note_id
                GROUP BY n.note_id, n.title, n.liked_count, n.comment_count
                HAVING actual_comment_count > 0
            """)
            
            print("✅ 创建 note_comment_stats 视图成功")
            
        except Exception as e:
            print(f"❌ 创建统计视图失败: {e}")
        
        await cursor.close()
    
    async def demonstrate_optimized_queries(self):
        """演示优化的查询"""
        cursor = await self.conn.cursor()
        
        print("🔍 优化查询示例:")
        print("-" * 40)
        
        # 查询1: 获取带回复关系的评论
        print("1. 带回复关系的评论查询:")
        await cursor.execute("""
            SELECT comment_id, nickname, content, comment_level, 
                   parent_nickname, like_count
            FROM comment_tree_view 
            WHERE note_id = (
                SELECT note_id FROM note_comment_stats 
                ORDER BY actual_comment_count DESC 
                LIMIT 1
            )
            LIMIT 10
        """)
        
        results = await cursor.fetchall()
        for row in results:
            if row[3] == 'top_level':
                print(f"  👤 {row[1]}: {row[2][:50]}... (❤️{row[5]})")
            else:
                print(f"    └─ 回复 @{row[4]}: {row[2][:40]}... (❤️{row[5]})")
        print()
        
        # 查询2: 笔记评论统计
        print("2. 笔记评论统计查询:")
        await cursor.execute("""
            SELECT title, actual_comment_count, top_level_comments, 
                   reply_comments, avg_comment_likes
            FROM note_comment_stats 
            ORDER BY actual_comment_count DESC 
            LIMIT 5
        """)
        
        results = await cursor.fetchall()
        for row in results:
            print(f"  📝 {row[0][:30]}...")
            print(f"     总评论: {row[1]} | 顶级: {row[2]} | 回复: {row[3]} | 平均赞: {row[4]:.1f}")
        print()
        
        await cursor.close()
    
    async def export_structured_data(self):
        """导出结构化数据"""
        cursor = await self.conn.cursor()
        
        print("📤 导出结构化数据...")
        
        # 导出评论树结构
        await cursor.execute("""
            SELECT note_id, comment_id, parent_comment_id, nickname, 
                   content, like_count, create_time, comment_level
            FROM comment_tree_view
            ORDER BY note_id, create_time
        """)
        
        comments = await cursor.fetchall()
        
        # 按笔记分组
        notes_data = defaultdict(list)
        for comment in comments:
            note_id = comment[0]
            notes_data[note_id].append({
                'comment_id': comment[1],
                'parent_comment_id': comment[2] if comment[2] and comment[2] != '0' else None,
                'nickname': comment[3],
                'content': comment[4],
                'like_count': comment[5],
                'create_time': str(comment[6]),
                'comment_level': comment[7]
            })
        
        # 构建完整的数据结构
        structured_data = {
            'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_notes': len(notes_data),
            'total_comments': len(comments),
            'notes': {}
        }
        
        # 为每个笔记构建评论树
        for note_id, note_comments in notes_data.items():
            # 获取笔记信息
            await cursor.execute("""
                SELECT title, liked_count, comment_count 
                FROM xhs_note 
                WHERE note_id = %s
            """, (note_id,))
            
            note_info = await cursor.fetchone()
            
            structured_data['notes'][note_id] = {
                'note_info': {
                    'title': note_info[0] if note_info else '',
                    'liked_count': note_info[1] if note_info else 0,
                    'comment_count': note_info[2] if note_info else 0
                },
                'comments': note_comments,
                'comment_tree': self._build_comment_tree(note_comments)
            }
        
        # 保存到文件
        with open('data/structured_comments_data.json', 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)
        
        print("✅ 结构化数据已导出到: data/structured_comments_data.json")
        
        await cursor.close()
        return structured_data
    
    def _build_comment_tree(self, comments):
        """构建评论树"""
        # 按parent_comment_id分组
        comments_by_parent = defaultdict(list)
        
        for comment in comments:
            parent_id = comment['parent_comment_id']
            comments_by_parent[parent_id].append(comment)
        
        # 构建树结构
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
    optimizer = DatabaseStructureOptimizer()
    
    try:
        await optimizer.connect_db()
        
        print("🎯 数据库结构优化和展示工具")
        print("=" * 60)
        
        # 分析当前评论结构
        await optimizer.analyze_comment_structure()
        
        # 创建优化的视图
        await optimizer.create_optimized_views()
        
        # 演示优化查询
        await optimizer.demonstrate_optimized_queries()
        
        # 导出结构化数据
        await optimizer.export_structured_data()
        
        print("\n💡 数据结构优化建议:")
        print("=" * 60)
        print("1. ✅ 已创建 comment_tree_view 视图 - 便于查询评论回复关系")
        print("2. ✅ 已创建 note_comment_stats 视图 - 便于统计分析")
        print("3. 📊 已导出结构化JSON数据 - 便于前端展示")
        print("4. 🔄 建议重新爬取数据并启用二级评论功能")
        
        print("\n🚀 获取二级评论的建议:")
        print("-" * 40)
        print("1. 确保配置文件中 ENABLE_GET_SUB_COMMENTS = True")
        print("2. 运行: python main.py --platform xhs --lt cookie --type search --get_sub_comment true")
        print("3. 重新运行本分析工具查看完整的评论树结构")
        
    except Exception as e:
        print(f"❌ 优化过程出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await optimizer.close_db()

if __name__ == '__main__':
    import os
    os.makedirs('data', exist_ok=True)
    
    asyncio.run(main())

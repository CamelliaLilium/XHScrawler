#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiomysql
import pandas as pd
import json
from datetime import datetime
from config.db_config import *

async def export_data():
    """导出爬取的数据到不同格式"""
    
    # 连接数据库
    conn = await aiomysql.connect(
        host=RELATION_DB_HOST,
        port=RELATION_DB_PORT,
        user=RELATION_DB_USER,
        password=RELATION_DB_PWD,
        db=RELATION_DB_NAME,
        charset='utf8mb4'
    )
    
    try:
        cursor = await conn.cursor()
        
        print("📊 开始导出数据...")
        
        # 导出笔记数据
        print("📝 导出笔记数据...")
        await cursor.execute("""
            SELECT note_id, title, `desc`, nickname, liked_count, collected_count, 
                   comment_count, share_count, note_url, source_keyword, time
            FROM xhs_note 
            ORDER BY time DESC
        """)
        notes_data = await cursor.fetchall()
        
        # 转换为DataFrame
        notes_df = pd.DataFrame(notes_data, columns=[
            'note_id', 'title', 'desc', 'nickname', 'liked_count', 
            'collected_count', 'comment_count', 'share_count', 'note_url', 
            'source_keyword', 'time'
        ])
        
        # 导出到CSV
        notes_df.to_csv('data/xhs_notes.csv', index=False, encoding='utf-8-sig')
        print(f"✅ 笔记数据已导出到: data/xhs_notes.csv ({len(notes_data)} 条)")
        
        # 导出评论数据
        print("💬 导出评论数据...")
        await cursor.execute("""
            SELECT comment_id, note_id, content, nickname, like_count, 
                   create_time, sub_comment_count, avatar
            FROM xhs_note_comment 
            ORDER BY create_time DESC
        """)
        comments_data = await cursor.fetchall()
        
        # 转换为DataFrame
        comments_df = pd.DataFrame(comments_data, columns=[
            'comment_id', 'note_id', 'content', 'nickname', 'like_count',
            'create_time', 'sub_comment_count', 'avatar'
        ])
        
        # 导出到CSV
        comments_df.to_csv('data/xhs_comments.csv', index=False, encoding='utf-8-sig')
        print(f"✅ 评论数据已导出到: data/xhs_comments.csv ({len(comments_data)} 条)")
        
        # 生成数据统计报告
        print("📈 生成数据统计报告...")
        
        # 笔记统计
        await cursor.execute("""
            SELECT 
                COUNT(*) as total_notes,
                AVG(CAST(liked_count AS UNSIGNED)) as avg_likes,
                MAX(CAST(liked_count AS UNSIGNED)) as max_likes,
                AVG(CAST(comment_count AS UNSIGNED)) as avg_comments,
                MAX(CAST(comment_count AS UNSIGNED)) as max_comments
            FROM xhs_note
        """)
        note_stats = await cursor.fetchone()
        
        # 评论统计
        await cursor.execute("""
            SELECT 
                COUNT(*) as total_comments,
                AVG(CAST(like_count AS UNSIGNED)) as avg_comment_likes,
                MAX(CAST(like_count AS UNSIGNED)) as max_comment_likes
            FROM xhs_note_comment
        """)
        comment_stats = await cursor.fetchone()
        
        # 热门笔记 (按点赞数)
        await cursor.execute("""
            SELECT title, liked_count, comment_count, nickname
            FROM xhs_note 
            ORDER BY CAST(liked_count AS UNSIGNED) DESC 
            LIMIT 5
        """)
        hot_notes = await cursor.fetchall()
        
        # 生成报告
        report = {
            "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "数据统计": {
                "笔记总数": int(note_stats[0] or 0),
                "评论总数": int(comment_stats[0] or 0),
                "平均点赞数": round(float(note_stats[1] or 0), 2),
                "最高点赞数": int(note_stats[2] or 0),
                "平均评论数": round(float(note_stats[3] or 0), 2),
                "最高评论数": int(note_stats[4] or 0),
                "评论平均点赞": round(float(comment_stats[1] or 0), 2),
                "评论最高点赞": int(comment_stats[2] or 0)
            },
            "热门笔记TOP5": [
                {
                    "标题": str(note[0] or ""),
                    "点赞数": str(note[1] or "0"),
                    "评论数": str(note[2] or "0"),
                    "作者": str(note[3] or "")
                } for note in hot_notes
            ]
        }
        
        # 保存报告
        with open('data/xhs_data_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print("✅ 数据统计报告已生成: data/xhs_data_report.json")
        
        # 打印概要
        print("\n" + "="*60)
        print("📋 数据导出完成 - 概要统计")
        print("="*60)
        print(f"📝 笔记总数: {report['数据统计']['笔记总数']}")
        print(f"💬 评论总数: {report['数据统计']['评论总数']}")
        print(f"❤️ 平均点赞数: {report['数据统计']['平均点赞数']}")
        print(f"🔥 最高点赞数: {report['数据统计']['最高点赞数']}")
        print(f"💭 平均评论数: {report['数据统计']['平均评论数']}")
        print("\n🏆 热门笔记TOP3:")
        for i, note in enumerate(report['热门笔记TOP5'][:3], 1):
            print(f"{i}. {note['标题'][:30]}... (点赞:{note['点赞数']}, 评论:{note['评论数']})")
        
    except Exception as e:
        print(f"❌ 导出出错: {e}")
    finally:
        await conn.ensure_closed()

if __name__ == '__main__':
    # 确保data目录存在
    import os
    os.makedirs('data', exist_ok=True)
    
    asyncio.run(export_data())

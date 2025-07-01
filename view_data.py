#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiomysql
from config.db_config import *

async def view_database_data():
    """查看数据库中爬取的数据"""
    
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
        
        print("=" * 80)
        print("📊 爬取数据统计")
        print("=" * 80)
        
        # 查看所有表
        await cursor.execute("SHOW TABLES")
        tables = await cursor.fetchall()
        print(f"📋 数据库表列表:")
        for table in tables:
            print(f"  - {table[0]}")
        print()
        
        # 查看小红书笔记数据
        await cursor.execute("SELECT COUNT(*) FROM xhs_note")
        note_count = await cursor.fetchone()
        print(f"📝 小红书笔记总数: {note_count[0]}")
        
        # 查看小红书评论数据
        await cursor.execute("SELECT COUNT(*) FROM xhs_note_comment")
        comment_count = await cursor.fetchone()
        print(f"💬 小红书评论总数: {comment_count[0]}")
        print()
        
        # 查看最新的5条笔记
        print("📖 最新爬取的5条笔记:")
        print("-" * 80)
        await cursor.execute("""
            SELECT note_id, title, desc_text, created_at, like_count, collected_count, comment_count 
            FROM xhs_note 
            ORDER BY last_modify_ts DESC 
            LIMIT 5
        """)
        notes = await cursor.fetchall()
        
        for i, note in enumerate(notes, 1):
            note_id, title, desc, created_at, like_count, collected_count, comment_count = note
            print(f"{i}. 标题: {title[:50]}...")
            print(f"   ID: {note_id}")
            print(f"   点赞: {like_count} | 收藏: {collected_count} | 评论: {comment_count}")
            print(f"   发布时间: {created_at}")
            print()
        
        # 查看最新的10条评论
        print("💭 最新爬取的10条评论:")
        print("-" * 80)
        await cursor.execute("""
            SELECT comment_id, note_id, content, nickname, like_count, create_time
            FROM xhs_note_comment 
            ORDER BY last_modify_ts DESC 
            LIMIT 10
        """)
        comments = await cursor.fetchall()
        
        for i, comment in enumerate(comments, 1):
            comment_id, note_id, content, nickname, like_count, create_time = comment
            print(f"{i}. {nickname}: {content[:100]}...")
            print(f"   笔记ID: {note_id} | 点赞: {like_count}")
            print()
            
    except Exception as e:
        print(f"❌ 查询出错: {e}")
    finally:
        await conn.ensure_closed()

if __name__ == '__main__':
    asyncio.run(view_database_data())

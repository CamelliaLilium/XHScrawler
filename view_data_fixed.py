#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiomysql
from config.db_config import *

async def view_database_structure():
    """查看数据库表结构和数据"""
    
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
        print("📊 小红书爬取数据统计")
        print("=" * 80)
        
        # 查看小红书笔记数据
        await cursor.execute("SELECT COUNT(*) FROM xhs_note")
        note_count = await cursor.fetchone()
        print(f"📝 小红书笔记总数: {note_count[0]}")
        
        # 查看小红书评论数据
        await cursor.execute("SELECT COUNT(*) FROM xhs_note_comment")
        comment_count = await cursor.fetchone()
        print(f"💬 小红书评论总数: {comment_count[0]}")
        print()
        
        # 查看xhs_note表结构
        print("📋 xhs_note 表结构:")
        await cursor.execute("DESCRIBE xhs_note")
        columns = await cursor.fetchall()
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")
        print()
        
        # 查看最新的3条笔记 (使用正确的列名)
        print("📖 最新爬取的3条笔记:")
        print("-" * 80)
        await cursor.execute("""
            SELECT note_id, title, `desc`, liked_count, collected_count, comment_count, time
            FROM xhs_note 
            ORDER BY last_modify_ts DESC 
            LIMIT 3
        """)
        notes = await cursor.fetchall()
        
        for i, note in enumerate(notes, 1):
            note_id, title, desc, liked_count, collected_count, comment_count, time_val = note
            print(f"{i}. 标题: {title}")
            print(f"   ID: {note_id}")
            print(f"   描述: {desc[:100] if desc else '无描述'}...")
            print(f"   点赞: {liked_count} | 收藏: {collected_count} | 评论: {comment_count}")
            print(f"   发布时间戳: {time_val}")
            print()
        
        # 查看最新的5条评论
        print("💭 最新爬取的5条评论:")
        print("-" * 80)
        await cursor.execute("""
            SELECT comment_id, note_id, content, nickname, like_count, create_time
            FROM xhs_note_comment 
            ORDER BY last_modify_ts DESC 
            LIMIT 5
        """)
        comments = await cursor.fetchall()
        
        for i, comment in enumerate(comments, 1):
            comment_id, note_id, content, nickname, like_count, create_time = comment
            print(f"{i}. {nickname}: {content}")
            print(f"   笔记ID: {note_id} | 点赞数: {like_count}")
            print(f"   评论时间: {create_time}")
            print()
            
    except Exception as e:
        print(f"❌ 查询出错: {e}")
    finally:
        await conn.ensure_closed()

if __name__ == '__main__':
    asyncio.run(view_database_structure())

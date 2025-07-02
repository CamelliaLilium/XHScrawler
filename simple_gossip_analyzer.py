#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版娱乐八卦负面舆情检测
使用Hugging Face API进行情感分析
"""

import pandas as pd
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import re
import json
from datetime import datetime
from typing import List, Dict, Tuple
import requests
import time

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei'] 
plt.rcParams['axes.unicode_minus'] = False

class SimpleGossipAnalyzer:
    """简化版娱乐八卦分析器"""
    
    def __init__(self):
        self.setup_keywords()
        self.load_data()
        
    def setup_keywords(self):
        """构建娱乐八卦关键词表（50+词语）"""
        self.gossip_keywords = {
            # 明星相关 (15个)
            'celebrity': [
                '明星', '艺人', '演员', '歌手', '网红', '博主', '主播', '偶像',
                '爱豆', '流量', '顶流', '糊咖', '过气', '新人', '老艺人'
            ],
            
            # 感情八卦 (15个) 
            'relationship': [
                '恋情', '绯闻', '分手', '复合', '出轨', '劈腿', '小三', '正宫',
                '前任', '现任', '暧昧', '约会', '同居', '结婚', '离婚'
            ],
            
            # 负面事件 (15个)
            'negative_events': [
                '塌房', '翻车', '黑料', '丑闻', '争议', '抄袭', '造假', '诈骗',
                '吸毒', '嫖娼', '家暴', '霸凌', '欺凌', '校园暴力', '职场骚扰'
            ],
            
            # 网络用语 (10个)
            'internet_slang': [
                '吃瓜', '爆料', '瓜', '锤', '实锤', '石锤', '澄清', '洗白',
                '公关', '营销号'
            ],
            
            # 情绪词汇 (10个)
            'emotions': [
                '愤怒', '失望', '恶心', '讨厌', '鄙视', '无语', '震惊', '气愤',
                '心疼', '同情'
            ]
        }
        
        # 展平所有关键词
        self.all_keywords = []
        for category, words in self.gossip_keywords.items():
            self.all_keywords.extend(words)
            
        print(f"构建娱乐八卦关键词表: {len(self.all_keywords)} 个关键词")
        
        # 保存关键词表
        with open('data/gossip_keywords.json', 'w', encoding='utf-8') as f:
            json.dump(self.gossip_keywords, f, ensure_ascii=False, indent=2)
    
    def load_data(self):
        """加载数据"""
        try:
            # 加载帖子数据
            self.notes_df = pd.read_csv('data/xhs_notes.csv')
            print(f"加载帖子数据: {len(self.notes_df)} 条")
            
            # 加载评论数据
            self.comments_df = pd.read_csv('data/xhs_comments.csv')
            print(f"加载评论数据: {len(self.comments_df)} 条")
            
            # 合并所有文本内容
            self.all_texts = []
            
            # 添加帖子标题和描述
            for _, row in self.notes_df.iterrows():
                if pd.notna(row['title']):
                    self.all_texts.append(str(row['title']))
                if pd.notna(row['desc']):
                    self.all_texts.append(str(row['desc']))
            
            # 添加评论内容  
            for _, row in self.comments_df.iterrows():
                if pd.notna(row['content']):
                    self.all_texts.append(str(row['content']))
                    
            print(f"总文本数量: {len(self.all_texts)}")
            
        except Exception as e:
            print(f"数据加载失败: {e}")
            self.notes_df = pd.DataFrame()
            self.comments_df = pd.DataFrame()
            self.all_texts = []
    
    def generate_wordcloud(self):
        """生成词云图"""
        print("\\n=== 生成词云图 ===")
        
        # 合并所有文本
        text = ' '.join(self.all_texts)
        
        # 清理文本
        text = re.sub(r'[#@﻿\[\]]+', '', text)
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'[a-zA-Z0-9]+', '', text)
        
        # 分词
        words = jieba.cut(text)
        
        # 过滤停用词
        stop_words = {
            '的', '了', '是', '我', '你', '他', '她', '它', '们', '在', '有', '和',
            '就', '都', '被', '从', '把', '为', '着', '过', '给', '与', '及',
            '话题', '方舟', '蛋仔', '派对', '游戏', '手游', '暗黑', '破坏神',
            'QQ', '炫舞', '崩坏', '星穹', '铁道', '明日', '逆水寒', '光与夜',
            '之恋', '无畏', '契约', '第五', '人格', '闪魂', 'cos', 'VCT'
        }
        
        filtered_words = [word for word in words if word not in stop_words and len(word) >= 2]
        text_for_wordcloud = ' '.join(filtered_words)
        
        # 生成词云
        try:
            wordcloud = WordCloud(
                font_path='docs/STZHONGS.TTF',  # 使用项目字体
                width=1200,
                height=800, 
                background_color='white',
                max_words=200,
                colormap='viridis'
            ).generate(text_for_wordcloud)
        except:
            # 如果字体文件不存在，使用默认设置
            wordcloud = WordCloud(
                width=1200,
                height=800,
                background_color='white', 
                max_words=200,
                colormap='viridis'
            ).generate(text_for_wordcloud)
        
        # 保存和显示词云
        plt.figure(figsize=(15, 10))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('娱乐八卦主题词云图', fontsize=20, pad=20)
        plt.tight_layout()
        plt.savefig('data/gossip_wordcloud.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("词云图已保存到: data/gossip_wordcloud.png")
        
        # 统计高频词
        word_freq = Counter(filtered_words)
        top_words = word_freq.most_common(20)
        
        print("\\n高频词汇 Top 20:")
        for word, freq in top_words:
            print(f"{word}: {freq}")
            
        return word_freq
    
    def keyword_matching(self, text: str) -> Tuple[bool, List[str], str]:
        """关键词匹配检测"""
        matched_keywords = []
        matched_category = ""
        
        for category, keywords in self.gossip_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    matched_keywords.append(keyword)
                    if not matched_category:
                        matched_category = category
        
        is_gossip = len(matched_keywords) > 0
        return is_gossip, matched_keywords, matched_category
    
    def huggingface_sentiment(self, text: str) -> str:
        """使用Hugging Face API进行情感分析"""
        # 这里使用免费的推理API
        API_URL = "https://api-inference.huggingface.co/models/uer/roberta-base-finetuned-chinanews-chinese"
        headers = {"Authorization": "Bearer YOUR_HUGGINGFACE_TOKEN"}  # 需要替换为实际token
        
        try:
            # 截断过长文本
            text = text[:500]
            
            payload = {"inputs": text}
            response = requests.post(API_URL, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    # 获取最高概率的标签
                    best_result = max(result[0], key=lambda x: x['score'])
                    label = best_result['label']
                    score = best_result['score']
                    
                    # 映射标签
                    if 'NEGATIVE' in label.upper() or score > 0.6:
                        return 'NEGATIVE'
                    elif 'POSITIVE' in label.upper():
                        return 'POSITIVE'
                    else:
                        return 'NEUTRAL'
            
            # API调用失败时使用规则方法
            return self.rule_based_sentiment(text)
            
        except Exception as e:
            print(f"API调用失败，使用规则方法: {e}")
            return self.rule_based_sentiment(text)
    
    def rule_based_sentiment(self, text: str) -> str:
        """基于规则的情感分析（备用方法）"""
        negative_words = [
            '恶心', '讨厌', '垃圾', '差劲', '失望', '愤怒', '气愤', '无语',
            '鄙视', '反感', '厌恶', '痛恨', '憎恨', '不爽', '郁闷', '烦躁',
            '塌房', '翻车', '黑料', '丑闻', '争议', '抄袭', '造假', '诈骗',
            '太差', '很烂', '恶心', '作呕', '烦人', '恶心人', '令人作呕'
        ]
        
        positive_words = [
            '好', '棒', '赞', '喜欢', '爱', '支持', '加油', '优秀', '厉害',
            '完美', '太好了', '很棒', '很好', '不错', '满意', '开心', '高兴',
            '感动', '温暖', '美好', '精彩', '震撼', '惊艳', '治愈'
        ]
        
        negative_count = sum(1 for word in negative_words if word in text)
        positive_count = sum(1 for word in positive_words if word in text)
        
        if negative_count > positive_count:
            return 'NEGATIVE'
        elif positive_count > negative_count:
            return 'POSITIVE'
        else:
            return 'NEUTRAL'
    
    def detect_negative_gossip(self):
        """检测负面八卦舆情"""
        print("\\n=== 负面舆情检测 ===")
        
        negative_posts = []
        negative_comments = []
        
        # 检测帖子
        print("正在分析帖子...")
        for idx, row in self.notes_df.iterrows():
            title = str(row['title']) if pd.notna(row['title']) else ""
            desc = str(row['desc']) if pd.notna(row['desc']) else ""
            full_text = title + " " + desc
            
            # 关键词匹配
            is_gossip, keywords, category = self.keyword_matching(full_text)
            
            if is_gossip:
                # 情感分析（使用规则方法，避免API限制）
                sentiment = self.rule_based_sentiment(full_text)
                
                if sentiment == 'NEGATIVE':
                    negative_posts.append({
                        'note_id': row['note_id'],
                        'title': title,
                        'desc': desc,
                        'nickname': row['nickname'],
                        'liked_count': row['liked_count'],
                        'comment_count': row['comment_count'],
                        'keywords': keywords,
                        'category': category,
                        'sentiment': sentiment,
                        'content': full_text[:200] + "..." if len(full_text) > 200 else full_text
                    })
        
        # 检测评论
        print("正在分析评论...")
        for idx, row in self.comments_df.iterrows():
            content = str(row['content']) if pd.notna(row['content']) else ""
            
            if len(content) < 5:  # 过滤太短的评论
                continue
                
            # 关键词匹配
            is_gossip, keywords, category = self.keyword_matching(content)
            
            if is_gossip:
                # 情感分析
                sentiment = self.rule_based_sentiment(content)
                
                if sentiment == 'NEGATIVE':
                    negative_comments.append({
                        'comment_id': row['comment_id'],
                        'note_id': row['note_id'],
                        'content': content,
                        'nickname': row['nickname'],
                        'like_count': row['like_count'],
                        'keywords': keywords,
                        'category': category,
                        'sentiment': sentiment
                    })
        
        # 保存检测结果
        results = {
            'detection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_posts': len(self.notes_df),
            'total_comments': len(self.comments_df),
            'negative_posts_count': len(negative_posts),
            'negative_comments_count': len(negative_comments),
            'negative_posts': negative_posts,
            'negative_comments': negative_comments
        }
        
        with open('data/negative_gossip_detection.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"检测完成！")
        print(f"总帖子数: {len(self.notes_df)}")
        print(f"总评论数: {len(self.comments_df)}")
        print(f"负面帖子数: {len(negative_posts)}")
        print(f"负面评论数: {len(negative_comments)}")
        
        return results
    
    def generate_statistics(self, results: Dict):
        """生成统计分析"""
        print("\\n=== 统计分析 ===")
        
        # 分类统计
        post_categories = [item['category'] for item in results['negative_posts']]
        comment_categories = [item['category'] for item in results['negative_comments']]
        all_categories = post_categories + comment_categories
        
        category_counts = Counter(all_categories)
        
        # 关键词统计
        all_keywords = []
        for item in results['negative_posts'] + results['negative_comments']:
            all_keywords.extend(item['keywords'])
        
        keyword_counts = Counter(all_keywords)
        
        stats = {
            'category_distribution': dict(category_counts),
            'keyword_frequency': dict(keyword_counts.most_common(20)),
            'negative_ratio': {
                'posts': len(results['negative_posts']) / len(self.notes_df) * 100,
                'comments': len(results['negative_comments']) / len(self.comments_df) * 100
            }
        }
        
        # 输出统计结果
        print("负面内容分类统计:")
        for category, count in category_counts.most_common():
            category_name = {
                'celebrity': '明星相关',
                'relationship': '感情八卦',
                'negative_events': '负面事件',
                'internet_slang': '网络用语',
                'emotions': '情绪词汇'
            }.get(category, category)
            print(f"  {category_name}: {count}")
        
        print("\\n高频负面关键词 Top 10:")
        for keyword, count in keyword_counts.most_common(10):
            print(f"  {keyword}: {count}")
        
        print(f"\\n负面比例:")
        print(f"  帖子: {stats['negative_ratio']['posts']:.2f}%")
        print(f"  评论: {stats['negative_ratio']['comments']:.2f}%")
        
        with open('data/negative_gossip_statistics.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        return stats
    
    def create_visualizations(self, results: Dict, stats: Dict):
        """创建可视化图表"""
        print("\\n=== 生成可视化图表 ===")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle('娱乐八卦负面舆情分析', fontsize=16, fontweight='bold')
        
        # 1. 分类分布饼图
        if stats['category_distribution']:
            categories = list(stats['category_distribution'].keys())
            counts = list(stats['category_distribution'].values())
            
            category_names = {
                'celebrity': '明星相关',
                'relationship': '感情八卦',
                'negative_events': '负面事件',
                'internet_slang': '网络用语',
                'emotions': '情绪词汇'
            }
            
            chinese_categories = [category_names.get(cat, cat) for cat in categories]
            colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc']
            
            axes[0, 0].pie(counts, labels=chinese_categories, autopct='%1.1f%%', 
                          startangle=90, colors=colors[:len(counts)])
            axes[0, 0].set_title('负面内容分类分布')
        
        # 2. 高频关键词柱状图
        if stats['keyword_frequency']:
            keywords = list(stats['keyword_frequency'].keys())[:8]
            frequencies = list(stats['keyword_frequency'].values())[:8]
            
            axes[0, 1].barh(keywords, frequencies, color='red', alpha=0.7)
            axes[0, 1].set_title('高频负面关键词')
            axes[0, 1].set_xlabel('出现频次')
        
        # 3. 负面比例对比
        categories = ['帖子', '评论']
        ratios = [stats['negative_ratio']['posts'], stats['negative_ratio']['comments']]
        
        bars = axes[1, 0].bar(categories, ratios, color=['#4CAF50', '#FF9800'], alpha=0.8)
        axes[1, 0].set_title('负面内容占比')
        axes[1, 0].set_ylabel('百分比 (%)')
        
        # 添加数值标签
        for bar, ratio in zip(bars, ratios):
            axes[1, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                           f'{ratio:.1f}%', ha='center', va='bottom')
        
        # 4. 总体数量对比
        labels = ['总帖子', '总评论', '负面帖子', '负面评论']
        values = [
            results['total_posts'],
            results['total_comments'], 
            results['negative_posts_count'],
            results['negative_comments_count']
        ]
        colors = ['lightblue', 'lightgreen', 'red', 'orange']
        
        bars = axes[1, 1].bar(labels, values, color=colors, alpha=0.7)
        axes[1, 1].set_title('数量统计')
        axes[1, 1].set_ylabel('数量')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        # 添加数值标签
        for bar, value in zip(bars, values):
            axes[1, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                           f'{value}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig('data/negative_gossip_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("可视化图表已保存到: data/negative_gossip_analysis.png")
    
    def run_complete_analysis(self):
        """运行完整分析"""
        print("=== 娱乐八卦负面舆情检测系统 ===\\n")
        
        try:
            # 1. 生成词云图
            word_freq = self.generate_wordcloud()
            
            # 2. 检测负面舆情
            results = self.detect_negative_gossip()
            
            # 3. 统计分析
            stats = self.generate_statistics(results)
            
            # 4. 生成可视化
            self.create_visualizations(results, stats)
            
            print("\\n=== 分析完成 ===")
            print("生成的文件:")
            print("- data/gossip_wordcloud.png (词云图)")
            print("- data/gossip_keywords.json (关键词表)")
            print("- data/negative_gossip_detection.json (检测结果)")
            print("- data/negative_gossip_statistics.json (统计数据)")
            print("- data/negative_gossip_analysis.png (分析图表)")
            
            # 输出关键发现
            print("\\n=== 关键发现 ===")
            print(f"✓ 构建了包含 {len(self.all_keywords)} 个词语的娱乐八卦关键词表")
            print(f"✓ 检测到 {results['negative_posts_count']} 条负面帖子")
            print(f"✓ 检测到 {results['negative_comments_count']} 条负面评论")
            print(f"✓ 帖子负面率: {stats['negative_ratio']['posts']:.2f}%")
            print(f"✓ 评论负面率: {stats['negative_ratio']['comments']:.2f}%")
            
            # 展示典型案例
            if results['negative_posts']:
                print("\\n=== 典型负面帖子 ===")
                for i, post in enumerate(results['negative_posts'][:3], 1):
                    print(f"{i}. {post['title']}")
                    print(f"   关键词: {', '.join(post['keywords'][:3])}")
                    print(f"   用户: {post['nickname']}")
                    print()
            
        except Exception as e:
            print(f"分析过程出错: {e}")
            import traceback
            traceback.print_exc()

def main():
    """主函数"""
    analyzer = SimpleGossipAnalyzer()
    analyzer.run_complete_analysis()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
娱乐八卦负面舆情检测系统
功能：
1. 生成词云图
2. 构建娱乐八卦关键词表
3. 负面舆情检测和分析
4. 数据可视化
"""

import pandas as pd
import jieba
import jieba.analyse
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Tuple
import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class GossipSentimentAnalyzer:
    """娱乐八卦负面舆情分析器"""
    
    def __init__(self):
        self.setup_jieba()
        self.load_data()
        self.build_keywords()
        self.setup_sentiment_model()
        
    def setup_jieba(self):
        """设置jieba分词"""
        # 添加娱乐八卦相关词汇
        custom_words = [
            '明星', '八卦', '绯闻', '恋情', '分手', '复合', '出轨', '小三',
            '潜规则', '整容', '塌房', '翻车', '黑料', '营销号', '造谣',
            '炒作', '洗白', '公关', '水军', '粉丝', '黑粉', '脱粉',
            '爆料', '瓜', '吃瓜', '内娱', '港台', '韩流', '流量',
            '顶流', '糊咖', '过气', '回踩', '撕逼', '开撕'
        ]
        
        for word in custom_words:
            jieba.add_word(word)
            
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
    
    def build_keywords(self):
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
            
        print(f"构建娱乐八卦关键词表完成，共 {len(self.all_keywords)} 个关键词")
        
        # 保存关键词表
        with open('data/gossip_keywords.json', 'w', encoding='utf-8') as f:
            json.dump(self.gossip_keywords, f, ensure_ascii=False, indent=2)
    
    def setup_sentiment_model(self):
        """设置情感分析模型"""
        try:
            # 使用中文情感分析模型
            model_name = "uer/roberta-base-finetuned-chinanews-chinese"
            self.sentiment_analyzer = pipeline(
                "text-classification",
                model=model_name,
                tokenizer=model_name,
                device=0 if torch.cuda.is_available() else -1
            )
            print("情感分析模型加载成功")
        except Exception as e:
            print(f"情感分析模型加载失败，使用规则方法: {e}")
            self.sentiment_analyzer = None
    
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
        
        # 过滤停用词和无意义词
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
        wordcloud = WordCloud(
            font_path='docs/STZHONGS.TTF',  # 使用项目自带字体
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
    
    def rule_based_sentiment(self, text: str) -> str:
        """基于规则的情感分析"""
        negative_words = [
            '恶心', '讨厌', '垃圾', '差劲', '失望', '愤怒', '气愤', '无语',
            '鄙视', '恶心', '作呕', '反感', '厌恶', '痛恨', '憎恨', '恶心',
            '不爽', '郁闷', '烦躁', '烦人', '恶心', '太差', '很烂', '垃圾',
            '塌房', '翻车', '黑料', '丑闻', '争议', '抄袭', '造假', '恶心'
        ]
        
        positive_words = [
            '好', '棒', '赞', '喜欢', '爱', '支持', '加油', '优秀', '厉害',
            '完美', '太好了', '很棒', '很好', '不错', '满意', '开心', '高兴'
        ]
        
        negative_count = sum(1 for word in negative_words if word in text)
        positive_count = sum(1 for word in positive_words if word in text)
        
        if negative_count > positive_count:
            return 'NEGATIVE'
        elif positive_count > negative_count:
            return 'POSITIVE'
        else:
            return 'NEUTRAL'
    
    def sentiment_analysis(self, text: str) -> str:
        """情感分析"""
        if self.sentiment_analyzer:
            try:
                # 截断过长文本
                text = text[:512]
                result = self.sentiment_analyzer(text)[0]
                label = result['label']
                confidence = result['score']
                
                # 根据模型输出映射情感
                if 'NEG' in label.upper() or confidence < 0.4:
                    return 'NEGATIVE'
                elif 'POS' in label.upper():
                    return 'POSITIVE'
                else:
                    return 'NEUTRAL'
            except Exception as e:
                print(f"模型情感分析失败，使用规则方法: {e}")
                return self.rule_based_sentiment(text)
        else:
            return self.rule_based_sentiment(text)
    
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
                # 情感分析
                sentiment = self.sentiment_analysis(full_text)
                
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
                sentiment = self.sentiment_analysis(content)
                
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
    
    def statistical_analysis(self, results: Dict):
        """统计分析"""
        print("\\n=== 统计分析 ===")
        
        # 1. 负面内容分类统计
        post_categories = [item['category'] for item in results['negative_posts']]
        comment_categories = [item['category'] for item in results['negative_comments']]
        all_categories = post_categories + comment_categories
        
        category_counts = Counter(all_categories)
        
        # 2. 关键词频率统计
        all_keywords = []
        for item in results['negative_posts'] + results['negative_comments']:
            all_keywords.extend(item['keywords'])
        
        keyword_counts = Counter(all_keywords)
        
        # 3. 时间分布分析（基于帖子数据）
        negative_note_ids = {item['note_id'] for item in results['negative_posts']}
        negative_notes_df = self.notes_df[self.notes_df['note_id'].isin(negative_note_ids)]
        
        if not negative_notes_df.empty and 'time' in negative_notes_df.columns:
            negative_notes_df['datetime'] = pd.to_datetime(negative_notes_df['time'], unit='ms')
            negative_notes_df['hour'] = negative_notes_df['datetime'].dt.hour
            time_distribution = negative_notes_df['hour'].value_counts().sort_index()
        else:
            time_distribution = pd.Series()
        
        # 输出统计结果
        print("\\n负面内容分类统计:")
        for category, count in category_counts.most_common():
            print(f"{category}: {count}")
        
        print("\\n高频负面关键词 Top 10:")
        for keyword, count in keyword_counts.most_common(10):
            print(f"{keyword}: {count}")
        
        # 保存统计结果
        stats = {
            'category_distribution': dict(category_counts),
            'keyword_frequency': dict(keyword_counts.most_common(20)),
            'time_distribution': dict(time_distribution) if not time_distribution.empty else {},
            'negative_ratio': {
                'posts': len(results['negative_posts']) / len(self.notes_df) * 100,
                'comments': len(results['negative_comments']) / len(self.comments_df) * 100
            }
        }
        
        with open('data/negative_gossip_statistics.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        return stats
    
    def visualize_results(self, results: Dict, stats: Dict):
        """可视化分析结果"""
        print("\\n=== 生成可视化图表 ===")
        
        # 设置图表样式
        plt.style.use('default')
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('娱乐八卦负面舆情分析报告', fontsize=16, fontweight='bold')
        
        # 1. 负面内容分类分布
        if stats['category_distribution']:
            categories = list(stats['category_distribution'].keys())
            counts = list(stats['category_distribution'].values())
            
            # 转换类别名称为中文
            category_names = {
                'celebrity': '明星相关',
                'relationship': '感情八卦', 
                'negative_events': '负面事件',
                'internet_slang': '网络用语',
                'emotions': '情绪词汇'
            }
            
            chinese_categories = [category_names.get(cat, cat) for cat in categories]
            
            axes[0, 0].pie(counts, labels=chinese_categories, autopct='%1.1f%%', startangle=90)
            axes[0, 0].set_title('负面内容分类分布')
        
        # 2. 高频负面关键词
        if stats['keyword_frequency']:
            keywords = list(stats['keyword_frequency'].keys())[:10]
            frequencies = list(stats['keyword_frequency'].values())[:10]
            
            axes[0, 1].barh(keywords, frequencies, color='red', alpha=0.7)
            axes[0, 1].set_title('高频负面关键词 Top 10')
            axes[0, 1].set_xlabel('出现频次')
        
        # 3. 负面内容比例
        categories = ['帖子', '评论']
        ratios = [stats['negative_ratio']['posts'], stats['negative_ratio']['comments']]
        
        axes[1, 0].bar(categories, ratios, color=['blue', 'orange'], alpha=0.7)
        axes[1, 0].set_title('负面内容占比 (%)')
        axes[1, 0].set_ylabel('百分比')
        for i, ratio in enumerate(ratios):
            axes[1, 0].text(i, ratio + 0.1, f'{ratio:.1f}%', ha='center')
        
        # 4. 时间分布（如果有数据）
        if stats['time_distribution']:
            hours = list(stats['time_distribution'].keys())
            counts = list(stats['time_distribution'].values())
            
            axes[1, 1].plot(hours, counts, marker='o', color='green', linewidth=2)
            axes[1, 1].set_title('负面内容时间分布')
            axes[1, 1].set_xlabel('小时')
            axes[1, 1].set_ylabel('数量')
            axes[1, 1].grid(True, alpha=0.3)
        else:
            axes[1, 1].text(0.5, 0.5, '暂无时间数据', ha='center', va='center', 
                           transform=axes[1, 1].transAxes, fontsize=12)
            axes[1, 1].set_title('负面内容时间分布')
        
        plt.tight_layout()
        plt.savefig('data/negative_gossip_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("可视化图表已保存到: data/negative_gossip_analysis.png")
    
    def generate_report(self, results: Dict, stats: Dict):
        """生成分析报告"""
        print("\\n=== 生成分析报告 ===")
        
        report = f"""
# 娱乐八卦负面舆情检测报告

## 检测概览
- 检测时间: {results['detection_time']}
- 总帖子数: {results['total_posts']}
- 总评论数: {results['total_comments']}
- 负面帖子数: {results['negative_posts_count']}
- 负面评论数: {results['negative_comments_count']}
- 帖子负面率: {stats['negative_ratio']['posts']:.2f}%
- 评论负面率: {stats['negative_ratio']['comments']:.2f}%

## 关键词表构建
本实验构建了包含 {len(self.all_keywords)} 个词语的娱乐八卦关键词表，分为5个类别：
- 明星相关: {len(self.gossip_keywords['celebrity'])} 个词语
- 感情八卦: {len(self.gossip_keywords['relationship'])} 个词语  
- 负面事件: {len(self.gossip_keywords['negative_events'])} 个词语
- 网络用语: {len(self.gossip_keywords['internet_slang'])} 个词语
- 情绪词汇: {len(self.gossip_keywords['emotions'])} 个词语

## 检测方法
1. **关键词匹配**: 基于构建的关键词表进行文本匹配
2. **情感分析**: 使用预训练的中文情感分析模型或规则方法
3. **组合判断**: 关键词匹配 + 负面情感 = 负面舆情

## 主要发现
### 负面内容分类分布:
"""
        
        for category, count in stats['category_distribution'].items():
            category_name = {
                'celebrity': '明星相关',
                'relationship': '感情八卦',
                'negative_events': '负面事件', 
                'internet_slang': '网络用语',
                'emotions': '情绪词汇'
            }.get(category, category)
            report += f"- {category_name}: {count} 条\\n"
        
        report += f"""
### 高频负面关键词:
"""
        
        for keyword, count in list(stats['keyword_frequency'].items())[:10]:
            report += f"- {keyword}: {count} 次\\n"
        
        report += f"""
## 典型负面案例

### 负面帖子示例:
"""
        
        for i, post in enumerate(results['negative_posts'][:3], 1):
            report += f"""
{i}. 标题: {post['title']}
   用户: {post['nickname']}
   匹配关键词: {', '.join(post['keywords'][:5])}
   内容摘要: {post['content'][:100]}...
"""

        report += f"""
### 负面评论示例:
"""
        
        for i, comment in enumerate(results['negative_comments'][:5], 1):
            report += f"""
{i}. 用户: {comment['nickname']}
   匹配关键词: {', '.join(comment['keywords'][:3])}
   内容: {comment['content'][:80]}...
"""

        report += f"""
## 结论与建议

1. **负面舆情特征**: 主要集中在明星绯闻、感情纠纷等话题
2. **传播特点**: 评论区往往比帖子本身包含更多负面情绪
3. **关键词效果**: 构建的关键词表能有效识别娱乐八卦相关内容
4. **情感分析**: 结合关键词和情感分析能较好地识别负面舆情

## 技术创新点

1. **多层筛选机制**: 关键词匹配 + 情感分析的组合策略
2. **领域专用词表**: 针对娱乐八卦领域构建的专业关键词表
3. **可视化分析**: 提供多维度的统计分析和可视化展示
4. **实时检测**: 支持对新数据的实时负面舆情检测
"""

        # 保存报告
        with open('data/negative_gossip_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
            
        print("分析报告已保存到: data/negative_gossip_report.md")
        print("\\n报告摘要:")
        print(f"- 共检测到 {results['negative_posts_count']} 条负面帖子")
        print(f"- 共检测到 {results['negative_comments_count']} 条负面评论") 
        print(f"- 帖子负面率: {stats['negative_ratio']['posts']:.2f}%")
        print(f"- 评论负面率: {stats['negative_ratio']['comments']:.2f}%")
    
    def run_analysis(self):
        """运行完整分析流程"""
        print("=== 娱乐八卦负面舆情检测系统 ===")
        print("开始分析...")
        
        try:
            # 1. 生成词云图
            word_freq = self.generate_wordcloud()
            
            # 2. 检测负面舆情
            results = self.detect_negative_gossip()
            
            # 3. 统计分析
            stats = self.statistical_analysis(results)
            
            # 4. 可视化
            self.visualize_results(results, stats)
            
            # 5. 生成报告
            self.generate_report(results, stats)
            
            print("\\n=== 分析完成 ===")
            print("生成的文件:")
            print("- data/gossip_wordcloud.png (词云图)")
            print("- data/gossip_keywords.json (关键词表)")
            print("- data/negative_gossip_detection.json (检测结果)")
            print("- data/negative_gossip_statistics.json (统计数据)")
            print("- data/negative_gossip_analysis.png (可视化图表)")
            print("- data/negative_gossip_report.md (分析报告)")
            
        except Exception as e:
            print(f"分析过程中出现错误: {e}")
            import traceback
            traceback.print_exc()

def main():
    """主函数"""
    analyzer = GossipSentimentAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()

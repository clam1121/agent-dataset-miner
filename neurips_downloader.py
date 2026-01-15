"""
NeurIPS论文下载模块
从NeurIPS Proceedings和OpenReview获取Spotlight和Best论文
"""

import os
import requests
import time
import logging
from pathlib import Path
from typing import Generator, Tuple, Optional, List, Dict
from bs4 import BeautifulSoup
import json
import re

logger = logging.getLogger(__name__)


class NeurIPSDownloader:
    """NeurIPS论文下载器"""
    
    def __init__(self, year: int = 2025, temp_dir: str = "temp"):
        """
        初始化下载器
        
        Args:
            year: NeurIPS年份
            temp_dir: 临时文件目录
        """
        self.year = year
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # NeurIPS相关URL
        self.proceedings_url = f"https://papers.nips.cc/paper_files/paper/{year}"
        self.neurips_cc_url = f"https://neurips.cc/Conferences/{year}"
        
        # OpenReview (NeurIPS也使用OpenReview)
        self.openreview_venue = f"NeurIPS.cc/{year}/Conference"
        
        # 论文类型（NeurIPS的分类）
        self.categories = ['spotlight', 'oral']  # oral通常包含best papers
        
        logger.info(f"成功初始化NeurIPS下载器 ({year})")
    
    def get_papers_from_openreview(self) -> List[Dict]:
        """
        从OpenReview获取NeurIPS论文列表
        
        Returns:
            论文信息列表
        """
        papers = []
        
        try:
            import openreview
            
            # 初始化OpenReview客户端
            client = openreview.api.OpenReviewClient(
                baseurl='https://api2.openreview.net'
            )
            
            logger.info(f"正在从OpenReview获取NeurIPS {self.year}论文...")
            
            # 获取所有投稿
            submissions = client.get_all_notes(
                invitation=f'{self.openreview_venue}/-/Submission',
                details='directReplies'
            )
            
            logger.info(f"找到 {len(submissions)} 篇投稿")
            
            for submission in submissions:
                try:
                    # 获取论文类别
                    category = self._get_paper_category_openreview(submission)
                    
                    if category not in ['spotlight', 'oral', 'best']:
                        continue
                    
                    # 提取论文信息
                    title = submission.content.get('title', {})
                    if isinstance(title, dict):
                        title = title.get('value', 'untitled')
                    
                    # 获取PDF URL
                    pdf_url = submission.content.get('pdf', {})
                    if isinstance(pdf_url, dict):
                        pdf_url = pdf_url.get('value', '')
                    
                    if pdf_url and pdf_url.startswith('/pdf/'):
                        pdf_url = f"https://openreview.net{pdf_url}"
                    elif not pdf_url and hasattr(submission, 'id'):
                        pdf_url = f"https://openreview.net/pdf?id={submission.id}"
                    
                    papers.append({
                        'title': title,
                        'submission_id': submission.id if hasattr(submission, 'id') else '',
                        'url': f"https://openreview.net/forum?id={submission.id}" if hasattr(submission, 'id') else '',
                        'pdf_url': pdf_url,
                        'category': category,
                        'source': 'openreview'
                    })
                    
                except Exception as e:
                    logger.debug(f"处理OpenReview论文时出错: {str(e)}")
                    continue
            
            logger.info(f"从OpenReview获取到 {len(papers)} 篇Spotlight/Oral论文")
            
        except Exception as e:
            logger.error(f"OpenReview获取失败: {str(e)}")
        
        return papers
    
    def _get_paper_category_openreview(self, submission) -> Optional[str]:
        """
        从OpenReview submission判断论文类别
        
        Args:
            submission: OpenReview提交对象
            
        Returns:
            类别名称或None
        """
        # 检查venue字段
        venue = submission.content.get('venue', {})
        if isinstance(venue, dict):
            venue = venue.get('value', '')
        
        venue_lower = str(venue).lower()
        
        if 'best' in venue_lower or 'award' in venue_lower:
            return 'best'
        elif 'oral' in venue_lower:
            return 'oral'
        elif 'spotlight' in venue_lower:
            return 'spotlight'
        
        # 检查decision
        if hasattr(submission, 'details') and 'directReplies' in submission.details:
            for reply in submission.details['directReplies']:
                if 'Decision' in reply.get('invitation', ''):
                    cont = reply.get('content', {}) or {}
                    val = cont.get('decision', cont.get('recommendation', ''))
                    if isinstance(val, dict):
                        val = val.get('value', '')
                    val_lower = str(val).lower()
                    
                    if 'best' in val_lower or 'award' in val_lower:
                        return 'best'
                    elif 'oral' in val_lower:
                        return 'oral'
                    elif 'spotlight' in val_lower:
                        return 'spotlight'
        
        return None
    
    def get_papers_from_proceedings(self) -> List[Dict]:
        """
        从NeurIPS Proceedings网站获取论文列表
        
        Returns:
            论文信息列表
        """
        papers = []
        
        try:
            logger.info(f"正在从Proceedings获取NeurIPS {self.year}论文...")
            
            # 访问proceedings页面
            response = requests.get(self.proceedings_url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"无法访问Proceedings，状态码: {response.status_code}")
                return papers
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # NeurIPS proceedings的HTML结构
            # 查找所有论文项
            paper_items = soup.find_all('li', class_='paper')
            
            if not paper_items:
                # 尝试其他可能的结构
                paper_items = soup.find_all('div', class_='paper-container')
            
            for item in paper_items:
                try:
                    # 提取标题
                    title_tag = item.find('a', class_='paper-title')
                    if not title_tag:
                        title_tag = item.find('h4') or item.find('h3')
                    
                    if not title_tag:
                        continue
                    
                    title = title_tag.text.strip()
                    paper_url = title_tag.get('href', '')
                    
                    if paper_url and not paper_url.startswith('http'):
                        paper_url = f"https://papers.nips.cc{paper_url}"
                    
                    # 查找PDF链接
                    pdf_link = item.find('a', text=re.compile('Paper|PDF', re.I))
                    pdf_url = pdf_link.get('href', '') if pdf_link else ''
                    
                    if pdf_url and not pdf_url.startswith('http'):
                        pdf_url = f"https://papers.nips.cc{pdf_url}"
                    
                    # 判断类别（从标签或类名）
                    category = 'poster'  # 默认
                    
                    # 查找spotlight或oral标记
                    category_tag = item.find(class_=re.compile('spotlight|oral|best', re.I))
                    if category_tag:
                        cat_text = category_tag.text.lower()
                        if 'best' in cat_text or 'award' in cat_text:
                            category = 'best'
                        elif 'oral' in cat_text:
                            category = 'oral'
                        elif 'spotlight' in cat_text:
                            category = 'spotlight'
                    
                    # 只保留spotlight和oral/best论文
                    if category in ['spotlight', 'oral', 'best']:
                        papers.append({
                            'title': title,
                            'url': paper_url,
                            'pdf_url': pdf_url,
                            'category': category,
                            'source': 'proceedings'
                        })
                
                except Exception as e:
                    logger.debug(f"解析论文项时出错: {str(e)}")
                    continue
            
            logger.info(f"从Proceedings获取到 {len(papers)} 篇Spotlight/Oral论文")
            
        except Exception as e:
            logger.error(f"Proceedings获取失败: {str(e)}")
        
        return papers
    
    def get_papers_from_neurips_cc(self) -> List[Dict]:
        """
        从neurips.cc官网获取论文信息（通常有awards信息）
        
        Returns:
            论文信息列表
        """
        papers = []
        
        try:
            logger.info(f"正在从neurips.cc获取获奖论文信息...")
            
            # 访问会议页面
            url = f"{self.neurips_cc_url}/Awards"
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"无法访问Awards页面，状态码: {response.status_code}")
                return papers
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找获奖论文
            award_sections = soup.find_all(['div', 'section'], class_=re.compile('award', re.I))
            
            for section in award_sections:
                try:
                    # 提取论文标题
                    title_tag = section.find(['h3', 'h4', 'strong'])
                    if not title_tag:
                        continue
                    
                    title = title_tag.text.strip()
                    
                    # 查找链接
                    link_tag = section.find('a', href=True)
                    paper_url = link_tag.get('href', '') if link_tag else ''
                    
                    if paper_url:
                        papers.append({
                            'title': title,
                            'url': paper_url,
                            'pdf_url': paper_url if paper_url.endswith('.pdf') else '',
                            'category': 'best',
                            'source': 'neurips.cc'
                        })
                
                except Exception as e:
                    logger.debug(f"解析获奖论文时出错: {str(e)}")
                    continue
            
            logger.info(f"从neurips.cc获取到 {len(papers)} 篇获奖论文")
            
        except Exception as e:
            logger.error(f"neurips.cc获取失败: {str(e)}")
        
        return papers
    
    def download_and_process_papers(self) -> Generator[Tuple[str, str, dict], None, None]:
        """
        下载论文并逐个返回，用于流式处理
        
        Yields:
            (pdf_path, category, paper_info): PDF路径、类别、论文信息
        """
        logger.info(f"开始获取NeurIPS {self.year}论文列表...")
        
        all_papers = []
        
        # 方法1: 尝试从OpenReview获取
        logger.info("\n方法1: 尝试从OpenReview获取...")
        openreview_papers = self.get_papers_from_openreview()
        if openreview_papers:
            all_papers.extend(openreview_papers)
        
        # 方法2: 从Proceedings获取
        logger.info("\n方法2: 尝试从Proceedings获取...")
        proceedings_papers = self.get_papers_from_proceedings()
        if proceedings_papers:
            all_papers.extend(proceedings_papers)
        
        # 方法3: 从neurips.cc获取获奖论文
        logger.info("\n方法3: 尝试从neurips.cc获取获奖论文...")
        award_papers = self.get_papers_from_neurips_cc()
        if award_papers:
            all_papers.extend(award_papers)
        
        # 去重（基于标题）
        seen_titles = set()
        unique_papers = []
        for paper in all_papers:
            title_lower = paper['title'].lower().strip()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_papers.append(paper)
        
        logger.info(f"\n总计找到 {len(unique_papers)} 篇唯一的Spotlight/Best论文")
        
        if not unique_papers:
            logger.warning("未找到任何论文，可能会议论文尚未发布")
            return
        
        # 按类别统计
        category_counts = {}
        for paper in unique_papers:
            cat = paper['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        logger.info(f"类别统计: {category_counts}")
        
        # 下载并处理每篇论文
        processed_count = 0
        
        for paper in unique_papers:
            try:
                if not paper.get('pdf_url'):
                    logger.warning(f"论文无PDF链接，跳过: {paper['title']}")
                    continue
                
                # 下载PDF
                pdf_path = self._download_pdf(
                    paper['pdf_url'],
                    paper['title'],
                    paper['category']
                )
                
                if pdf_path:
                    processed_count += 1
                    logger.info(f"[{paper['category'].upper()}] 已下载 ({processed_count}/{len(unique_papers)}): {paper['title']}")
                    
                    # 返回PDF路径供处理
                    yield pdf_path, paper['category'], paper
                    
                else:
                    logger.warning(f"下载失败: {paper['title']}")
                
                # 避免请求过快
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"处理论文时出错: {str(e)}")
                continue
        
        logger.info(f"完成！共处理 {processed_count} 篇论文")
    
    def _download_pdf(self, url: str, title: str, category: str) -> Optional[str]:
        """
        下载PDF文件
        
        Args:
            url: PDF URL
            title: 论文标题
            category: 论文类别
            
        Returns:
            本地PDF路径或None
        """
        # 清理文件名
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title[:100]  # 限制长度
        
        filename = f"NeurIPS_{category}_{safe_title}.pdf"
        filepath = self.temp_dir / filename
        
        try:
            response = requests.get(url, timeout=60, allow_redirects=True)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                logger.debug(f"PDF已保存: {filepath}")
                return str(filepath)
            else:
                logger.warning(f"下载失败 (状态码: {response.status_code})")
                return None
                
        except Exception as e:
            logger.error(f"下载PDF失败: {str(e)}")
            return None


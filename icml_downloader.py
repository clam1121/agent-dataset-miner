"""
ICML论文下载模块
从PMLR (Proceedings of Machine Learning Research) 和 OpenReview获取ICML论文
"""

import os
import requests
import time
import logging
from pathlib import Path
from typing import Generator, Tuple, Optional, List, Dict
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class ICMLDownloader:
    """ICML论文下载器"""
    
    def __init__(self, year: int = 2025, temp_dir: str = "temp"):
        """
        初始化下载器
        
        Args:
            year: ICML年份
            temp_dir: 临时文件目录
        """
        self.year = year
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # PMLR相关URL
        # ICML论文发布在PMLR (Proceedings of Machine Learning Research)
        # Volume编号规律：ICML 2024是v235, 2023是v202, 2022是v162
        self.volume_map = {
            2025: 'v268',  # 预估（待确认）
            2024: 'v235',
            2023: 'v202',
            2022: 'v162',
            2021: 'v139',
            2020: 'v119',
        }
        
        self.pmlr_base_url = "https://proceedings.mlr.press"
        self.volume = self.volume_map.get(year, f'v{200 + (year - 2020) * 30}')  # 估算
        
        # OpenReview (ICML近年来也使用OpenReview)
        self.openreview_venue = f"ICML.cc/{year}/Conference"
        
        # 论文类型
        self.categories = ['oral', 'spotlight']
        
        logger.info(f"成功初始化ICML下载器 ({year}, Volume: {self.volume})")
    
    def get_papers_from_pmlr(self) -> List[Dict]:
        """
        从PMLR获取ICML论文列表
        
        Returns:
            论文信息列表
        """
        papers = []
        
        try:
            url = f"{self.pmlr_base_url}/{self.volume}"
            logger.info(f"正在从PMLR获取论文列表: {url}")
            
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"无法访问PMLR，状态码: {response.status_code}")
                return papers
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # PMLR的HTML结构：查找所有论文项
            # 通常在 <div class="paper"> 或类似结构中
            paper_items = soup.find_all('div', class_='paper')
            
            if not paper_items:
                # 尝试其他可能的结构
                paper_items = soup.find_all('p', class_='links')
                if paper_items:
                    # 如果找到的是links，需要找到对应的标题
                    paper_items = soup.find_all(['div', 'article'], recursive=True)
            
            for item in paper_items:
                try:
                    # 提取标题
                    title_tag = item.find('span', class_='title') or item.find('h3') or item.find('h4')
                    
                    if not title_tag:
                        # 尝试查找链接中的标题
                        title_link = item.find('a', href=re.compile(r'\.html$'))
                        if title_link:
                            title_tag = title_link
                    
                    if not title_tag:
                        continue
                    
                    title = title_tag.text.strip()
                    
                    # 提取论文页面URL
                    paper_link = item.find('a', text=re.compile('abs|Abstract', re.I))
                    if not paper_link:
                        paper_link = item.find('a', href=re.compile(r'\.html$'))
                    
                    paper_url = paper_link.get('href', '') if paper_link else ''
                    if paper_url and not paper_url.startswith('http'):
                        paper_url = f"{self.pmlr_base_url}/{paper_url}"
                    
                    # 提取PDF链接
                    pdf_link = item.find('a', text=re.compile('Download PDF|PDF', re.I))
                    if not pdf_link:
                        pdf_link = item.find('a', href=re.compile(r'\.pdf$'))
                    
                    pdf_url = pdf_link.get('href', '') if pdf_link else ''
                    if pdf_url and not pdf_url.startswith('http'):
                        pdf_url = f"{self.pmlr_base_url}/{pdf_url}"
                    
                    # 判断类别（从标签或文本）
                    category = 'poster'  # 默认
                    
                    # 查找oral或spotlight标记
                    item_text = item.get_text().lower()
                    if 'oral' in item_text or 'outstanding' in item_text:
                        category = 'oral'
                    elif 'spotlight' in item_text:
                        category = 'spotlight'
                    
                    # 检查是否有awards标记
                    if 'award' in item_text or 'best' in item_text:
                        category = 'best'
                    
                    # 只保留oral, spotlight和best
                    if category in ['oral', 'spotlight', 'best']:
                        papers.append({
                            'title': title,
                            'url': paper_url,
                            'pdf_url': pdf_url,
                            'category': category,
                            'source': 'pmlr'
                        })
                
                except Exception as e:
                    logger.debug(f"解析论文项时出错: {str(e)}")
                    continue
            
            logger.info(f"从PMLR获取到 {len(papers)} 篇Oral/Spotlight论文")
            
        except Exception as e:
            logger.error(f"PMLR获取失败: {str(e)}")
        
        return papers
    
    def get_papers_from_openreview(self) -> List[Dict]:
        """
        从OpenReview获取ICML论文列表
        
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
            
            logger.info(f"正在从OpenReview获取ICML {self.year}论文...")
            
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
        
        if 'best' in venue_lower or 'award' in venue_lower or 'outstanding' in venue_lower:
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
                    
                    if 'best' in val_lower or 'award' in val_lower or 'outstanding' in val_lower:
                        return 'best'
                    elif 'oral' in val_lower:
                        return 'oral'
                    elif 'spotlight' in val_lower:
                        return 'spotlight'
        
        return None
    
    def download_and_process_papers(self) -> Generator[Tuple[str, str, dict], None, None]:
        """
        下载论文并逐个返回，用于流式处理
        
        Yields:
            (pdf_path, category, paper_info): PDF路径、类别、论文信息
        """
        logger.info(f"开始获取ICML {self.year}论文列表...")
        
        all_papers = []
        
        # 方法1: 尝试从PMLR获取
        logger.info("\n方法1: 尝试从PMLR获取...")
        pmlr_papers = self.get_papers_from_pmlr()
        if pmlr_papers:
            all_papers.extend(pmlr_papers)
        
        # 方法2: 从OpenReview获取
        logger.info("\n方法2: 尝试从OpenReview获取...")
        openreview_papers = self.get_papers_from_openreview()
        if openreview_papers:
            all_papers.extend(openreview_papers)
        
        # 去重（基于标题）
        seen_titles = set()
        unique_papers = []
        for paper in all_papers:
            title_lower = paper['title'].lower().strip()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_papers.append(paper)
        
        logger.info(f"\n总计找到 {len(unique_papers)} 篇唯一的Oral/Spotlight论文")
        
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
        
        filename = f"ICML_{category}_{safe_title}.pdf"
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




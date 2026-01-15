"""
ICLR论文下载模块
从OpenReview下载ICLR 2025的论文PDF
"""

import openreview
import os
import requests
import time
import logging
from pathlib import Path
from typing import Generator, Tuple, Optional

logger = logging.getLogger(__name__)


class ICLRDownloader:
    """ICLR论文下载器"""
    
    def __init__(self, year: int = 2025, temp_dir: str = "temp"):
        """
        初始化下载器
        
        Args:
            year: ICLR年份
            temp_dir: 临时文件目录
        """
        self.year = year
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.venue_id = f'ICLR.cc/{year}/Conference'
        self.categories = ['Oral', 'Spotlight', 'Poster']
        
        # 初始化OpenReview客户端
        try:
            self.client = openreview.api.OpenReviewClient(
                baseurl='https://api2.openreview.net'
            )
            logger.info(f"成功初始化OpenReview客户端 (ICLR {year})")
        except Exception as e:
            logger.error(f"初始化OpenReview客户端失败: {str(e)}")
            raise
            
    def download_and_process_papers(self) -> Generator[Tuple[str, str, dict], None, None]:
        """
        下载论文并逐个返回，用于流式处理
        
        Yields:
            (pdf_path, category, paper_info): PDF路径、类别、论文信息
        """
        logger.info(f"开始获取ICLR {self.year}论文列表...")
        
        try:
            # 获取所有投稿
            submissions = self.client.get_all_notes(
                invitation=f'{self.venue_id}/-/Submission',
                details='directReplies'
            )
            
            logger.info(f"找到 {len(submissions)} 篇投稿")
            
            processed_count = 0
            
            for submission in submissions:
                try:
                    # 判断类别
                    category = self._get_paper_category(submission)
                    
                    if category not in self.categories:
                        continue
                    
                    # 获取论文信息
                    paper_info = self._extract_paper_info(submission)
                    
                    # 获取PDF URL
                    pdf_url = self._get_pdf_url(submission)
                    
                    if not pdf_url:
                        logger.warning(f"未找到PDF链接: {paper_info['title']}")
                        continue
                    
                    # 下载PDF到临时目录
                    pdf_path = self._download_pdf(pdf_url, paper_info['title'], category)
                    
                    if pdf_path:
                        processed_count += 1
                        logger.info(f"[{category}] 已下载 ({processed_count}): {paper_info['title']}")
                        
                        # 返回PDF路径供处理
                        yield pdf_path, category, paper_info
                        
                        # 注意：调用方处理完后需要删除文件
                        
                except Exception as e:
                    logger.error(f"处理论文时出错: {str(e)}")
                    continue
                    
            logger.info(f"完成！共处理 {processed_count} 篇论文")
            
        except Exception as e:
            logger.error(f"获取论文列表失败: {str(e)}")
            raise
    
    def _get_paper_category(self, submission) -> Optional[str]:
        """
        判断论文类别 (Oral/Spotlight/Poster)
        
        Args:
            submission: OpenReview提交对象
            
        Returns:
            类别名称或None
        """
        # 方法1: 从venue字段提取
        venue = submission.content.get('venue', {})
        if isinstance(venue, dict):
            venue = venue.get('value', '')
        
        venue_lower = str(venue).lower()
        if 'oral' in venue_lower:
            return 'Oral'
        elif 'spotlight' in venue_lower:
            return 'Spotlight'
        elif 'poster' in venue_lower:
            return 'Poster'
        
        # 方法2: 从venueid检查是否被拒绝
        venueid = submission.content.get('venueid', {})
        if isinstance(venueid, dict):
            venueid = venueid.get('value', '')
        
        venueid_lower = str(venueid).lower()
        if 'rejected' in venueid_lower or 'withdrawn' in venueid_lower:
            return None
        
        # 方法3: 从决策中提取
        if hasattr(submission, 'details') and 'directReplies' in submission.details:
            for reply in submission.details['directReplies']:
                if 'Decision' in reply.get('invitation', ''):
                    cont = reply.get('content', {}) or {}
                    val = cont.get('decision', cont.get('recommendation', cont.get('presentation', '')))
                    if isinstance(val, dict):
                        val = val.get('value', '')
                    val_lower = str(val).lower()
                    
                    if 'oral' in val_lower:
                        return 'Oral'
                    elif 'spotlight' in val_lower:
                        return 'Spotlight'
                    elif 'poster' in val_lower:
                        return 'Poster'
                    elif 'accept' in val_lower:
                        return 'Poster'  # 默认接收为Poster
        
        return None
    
    def _extract_paper_info(self, submission) -> dict:
        """
        提取论文基本信息
        
        Args:
            submission: OpenReview提交对象
            
        Returns:
            论文信息字典
        """
        title = submission.content.get('title', {})
        if isinstance(title, dict):
            title = title.get('value', 'untitled')
        
        return {
            'title': title,
            'submission_id': submission.id if hasattr(submission, 'id') else '',
            'openreview_url': f"https://openreview.net/forum?id={submission.id}" if hasattr(submission, 'id') else ''
        }
    
    def _get_pdf_url(self, submission) -> Optional[str]:
        """
        获取PDF下载链接
        
        Args:
            submission: OpenReview提交对象
            
        Returns:
            PDF URL或None
        """
        pdf_url = submission.content.get('pdf', {})
        if isinstance(pdf_url, dict):
            pdf_url = pdf_url.get('value', '')
        
        # 修复相对路径
        if pdf_url and pdf_url.startswith('/pdf/'):
            pdf_url = f"https://openreview.net{pdf_url}"
        elif not pdf_url and hasattr(submission, 'id'):
            pdf_url = f"https://openreview.net/pdf?id={submission.id}"
        
        return pdf_url if pdf_url else None
    
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
        
        filename = f"{category}_{safe_title}.pdf"
        filepath = self.temp_dir / filename
        
        try:
            response = requests.get(url, timeout=60)
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




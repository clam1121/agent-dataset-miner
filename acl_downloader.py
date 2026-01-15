"""
ACL Anthology论文下载模块
从ACL Anthology下载2025年的Main和Findings论文
"""

import os
import requests
import time
import logging
from pathlib import Path
from typing import Generator, Tuple, Optional, List
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)


class ACLDownloader:
    """ACL Anthology论文下载器"""
    
    def __init__(self, year: int = 2025, temp_dir: str = "temp"):
        """
        初始化下载器
        
        Args:
            year: 年份
            temp_dir: 临时文件目录
        """
        self.year = year
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # ACL Anthology API基础URL
        self.base_url = "https://aclanthology.org"
        self.api_url = "https://aclanthology.org"
        
        # 2025年的会议标识符（根据ACL命名规则）
        # 格式通常是: {year}.{venue}-{type}.{number}
        self.venues = {
            'ACL': f'{year}.acl',      # ACL 2025
            'EMNLP': f'{year}.emnlp',  # EMNLP 2025
            'NAACL': f'{year}.naacl',  # NAACL 2025
            'EACL': f'{year}.eacl',    # EACL 2025
        }
        
        self.categories = ['main', 'findings']
        
        logger.info(f"成功初始化ACL Anthology下载器 ({year})")
    
    def get_paper_list_from_anthology(self, venue: str, category: str) -> List[dict]:
        """
        从ACL Anthology获取论文列表
        
        Args:
            venue: 会议名称 (ACL, EMNLP等)
            category: 类别 (main, findings)
            
        Returns:
            论文信息列表
        """
        papers = []
        
        # 构建anthology ID，例如: 2025.acl-long, 2025.acl-findings
        if category == 'main':
            anthology_id = f"{self.venues[venue]}-long"
        else:  # findings
            anthology_id = f"{self.venues[venue]}-{category}"
        
        logger.info(f"正在获取 {anthology_id} 的论文列表...")
        
        try:
            # 访问anthology的事件页面
            url = f"{self.base_url}/events/{venue.lower()}-{self.year}/"
            logger.info(f"访问URL: {url}")
            
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"无法访问 {url}, 状态码: {response.status_code}")
                return papers
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找对应track的论文
            # ACL Anthology的HTML结构：通常在<p class="d-sm-flex align-items-stretch">中
            paper_items = soup.find_all('p', class_='d-sm-flex')
            
            for item in paper_items:
                try:
                    # 提取论文标题
                    title_tag = item.find('strong')
                    if not title_tag:
                        title_tag = item.find('span', class_='d-block')
                    
                    if not title_tag:
                        continue
                    
                    title_link = title_tag.find('a')
                    if not title_link:
                        continue
                    
                    title = title_link.text.strip()
                    paper_url = title_link.get('href', '')
                    
                    if not paper_url.startswith('http'):
                        paper_url = f"{self.base_url}{paper_url}"
                    
                    # 提取anthology ID（从URL中）
                    anthology_paper_id = paper_url.split('/')[-2] if '/' in paper_url else ''
                    
                    # 检查是否属于目标类别
                    if category == 'main' and 'long' not in anthology_paper_id.lower():
                        continue
                    if category == 'findings' and 'findings' not in anthology_paper_id.lower():
                        continue
                    
                    # 构建PDF URL
                    pdf_url = f"{self.base_url}/{anthology_paper_id}.pdf"
                    
                    papers.append({
                        'title': title,
                        'anthology_id': anthology_paper_id,
                        'url': paper_url,
                        'pdf_url': pdf_url,
                        'venue': venue,
                        'category': category
                    })
                    
                except Exception as e:
                    logger.debug(f"解析论文项时出错: {str(e)}")
                    continue
            
            logger.info(f"找到 {len(papers)} 篇 {anthology_id} 论文")
            
        except Exception as e:
            logger.error(f"获取论文列表失败: {str(e)}")
        
        return papers
    
    def get_papers_from_bib(self, venue: str, category: str) -> List[dict]:
        """
        通过BibTeX文件获取论文列表（备用方法）
        
        Args:
            venue: 会议名称
            category: 类别
            
        Returns:
            论文信息列表
        """
        papers = []
        
        # 构建anthology ID
        if category == 'main':
            volume_id = f"{self.venues[venue]}-long"
        else:
            volume_id = f"{self.venues[venue]}-{category}"
        
        try:
            # 下载BibTeX文件
            bib_url = f"{self.base_url}/volumes/{volume_id}.bib"
            logger.info(f"尝试下载BibTeX: {bib_url}")
            
            response = requests.get(bib_url, timeout=30)
            
            if response.status_code == 200:
                # 解析BibTeX（简单解析）
                bib_text = response.text
                entries = bib_text.split('@inproceedings{')
                
                for entry in entries[1:]:  # 跳过第一个空项
                    try:
                        # 提取anthology ID
                        anthology_id = entry.split(',')[0].strip()
                        
                        # 提取标题
                        title_match = entry.split('title = "')[1].split('"')[0] if 'title = "' in entry else ''
                        
                        if anthology_id and title_match:
                            papers.append({
                                'title': title_match,
                                'anthology_id': anthology_id,
                                'url': f"{self.base_url}/{anthology_id}",
                                'pdf_url': f"{self.base_url}/{anthology_id}.pdf",
                                'venue': venue,
                                'category': category
                            })
                    except:
                        continue
                
                logger.info(f"从BibTeX解析到 {len(papers)} 篇论文")
        
        except Exception as e:
            logger.warning(f"BibTeX方法失败: {str(e)}")
        
        return papers
    
    def download_and_process_papers(self) -> Generator[Tuple[str, str, dict], None, None]:
        """
        下载论文并逐个返回，用于流式处理
        
        Yields:
            (pdf_path, category, paper_info): PDF路径、类别、论文信息
        """
        logger.info(f"开始获取ACL {self.year}论文列表...")
        
        all_papers = []
        
        # 遍历所有会议和类别
        for venue in self.venues.keys():
            for category in self.categories:
                logger.info(f"\n正在获取 {venue} {category} 论文...")
                
                # 尝试两种方法获取论文列表
                papers = self.get_paper_list_from_anthology(venue, category)
                
                if not papers:
                    logger.info(f"尝试使用BibTeX方法...")
                    papers = self.get_papers_from_bib(venue, category)
                
                if papers:
                    logger.info(f"✓ 成功获取 {len(papers)} 篇 {venue} {category} 论文")
                    all_papers.extend(papers)
                else:
                    logger.warning(f"✗ {venue} {category} 未找到论文（可能会议尚未举办）")
        
        logger.info(f"\n总计找到 {len(all_papers)} 篇论文")
        
        if not all_papers:
            logger.warning("未找到任何论文，请检查年份和会议设置")
            return
        
        # 下载并处理每篇论文
        processed_count = 0
        
        for paper in all_papers:
            try:
                # 下载PDF
                pdf_path = self._download_pdf(
                    paper['pdf_url'],
                    paper['title'],
                    f"{paper['venue']}_{paper['category']}"
                )
                
                if pdf_path:
                    processed_count += 1
                    logger.info(f"[{paper['venue']} {paper['category']}] 已下载 ({processed_count}/{len(all_papers)}): {paper['title']}")
                    
                    # 返回PDF路径供处理
                    yield pdf_path, f"{paper['venue']}_{paper['category']}", paper
                    
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
        
        filename = f"{category}_{safe_title}.pdf"
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


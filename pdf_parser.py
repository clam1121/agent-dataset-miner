"""
PDF解析模块
提取PDF中的文本内容、URL链接和作者信息
"""

import fitz  # PyMuPDF
import re
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class PDFParser:
    """PDF解析器"""
    
    def __init__(self, pdf_path: str):
        """
        初始化PDF解析器
        
        Args:
            pdf_path: PDF文件路径
        """
        self.pdf_path = pdf_path
        try:
            self.doc = fitz.open(pdf_path)
            logger.info(f"成功打开PDF: {pdf_path}, 共 {len(self.doc)} 页")
        except Exception as e:
            logger.error(f"打开PDF失败: {str(e)}")
            raise
            
        # 预编译正则表达式
        self.url_pattern = re.compile(r'https?://[^\s\)>\]]+')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
    def extract_full_text(self, max_pages: int = None) -> str:
        """
        提取PDF的全部文本
        
        Args:
            max_pages: 最大页数限制，None表示全部
            
        Returns:
            提取的文本内容
        """
        text_parts = []
        pages_to_process = min(len(self.doc), max_pages) if max_pages else len(self.doc)
        
        for page_num in range(pages_to_process):
            page = self.doc[page_num]
            text = page.get_text("text")
            text_parts.append(text)
            
        full_text = "\n".join(text_parts)
        logger.info(f"提取了 {pages_to_process} 页，共 {len(full_text)} 字符")
        return full_text
    
    def extract_urls(self, text: str = None) -> List[str]:
        """
        提取文本中的所有URL
        
        Args:
            text: 输入文本，如果为None则提取全文
            
        Returns:
            URL列表
        """
        if text is None:
            text = self.extract_full_text()
            
        urls = self.url_pattern.findall(text)
        # 清理URL末尾的标点符号
        cleaned_urls = []
        for url in urls:
            url = url.rstrip('.,;:!?')
            cleaned_urls.append(url)
            
        # 去重
        unique_urls = list(set(cleaned_urls))
        logger.info(f"提取到 {len(unique_urls)} 个唯一URL")
        return unique_urls
    
    def extract_metadata(self) -> Dict[str, str]:
        """
        提取PDF的元数据
        
        Returns:
            元数据字典
        """
        try:
            metadata = self.doc.metadata
            return {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "keywords": metadata.get("keywords", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
            }
        except Exception as e:
            logger.warning(f"提取元数据失败: {str(e)}")
            return {}
    
    def extract_first_page_text(self) -> str:
        """
        提取首页文本（通常包含标题、作者、摘要）
        
        Returns:
            首页文本
        """
        if len(self.doc) > 0:
            first_page = self.doc[0]
            text = first_page.get_text("text")
            logger.info(f"提取首页文本，长度: {len(text)}")
            return text
        return ""
    
    def extract_references_section(self) -> str:
        """
        尝试提取参考文献部分（通常包含大量URL）
        
        Returns:
            参考文献文本
        """
        full_text = self.extract_full_text()
        
        # 查找References部分
        patterns = [
            r'References\n(.*)',
            r'REFERENCES\n(.*)',
            r'Bibliography\n(.*)',
            r'参考文献\n(.*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)
            if match:
                refs_text = match.group(1)
                logger.info(f"找到参考文献部分，长度: {len(refs_text)}")
                return refs_text
                
        logger.warning("未找到参考文献部分")
        return ""
    
    def extract_dataset_related_sentences(self, keywords: List[str] = None) -> List[str]:
        """
        提取与数据集相关的句子
        
        Args:
            keywords: 关键词列表
            
        Returns:
            相关句子列表
        """
        if keywords is None:
            keywords = [
                'dataset', 'benchmark', 'corpus', 'collection',
                'training data', 'test set', 'evaluation set',
                'github', 'huggingface', 'kaggle'
            ]
            
        full_text = self.extract_full_text()
        
        # 按句子分割
        sentences = re.split(r'[.!?]\s+', full_text)
        
        related_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 检查是否包含关键词
            sentence_lower = sentence.lower()
            if any(keyword.lower() in sentence_lower for keyword in keywords):
                related_sentences.append(sentence)
                
        logger.info(f"提取到 {len(related_sentences)} 个相关句子")
        return related_sentences
    
    def get_summary_text(self, max_chars: int = 20000) -> Tuple[str, List[str]]:
        """
        获取论文摘要文本和URL列表，用于LLM处理
        优先使用前几页和数据集相关内容
        
        Args:
            max_chars: 最大字符数
            
        Returns:
            (摘要文本, URL列表)
        """
        # 提取前5页
        first_pages_text = []
        for i in range(min(5, len(self.doc))):
            first_pages_text.append(self.doc[i].get_text("text"))
            
        # 提取数据集相关句子
        dataset_sentences = self.extract_dataset_related_sentences()
        
        # 组合文本
        summary_parts = [
            "=== 论文前几页 ===",
            "\n".join(first_pages_text),
            "\n=== 数据集相关内容 ===",
            "\n".join(dataset_sentences[:50])  # 限制句子数
        ]
        
        summary_text = "\n".join(summary_parts)
        
        # 截断到最大长度
        if len(summary_text) > max_chars:
            summary_text = summary_text[:max_chars] + "\n...(文本已截断)"
            
        # 提取URL
        urls = self.extract_urls(summary_text)
        
        logger.info(f"生成摘要文本，长度: {len(summary_text)}, URL数: {len(urls)}")
        return summary_text, urls
    
    def close(self):
        """关闭PDF文档"""
        try:
            if hasattr(self, 'doc') and self.doc:
                self.doc.close()
                logger.debug(f"已关闭PDF: {self.pdf_path}")
        except Exception as e:
            logger.error(f"关闭PDF失败: {str(e)}")
            
    def __del__(self):
        """析构函数"""
        self.close()




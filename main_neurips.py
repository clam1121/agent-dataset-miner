"""
NeurIPS论文数据集挖掘主程序
从NeurIPS获取2025年Spotlight和Best论文，提取数据集信息
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from neurips_downloader import NeurIPSDownloader
from pdf_parser import PDFParser
from llm_client import call_gpt4o_text
from prompts import (
    EXTRACT_PAPER_META_PROMPT,
    EXTRACT_DATASET_NAMES_PROMPT,
    EXTRACT_DATASET_DETAILS_PROMPT,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dataset_miner_neurips.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NeurIPSDatasetMiner:
    """NeurIPS数据集信息挖掘器"""
    
    def __init__(self, output_file: str = "outputs/dataset_neurips_results.jsonl"):
        """
        初始化
        
        Args:
            output_file: 输出文件路径
        """
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 数据集ID计数器
        self.dataset_counter = 0
        
    def extract_json_from_response(self, response: str) -> Any:
        """
        从LLM响应中提取JSON
        
        Args:
            response: LLM返回的文本
            
        Returns:
            解析后的JSON对象
        """
        try:
            # 尝试直接解析
            return json.loads(response)
        except:
            pass
        
        # 尝试提取```json```块
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # 尝试提取{}块
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        logger.error(f"无法解析JSON响应: {response[:200]}")
        return None
    
    def process_paper(self, pdf_path: str, category: str, paper_info: dict) -> List[Dict]:
        """
        处理单篇论文，提取数据集信息
        
        Args:
            pdf_path: PDF文件路径
            category: 论文类别
            paper_info: 论文基本信息
            
        Returns:
            数据集信息列表
        """
        logger.info(f"开始处理论文: {paper_info['title']}")
        
        results = []
        
        try:
            # 1. 解析PDF
            parser = PDFParser(pdf_path)
            summary_text, urls = parser.get_summary_text(max_chars=25000)
            
            logger.info(f"提取文本长度: {len(summary_text)}, URL数量: {len(urls)}")
            
            # 2. 提取论文元信息
            logger.info("步骤1: 提取论文元信息...")
            meta_prompt = EXTRACT_PAPER_META_PROMPT.format(text=summary_text[:15000])
            meta_response = call_gpt4o_text(meta_prompt)
            paper_meta = self.extract_json_from_response(meta_response)
            
            if not paper_meta:
                logger.warning("论文元信息提取失败，使用默认值")
                paper_meta = {
                    "title": paper_info.get('title', 'Unknown'),
                    "authors": [],
                    "venue": f"NeurIPS {category}",
                    "year": "2025",
                    "url": paper_info.get('url', ''),
                    "is_fellow": "false"
                }
            
            # 补充NeurIPS URL
            if not paper_meta.get('url'):
                paper_meta['url'] = paper_info.get('url', '')
            
            # 标记是否为获奖论文
            if category == 'best':
                paper_meta['is_fellow'] = "true"
            
            # 3. 提取数据集名称
            logger.info("步骤2: 提取数据集名称...")
            dataset_names_prompt = EXTRACT_DATASET_NAMES_PROMPT.format(text=summary_text)
            dataset_names_response = call_gpt4o_text(dataset_names_prompt)
            dataset_names_json = self.extract_json_from_response(dataset_names_response)
            
            dataset_names = []
            if dataset_names_json and 'datasets' in dataset_names_json:
                dataset_names = dataset_names_json['datasets']
            
            if not dataset_names:
                logger.warning("未找到数据集，跳过此论文")
                parser.close()
                return results
            
            logger.info(f"找到 {len(dataset_names)} 个数据集: {dataset_names}")
            
            # 4. 为每个数据集提取详细信息
            for idx, dataset_name in enumerate(dataset_names, 1):
                logger.info(f"步骤3.{idx}: 提取数据集 '{dataset_name}' 的详细信息...")
                
                try:
                    # 提取数据集详细信息
                    details_prompt = EXTRACT_DATASET_DETAILS_PROMPT.format(
                        dataset_name=dataset_name,
                        text=summary_text,
                        urls="\n".join(urls)
                    )
                    details_response = call_gpt4o_text(details_prompt)
                    details = self.extract_json_from_response(details_response)
                    
                    if not details:
                        logger.warning(f"数据集 '{dataset_name}' 详细信息提取失败，使用默认值")
                        details = {
                            "content": f"A dataset mentioned in the paper: {dataset_name}",
                            "type": ["unspecified"],
                            "domain": ["unspecified"],
                            "fields": ["unspecified"],
                            "dataset_link": "",
                            "platform": ""
                        }
                    
                    # 组装结果
                    self.dataset_counter += 1
                    dataset_record = {
                        "dataset id": str(self.dataset_counter).zfill(3),
                        "name": dataset_name,
                        "dataset describe": {
                            "content": details.get("content", ""),
                            "type": details.get("type", ["unspecified"]),
                            "domain": details.get("domain", ["unspecified"]),
                            "fields": details.get("fields", ["unspecified"])
                        },
                        "paper_refs": paper_meta,
                        "dataset link": details.get("dataset_link", ""),
                        "platform": details.get("platform", "")
                    }
                    
                    results.append(dataset_record)
                    logger.info(f"✓ 数据集 '{dataset_name}' 处理完成")
                    
                except Exception as e:
                    logger.error(f"处理数据集 '{dataset_name}' 时出错: {str(e)}")
                    continue
            
            parser.close()
            
        except Exception as e:
            logger.error(f"处理论文时出错: {str(e)}", exc_info=True)
        
        return results
    
    def save_results(self, results: List[Dict]):
        """
        保存结果到JSONL文件（立即写入磁盘）
        
        Args:
            results: 数据集信息列表
        """
        if not results:
            logger.info("本次无数据集需要保存")
            return
            
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                for record in results:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
                    f.flush()  # 立即写入磁盘
                    logger.info(f"  ✓ 已保存数据集: {record['name']} (ID: {record['dataset id']})")
            logger.info(f"✅ 成功保存 {len(results)} 条记录到 {self.output_file}")
        except Exception as e:
            logger.error(f"❌ 保存结果失败: {str(e)}")
    
    def run(self, year: int = 2025):
        """
        运行主流程
        
        Args:
            year: NeurIPS年份
        """
        logger.info(f"=== 开始挖掘NeurIPS {year}数据集信息 ===")
        logger.info(f"目标: Spotlight和Best论文")
        
        # 初始化下载器
        downloader = NeurIPSDownloader(year=year, temp_dir="temp")
        
        total_papers = 0
        total_datasets = 0
        
        try:
            # 流式处理：下载一篇处理一篇
            for pdf_path, category, paper_info in downloader.download_and_process_papers():
                total_papers += 1
                
                logger.info(f"\n{'='*60}")
                logger.info(f"处理第 {total_papers} 篇论文 [{category.upper()}]")
                logger.info(f"标题: {paper_info['title']}")
                logger.info(f"来源: {paper_info.get('source', 'N/A')}")
                logger.info(f"{'='*60}")
                
                try:
                    # 处理论文
                    results = self.process_paper(pdf_path, category, paper_info)
                    
                    # 立即保存结果到文件
                    if results:
                        logger.info(f"\n📝 正在保存提取的数据集信息...")
                        self.save_results(results)
                        total_datasets += len(results)
                        logger.info(f"✓ 本篇论文完成：提取并保存了 {len(results)} 个数据集")
                    else:
                        logger.info(f"⚠️ 本篇论文未提取到数据集")
                    
                except Exception as e:
                    logger.error(f"❌ 处理论文失败: {str(e)}", exc_info=True)
                
                finally:
                    # 删除PDF文件释放空间
                    try:
                        if os.path.exists(pdf_path):
                            os.remove(pdf_path)
                            logger.info(f"已删除临时文件: {pdf_path}")
                    except Exception as e:
                        logger.warning(f"删除临时文件失败: {str(e)}")
            
            logger.info(f"\n{'='*60}")
            logger.info(f"=== 处理完成 ===")
            logger.info(f"总论文数: {total_papers}")
            logger.info(f"总数据集数: {total_datasets}")
            logger.info(f"输出文件: {self.output_file}")
            logger.info(f"{'='*60}")
            
        except Exception as e:
            logger.error(f"运行过程中出错: {str(e)}", exc_info=True)


def main():
    """主函数"""
    miner = NeurIPSDatasetMiner(output_file="outputs/dataset_neurips_results.jsonl")
    miner.run(year=2025)


if __name__ == "__main__":
    main()


"""
ACL下载器测试脚本
测试能否成功获取ACL论文列表
"""

import logging
from acl_downloader import ACLDownloader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_acl_downloader():
    """测试ACL下载器"""
    print("="*60)
    print("测试ACL Anthology下载器")
    print("="*60)
    
    # 测试2024年（因为2025年可能还没有论文）
    for year in [2024, 2025]:
        print(f"\n尝试获取 {year} 年论文...")
        
        downloader = ACLDownloader(year=year, temp_dir="temp_test")
        
        # 测试获取ACL Main论文列表
        papers = downloader.get_paper_list_from_anthology('ACL', 'main')
        
        if papers:
            print(f"✓ 成功找到 {len(papers)} 篇 ACL {year} Main 论文")
            print(f"\n前3篇论文示例:")
            for i, paper in enumerate(papers[:3], 1):
                print(f"\n{i}. {paper['title']}")
                print(f"   ID: {paper['anthology_id']}")
                print(f"   PDF: {paper['pdf_url']}")
            break
        else:
            print(f"✗ 未找到 {year} 年论文，尝试BibTeX方法...")
            
            papers = downloader.get_papers_from_bib('ACL', 'main')
            if papers:
                print(f"✓ 通过BibTeX找到 {len(papers)} 篇论文")
                print(f"\n前3篇论文示例:")
                for i, paper in enumerate(papers[:3], 1):
                    print(f"\n{i}. {paper['title']}")
                    print(f"   ID: {paper['anthology_id']}")
                break
            else:
                print(f"✗ {year} 年暂无可用论文")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    test_acl_downloader()




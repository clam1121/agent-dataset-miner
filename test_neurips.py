"""
NeurIPS下载器测试脚本
测试能否成功获取NeurIPS论文列表
"""

import logging
from neurips_downloader import NeurIPSDownloader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_neurips_downloader():
    """测试NeurIPS下载器"""
    print("="*60)
    print("测试NeurIPS下载器")
    print("="*60)
    
    # 测试2024年和2025年
    for year in [2024, 2025]:
        print(f"\n尝试获取 {year} 年论文...")
        
        downloader = NeurIPSDownloader(year=year, temp_dir="temp_test")
        
        # 方法1: OpenReview
        print(f"\n--- 方法1: OpenReview ---")
        papers_or = downloader.get_papers_from_openreview()
        if papers_or:
            print(f"✓ OpenReview找到 {len(papers_or)} 篇论文")
            print(f"\n前3篇示例:")
            for i, paper in enumerate(papers_or[:3], 1):
                print(f"\n{i}. [{paper['category'].upper()}] {paper['title']}")
                print(f"   URL: {paper['url']}")
        else:
            print(f"✗ OpenReview未找到论文")
        
        # 方法2: Proceedings
        print(f"\n--- 方法2: Proceedings ---")
        papers_proc = downloader.get_papers_from_proceedings()
        if papers_proc:
            print(f"✓ Proceedings找到 {len(papers_proc)} 篇论文")
            print(f"\n前3篇示例:")
            for i, paper in enumerate(papers_proc[:3], 1):
                print(f"\n{i}. [{paper['category'].upper()}] {paper['title']}")
                print(f"   PDF: {paper['pdf_url']}")
        else:
            print(f"✗ Proceedings未找到论文")
        
        # 方法3: Awards
        print(f"\n--- 方法3: neurips.cc Awards ---")
        papers_award = downloader.get_papers_from_neurips_cc()
        if papers_award:
            print(f"✓ 找到 {len(papers_award)} 篇获奖论文")
            for i, paper in enumerate(papers_award, 1):
                print(f"\n{i}. [BEST] {paper['title']}")
                print(f"   URL: {paper['url']}")
        else:
            print(f"✗ 未找到获奖论文信息")
        
        # 总结
        total = len(papers_or) + len(papers_proc) + len(papers_award)
        if total > 0:
            print(f"\n✅ {year} 年共找到 {total} 篇论文（合并前）")
            break
        else:
            print(f"\n❌ {year} 年暂无可用论文")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    test_neurips_downloader()


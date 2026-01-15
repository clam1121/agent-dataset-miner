"""
ICML下载器测试脚本
测试能否成功获取ICML论文列表
"""

import logging
from icml_downloader import ICMLDownloader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_icml_downloader():
    """测试ICML下载器"""
    print("="*60)
    print("测试ICML下载器")
    print("="*60)
    
    # 测试2024年和2023年
    for year in [2024, 2023]:
        print(f"\n尝试获取 {year} 年论文...")
        
        downloader = ICMLDownloader(year=year, temp_dir="temp_test")
        
        # 方法1: PMLR
        print(f"\n--- 方法1: PMLR ---")
        papers_pmlr = downloader.get_papers_from_pmlr()
        if papers_pmlr:
            print(f"✓ PMLR找到 {len(papers_pmlr)} 篇论文")
            print(f"\n前3篇示例:")
            for i, paper in enumerate(papers_pmlr[:3], 1):
                print(f"\n{i}. [{paper['category'].upper()}] {paper['title']}")
                print(f"   PDF: {paper['pdf_url']}")
        else:
            print(f"✗ PMLR未找到论文")
        
        # 方法2: OpenReview
        print(f"\n--- 方法2: OpenReview ---")
        papers_or = downloader.get_papers_from_openreview()
        if papers_or:
            print(f"✓ OpenReview找到 {len(papers_or)} 篇论文")
            print(f"\n前3篇示例:")
            for i, paper in enumerate(papers_or[:3], 1):
                print(f"\n{i}. [{paper['category'].upper()}] {paper['title']}")
                print(f"   URL: {paper['url']}")
        else:
            print(f"✗ OpenReview未找到论文")
        
        # 总结
        total = len(papers_pmlr) + len(papers_or)
        if total > 0:
            print(f"\n✅ {year} 年共找到 {total} 篇论文（合并前）")
            break
        else:
            print(f"\n❌ {year} 年暂无可用论文")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    test_icml_downloader()




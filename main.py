import time
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor

# 引入我們寫好的模組
from ptt_search import search_ptt
from ptt_spider import parse_ptt_article

# 設定 API Key
genai.configure(api_key="MY_API_KEY") 

def analyze_aggregated_data(keyword, articles_data):
    """
    將多篇文章資料打包，一次餵給 AI
    """
    model = genai.GenerativeModel('gemini-flash-latest')
    
    # 1. 組合超大 Prompt
    combined_content = ""
    for i, data in enumerate(articles_data):
        if not data: continue
        
        combined_content += f"""
        === 第 {i+1} 篇討論 ===
        標題：{data['meta']['title']}
        日期：{data['meta']['time']}
        內文摘要：{data['body'][:500]}... (下略)
        精選留言：
        """
        # 只取前 30 則留言 + 後 20 則留言 (取頭取尾看風向)
        selected_comments = data['comments'][:30] + data['comments'][-20:]
        for c in selected_comments:
            combined_content += f"  - {c['user']} ({c['type']}): {c['content']}\n"
        combined_content += "\n"

    prompt = f"""
    你是一個專業的購物決策助手 "Truth Lens"。
    使用者想查詢的產品/關鍵字是：「{keyword}」。
    
    我蒐集了 PTT 最熱門的幾篇討論，請幫我進行「綜合分析報告」。
    
    【分析資料源】：
    {combined_content}
    
    【請輸出以下格式的報告】：
    
    ## 1. 終極結論 (Verdict)
    (請用一句話告訴我：買，還是不買？或是適合什麼樣的人買？)
    
    ## 2. 真實優缺點 (Pros & Cons)
    | 優點 (推) | 缺點 (噓/災情) |
    | :--- | :--- |
    | (列點) | (列點) |
    
    ## 3. 關鍵爭議/災情警示
    (是否有特定批次、特定韌體版本的問題？還是只是個案？)
    
    ## 4. 價格與入手建議
    (如果文中有人提到價格，請整理出一個「網友認知的合理入手價」)
    
    ## 5. 綜合推薦分數 (0-10分)
    """
    
    print("正在請求 Gemini 進行綜合分析 (這可能需要幾秒鐘)...")
    response = model.generate_content(prompt)
    return response.text

def main():
    keyword = input("請輸入你想查詢的關鍵字 (例如: Pixel 9, Sony XM5): ")
    board = "MobileComm" # 預設手機版，你也可以改 Gossiping 或 PC_Shopping
    
    print(f"\n1. 正在 PTT {board} 版搜尋 '{keyword}'...")
    search_results = search_ptt(keyword, board=board, max_articles=5) # 抓前 5 篇
    
    if not search_results:
        print("找不到相關文章。")
        return

    print(f"   找到 {len(search_results)} 篇熱門文章，準備爬取詳細內容...")
    
    # 使用 ThreadPoolExecutor 平行爬取 (速度優化)
    crawled_data = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        # 建立任務清單
        future_to_url = {executor.submit(parse_ptt_article, res['url']): res for res in search_results}
        
        for future in future_to_url:
            data = future.result()
            if data:
                crawled_data.append(data)
                print(f"   v 已讀取：{data['meta']['title']}")
    
    if not crawled_data:
        print("無法讀取文章內容。")
        return

    # 聚合分析
    print("\n2. 正在進行 AI 綜合分析...")
    final_report = analyze_aggregated_data(keyword, crawled_data)
    
    print("\n" + "="*40)
    print(final_report)
    print("="*40)

if __name__ == "__main__":
    main()
import os
import google.generativeai as genai
from ptt_spider import parse_ptt_article # 引入你剛剛寫的爬蟲

# 設定 API Key (建議設在環境變數，或先暫時貼在這裡)
# os.environ["GOOGLE_API_KEY"] = "你的_GEMINI_API_KEY"
genai.configure(api_key="MY_API_KEY") 

def analyze_article(article_data):
    if not article_data:
        return "無法分析：無資料"

    # 1. 預處理留言：把留言串成字串，並加上 ID 以便 AI 識別
    # 我們只取前 50 則留言避免 Token 爆炸 (雖然 Gemini 其實吃得下)
    comments_text = ""
    for c in article_data['comments'][:100]:
        comments_text += f"{c['user']} ({c['type']}): {c['content']}\n"

    # 2. 建構 Prompt (這是 Truth Lens 的靈魂)
    prompt = f"""
    你是一個專業的輿情分析師，請針對以下 PTT 文章與留言進行深度分析。
    
    【分析目標】：
    1. **事件懶人包**：用一句話講完發生什麼事。
    2. **真實風向 (Truth Score)**：鄉民是支持原PO還是支持廠商？請給出 0-10 分 (0=完全支持廠商, 10=完全支持原PO)，並說明理由。
    3. **關鍵爭議點**：大家在吵什麼細節？(例如合約日期、客服態度)。
    4. **潛在風險/行動呼籲**：如果你是類似的用戶，這篇文章給你什麼具體建議？(例如要去檢查帳單、找NCC)。
    5. **情緒關鍵字**：列出 3 個最常出現的情緒形容詞 (如：囂張、爽、爛)。

    【文章標題】：{article_data['meta']['title']}
    【文章內容】：
    {article_data['body']}

    【鄉民留言】：
    {comments_text}
    """

    # 3. Call Gemini
    model = genai.GenerativeModel('gemini-flash-latest')
    response = model.generate_content(prompt)
    
    return response.text

# --- 執行 ---
if __name__ == "__main__":
    # 使用你剛剛測試成功的那個 URL
    url = "https://www.ptt.cc/bbs/MobileComm/M.1764045545.A.9F9.html" # 記得換成你剛才那個真實網址
    
    print("1. 正在爬取文章...")
    data = parse_ptt_article(url)
    
    if data:
        print("2. 正在呼叫 AI 進行分析 (請稍候)...")
        analysis = analyze_article(data)
        
        print("\n" + "="*30)
        print("【Truth Lens 分析報告】")
        print("="*30)
        print(analysis)
    else:
        print("爬取失敗")
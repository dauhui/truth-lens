import requests
from bs4 import BeautifulSoup

def parse_ptt_article(url):
    # 1. 設定 Header 與 Cookie (繞過 PTT 18歲確認)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    cookies = {'over18': '1'}  # 這是關鍵，有些版(如 Gossiping)需要這個

    try:
        response = requests.get(url, headers=headers, cookies=cookies)
        response.raise_for_status() # 檢查連線是否成功
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    main_content = soup.find(id='main-content')

    if not main_content:
        print("無法定位主要內容，可能是網址錯誤或文章已被刪除")
        return None

    # --- 資料解析開始 ---
    
    # 2. 提取 Meta 資料 (作者, 標題, 時間)
    metas = main_content.find_all('div', class_='article-metaline')
    meta_info = {}
    if metas and len(metas) >= 3:
        meta_info['author'] = metas[0].find('span', class_='article-meta-value').text
        meta_info['title'] = metas[1].find('span', class_='article-meta-value').text
        meta_info['time'] = metas[2].find('span', class_='article-meta-value').text
    else:
        meta_info = {'title': '未知標題', 'author': '未知作者', 'time': '未知時間'}

    # 3. 提取留言 (Pushes) 並從主內容中移除
    # 我們要把留言存成 List，方便之後統計「推/噓」數量
    pushes = main_content.find_all('div', class_='push')
    comments = []
    
    for push in pushes:
        push_tag = push.find('span', class_='push-tag').text.strip() # 推, 噓, →
        push_userid = push.find('span', class_='push-userid').text.strip()
        push_content = push.find('span', class_='push-content').text.strip(': ')
        
        comments.append({
            'type': push_tag,
            'user': push_userid,
            'content': push_content
        })
        
        # 重要：讀完後從 main_content 移除這行，避免它混入「本文」
        push.extract() 

    # 4. 移除 Meta 標籤，剩下的就是純淨的「本文」
    for meta in metas:
        meta.extract()
        
    # 移除其他可能干擾的元素 (如：文章網址連結、IP顯示)
    for tag in main_content.find_all(['div', 'span']):
        if 'article-metaline-right' in tag.get('class', []):
            tag.extract()
    
    body_content = main_content.text.strip()

    return {
        'meta': meta_info,
        'body': body_content,
        'comments': comments
    }

# --- 測試執行 ---
if __name__ == "__main__":
    # 找一篇 MobileComm (手機版) 的文章來測試
    # 範例：iPhone 16 Pro 相關討論 (你可以換成任何你想測的 PTT 網址)
    target_url = "https://www.ptt.cc/bbs/MobileComm/M.1764045545.A.9F9.html" # 注意：這是我隨便打的格式，請換成真實網址
    
    # 建議你現在去 PTT MobileComm 版隨便複製一個網址貼過來：
    # 例如：https://www.ptt.cc/bbs/MobileComm/M.1732501234.A.567.html
    
    print(f"正在爬取: {target_url} ...")
    # 這裡請先暫時註解掉上面那行假的，填入你真實想測的 URL
    data = parse_ptt_article(target_url) 
    
    # 為了讓你馬上能跑，我先不Call函數，請你填入網址後把註解拿掉
    print("請修改代碼中的 target_url 為真實 PTT 連結後再執行！")
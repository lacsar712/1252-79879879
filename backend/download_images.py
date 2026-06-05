import os
import time
import urllib.request
import urllib.error

# 确保目录存在
os.makedirs("static/images", exist_ok=True)

# 图片映射
images = [
    "https://img3.doubanio.com/view/subject/l/public/s29366730.jpg",
    "https://img9.doubanio.com/view/subject/l/public/s33703494.jpg", 
    "https://img9.doubanio.com/view/subject/l/public/s29195878.jpg",
    "https://img1.doubanio.com/view/subject/l/public/s25648004.jpg",
    "https://img3.doubanio.com/view/subject/l/public/s4103991.jpg",
    "https://img1.doubanio.com/view/subject/l/public/s28916534.jpg",
    "https://img2.doubanio.com/view/subject/l/public/s34175562.jpg",
    "https://img9.doubanio.com/view/subject/l/public/s29901158.jpg",
    "https://img2.doubanio.com/view/subject/l/public/s28379955.jpg",
    "https://img9.doubanio.com/view/subject/l/public/s27297117.jpg",
    "https://img2.doubanio.com/view/subject/l/public/s29053580.jpg",
    "https://img2.doubanio.com/view/subject/l/public/s28357056.jpg"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://movie.douban.com/" 
}

print("开始下载图片...")
for url in images:
    filename = url.split("/")[-1]
    filepath = os.path.join("static/images", filename)
    
    # 尝试不同域名
    domains = ["img1.doubanio.com", "img2.doubanio.com", "img3.doubanio.com", "img9.doubanio.com"]
    success = False
    
    for domain in domains:
        current_url = url.replace(url.split("/")[2], domain)
        try:
            print(f"尝试下载: {current_url}")
            req = urllib.request.Request(current_url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    with open(filepath, "wb") as f:
                        f.write(response.read())
                    print(f"成功保存: {filename}")
                    success = True
                    break
                else:
                    print(f"失败 {response.status}")
        except Exception as e:
            print(f"异常: {e}")
            
    if not success:
        print(f"无法下载图片: {filename}")
        # 如果下载失败，创建一个简单的 placeholder
        # 这里我们就不创建了，让它留空或者怎样，但最好保证下载成功

print("下载完成")

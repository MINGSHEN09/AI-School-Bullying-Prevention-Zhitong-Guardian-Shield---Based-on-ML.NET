import os
import time
from wxauto import *

# 获取当前微信客户端
wx = WeChat()

# 设置监控路径（系统图片文件夹/已处理/分类/霸凌）
pictures_folder = os.path.join(os.environ['USERPROFILE'], 'Pictures')
monitor_folder = os.path.join(pictures_folder, '已处理', '分类', '霸凌')

# 创建已发送文件记录
sent_files = set()

# 支持的图片格式
image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}

# 确保监控目录存在
os.makedirs(monitor_folder, exist_ok=True)

# 指定微信接收者
who = '文件传输助手'

print(f"开始监控目录：{monitor_folder}")
print("准备就绪，等待新图片...")

while True:
    try:
        # 获取当前目录文件列表
        current_files = set()
        for root, dirs, files in os.walk(monitor_folder):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), monitor_folder)
                current_files.add(rel_path)

        # 发现新文件
        new_files = current_files - sent_files
        
        if new_files:
            for rel_path in new_files:
                file_path = os.path.join(monitor_folder, rel_path)
                file_name = os.path.basename(file_path)
                
                # 检查文件有效性
                if not os.path.exists(file_path):
                    continue
                
                # 验证文件类型
                _, ext = os.path.splitext(file_path)
                if ext.lower() in image_extensions:
                    try:
                        # 发送图片文件
                        wx.SendFiles(file_path, who=who)
                        sent_files.add(rel_path)
                        print(f"[{time.strftime('%H:%M:%S')}] 已发送：{file_name}")
                    except Exception as e:
                        print(f"发送失败：{file_name} - {str(e)}")
                else:
                    print(f"跳过非图片文件：{file_name}")
                    sent_files.add(rel_path)

        time.sleep(1)

    except KeyboardInterrupt:
        print("\n监控已停止")
        break
    except Exception as e:
        print(f"发生错误：{str(e)}")
        time.sleep(5)
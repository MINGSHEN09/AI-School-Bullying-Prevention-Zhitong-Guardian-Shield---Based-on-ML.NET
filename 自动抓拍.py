import cv2
import time
import os
from datetime import datetime

def capture_webcam_photo():
    # 配置参数
    CAMERA_INDEX =0           
    AUTO_INTERVAL = 0.8        # 自动抓拍间隔（秒）
    EXIT_KEY = 27              # ESC键退出
    
    # 设置保存路径（系统图片文件夹/未处理）
    pictures_folder = os.path.join(os.environ['USERPROFILE'], 'Pictures')
    save_folder = os.path.join(pictures_folder, "未处理")
    os.makedirs(save_folder, exist_ok=True)

    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print("无法打开摄像头")
        return

    last_auto_capture = 0  # 上次自动抓拍时间
    print(f"【存储路径】{save_folder}")
    print("操作指南：")
    print(f"自动抓拍 - 每 {AUTO_INTERVAL} 秒保存一次")
    print(f"退出程序 - 按ESC键")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("视频流中断")
            break

        # 显示实时画面（缩小显示）
        display_frame = cv2.resize(frame, None, fx=0.5, fy=0.5)
        cv2.imshow('自动抓拍监控 - 按ESC退出', display_frame)

        # 获取当前时间
        current_time = time.time()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 自动定时抓拍
        if current_time - last_auto_capture >= AUTO_INTERVAL:
            filename = os.path.join(save_folder, f"auto_{timestamp}.jpg")
            cv2.imwrite(filename, frame)
            print(f"自动抓拍：{os.path.basename(filename)}")
            last_auto_capture = current_time

        # 退出检测
        if cv2.waitKey(1) == EXIT_KEY:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("程序已安全退出")

if __name__ == "__main__":
    capture_webcam_photo()
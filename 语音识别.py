# by Craig Cai
import speech_recognition as sr
from termcolor import colored
import time
import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
import smtplib
from email.mime.text import MIMEText
import requests
import hashlib
import base64
import json
from urllib.parse import urlencode
import hmac

# ==================== 配置区域 ====================

# 选择使用的API（1: 腾讯云 2: 科大讯飞）
API_CHOICE = 1

# 腾讯云配置（免费额度：每月10000次）
TENCENT_SECRET_ID = ""
TENCENT_SECRET_KEY = ""

# 科大讯飞配置（免费额度：每天500次）
IFLYTEK_APPID = ""
IFLYTEK_API_KEY = ""

# 关键词列表
KEYWORDS = ["危险", "攻击", "紧急", "help", "救命", "fire", "火警", "报警"]

# 邮件通知配置
EMAIL_ENABLED = True
SMTP_SERVER = "smtp.163.com"  # 以QQ邮箱为例
SMTP_PORT = 465
EMAIL_USER = "caimingshen163@163.com"
EMAIL_PASSWORD = "PWVVbAJDCvXDE6Wx"  # 不是密码，是SMTP授权码
EMAIL_RECEIVERS = ["receiver1@example.com", "receiver2@example.com"]

# 日志配置
LOG_DIR = "logs"
LOG_LEVEL = logging.INFO

# ==================== 工具函数 ====================

def setup_logging():
    """配置日志系统"""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)
    
    handler = TimedRotatingFileHandler(
        os.path.join(LOG_DIR, 'speech_alarm.log'),
        when='midnight',
        interval=1,
        backupCount=7
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)

def send_email(subject, content):
    """发送邮件通知"""
    if not EMAIL_ENABLED:
        return False
    
    try:
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = ", ".join(EMAIL_RECEIVERS)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, EMAIL_RECEIVERS, msg.as_string())
        
        logging.info("邮件通知发送成功")
        return True
    except Exception as e:
        logging.error(f"发送邮件失败: {str(e)}")
        return False

# ==================== 语音识别API实现 ====================

def tencent_asr(audio_data):
    """腾讯云语音识别（免费）"""
    endpoint = "asr.tencentcloudapi.com"
    service = "asr"
    action = "SentenceRecognition"
    version = "2019-06-14"
    region = "ap-guangzhou"
    
    # 准备音频数据
    audio_base64 = base64.b64encode(audio_data.get_wav_data()).decode('utf-8')
    
    # 构造请求参数
    params = {
        "ProjectId": 0,
        "SubServiceType": 2,
        "EngSerViceType": "16k_zh",
        "SourceType": 1,
        "VoiceFormat": "wav",
        "UsrAudioKey": "session-123",
        "Data": audio_base64
    }
    
    # 生成签名
    def sign(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()
    
    def get_signature(params):
        canonical_querystring = ""
        signed_headers = "content-type;host"
        payload = json.dumps(params)
        hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = f"POST\n/\n\ncontent-type:application/json\nhost:{endpoint}\n\n{signed_headers}\n{hashed_request_payload}"
        
        t = int(time.time())
        date = time.strftime("%Y-%m-%d", time.gmtime(t))
        credential_scope = f"{date}/{service}/tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = f"TC3-HMAC-SHA256\n{t}\n{credential_scope}\n{hashed_canonical_request}"
        
        secret_date = sign(("TC3" + TENCENT_SECRET_KEY).encode("utf-8"), date)
        secret_service = sign(secret_date, service)
        secret_signing = sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        
        return f"TC3-HMAC-SHA256 Credential={TENCENT_SECRET_ID}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    
    headers = {
        "Content-Type": "application/json",
        "Host": endpoint,
        "X-TC-Action": action,
        "X-TC-Version": version,
        "X-TC-Timestamp": str(int(time.time())),
        "X-TC-Region": region,
        "Authorization": get_signature(params)
    }
    
    try:
        response = requests.post(f"https://{endpoint}", headers=headers, data=json.dumps(params))
        result = response.json()
        if "Response" in result and "Result" in result["Response"]:
            return result["Response"]["Result"]
        else:
            logging.error(f"腾讯云API错误: {result}")
            return None
    except Exception as e:
        logging.error(f"腾讯云API请求失败: {str(e)}")
        return None

def iflytek_asr(audio_data):
    """科大讯飞语音识别（免费）"""
    url = "http://raasr.xfyun.cn/v2/api"
    
    # 准备音频数据
    audio_base64 = base64.b64encode(audio_data.get_wav_data()).decode('utf-8')
    
    # 构造请求参数
    params = {
        "common": {
            "app_id": IFLYTEK_APPID
        },
        "business": {
            "language": "zh_cn",
            "domain": "iat",
            "accent": "mandarin"
        },
        "data": {
            "audio": audio_base64,
            "status": 2  # 2表示最后一帧
        }
    }
    
    # 生成签名
    def get_signature():
        ts = str(int(time.time()))
        m2 = hashlib.md5()
        m2.update((IFLYTEK_APPID + ts).encode('utf-8'))
        md5 = m2.hexdigest()
        m3 = hmac.new(IFLYTEK_API_KEY.encode('utf-8'), md5.encode('utf-8'), hashlib.sha1)
        signa = base64.b64encode(m3.digest()).decode('utf-8')
        return ts, signa
    
    ts, signa = get_signature()
    headers = {
        "Content-Type": "application/json",
        "X-Appid": IFLYTEK_APPID,
        "X-CurTime": ts,
        "X-Param": base64.b64encode(json.dumps(params["business"]).encode('utf-8')).decode('utf-8'),
        "X-CheckSum": signa
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(params))
        result = response.json()
        if result.get("code") == 0 and "data" in result:
            return result["data"]["result"]
        else:
            logging.error(f"讯飞API错误: {result}")
            return None
    except Exception as e:
        logging.error(f"讯飞API请求失败: {str(e)}")
        return None

# ==================== 主程序 ====================

def recognize_speech():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    logging.info("语音关键词报警系统启动")
    logging.info(f"监控的关键词: {', '.join(KEYWORDS)}")
    
    try:
        while True:
            with microphone as source:
                logging.info("环境噪声校准中...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                logging.info("请开始说话(10秒内)...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            try:
                logging.info("正在识别语音...")
                
                if API_CHOICE == 1:  # 腾讯云
                    text = tencent_asr(audio)
                else:  # 科大讯飞
                    text = iflytek_asr(audio)
                
                if text:
                    logging.info(f"识别结果: {text}")
                    print(f"\n识别结果: {text}")
                    
                    # 检查关键词
                    keywords_detected = [
                        kw for kw in KEYWORDS 
                        if kw.lower() in text.lower()
                    ]
                    
                    if keywords_detected:
                        logging.warning(f"检测到关键词: {keywords_detected}")
                        play_alarm(text, keywords_detected)
                else:
                    logging.warning("语音识别返回空结果")
                        
            except sr.UnknownValueError:
                logging.warning("无法识别语音内容")
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logging.error(f"发生错误: {str(e)}")
                
            print("\n准备下一次监听...\n")
            
    except KeyboardInterrupt:
        logging.info("程序已安全停止")

def play_alarm(text, keywords_detected):
    """报警处理"""
    # 终端报警
    for _ in range(5):
        os.system('cls' if os.name == 'nt' else 'clear')
        alarm_msg = f"⚠️ 警报! 检测到关键词: {', '.join(keywords_detected)} ⚠️\n原文: {text}"
        print(colored(alarm_msg, "red", attrs=["bold", "blink"]))
        time.sleep(0.5)
        os.system('cls' if os.name == 'nt' else 'clear')
        time.sleep(0.5)
    
    # 发送通知
    subject = "语音关键词报警通知"
    content = f"检测到关键词: {', '.join(keywords_detected)}\n识别内容: {text}\n时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    if EMAIL_ENABLED:
        send_email(subject, content)

if __name__ == "__main__":
    # 初始化日志
    setup_logging()
    
    # 检查配置
    if API_CHOICE == 1 and (TENCENT_SECRET_ID == "你的腾讯云SecretId" or TENCENT_SECRET_KEY == "你的腾讯云SecretKey"):
        logging.error("错误: 请先配置腾讯云API密钥")
        sys.exit(1)
    elif API_CHOICE == 2 and (IFLYTEK_APPID == "你的讯飞APPID" or IFLYTEK_API_KEY == "你的讯飞API_KEY"):
        logging.error("错误: 请先配置讯飞API密钥")
        sys.exit(1)
    
    try:
        recognize_speech()
    except Exception as e:
        logging.critical(f"程序异常终止: {str(e)}", exc_info=True)
        sys.exit(1)

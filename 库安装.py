import subprocess
import sys

def install_packages():
    # 定义要安装的包列表
    packages = [
        'wxauto',       # 微信自动化库
        'opencv-python' # OpenCV库
    ]
    
    # 使用清华大学镜像源
    mirror = 'https://pypi.tuna.tsinghua.edu.cn/simple'
    
    # 遍历安装每个包
    for package in packages:
        try:
            print(f"正在安装 {package}...")
            
            # 使用当前Python解释器对应的pip进行安装
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package, '-i', mirror],
                check=True,
                capture_output=True,
                text=True
            )
            
            # 输出安装结果
            print(f"成功安装 {package}")
            print(result.stdout)
            
        except subprocess.CalledProcessError as e:
            # 捕获安装失败异常
            print(f"安装 {package} 失败，错误信息：")
            print(e.stderr)
            sys.exit(1)  # 退出程序并返回错误码

if __name__ == "__main__":
    install_packages()
    print("所有包安装完成！")
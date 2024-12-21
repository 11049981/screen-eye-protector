# 屏幕护眼灯应用程序基础框架

import tkinter as tk
from tkinter import messagebox
import subprocess
import cv2
import numpy as np
import threading
import time
import os
import requests
from PIL import Image, ImageDraw, ImageFont, ImageTk
import random
import hashlib
import winreg
import wmi
import ctypes
from ctypes import windll
import screen_brightness_control as sbc

class MainWindow:
    def __init__(self, master):
        self.master = master
        self.brightness = sbc.get_brightness()[0]  # 获取当前亮度
        self.color_temperature = 6500  # 默认色温值
        self.master.title("智能护眼助手")
        self.master.geometry("600x650")
        self.master.configure(bg="#E6F3FF")

        # 初始化WMI接口
        self.wmi = wmi.WMI(namespace='wmi')
        
        # 获取显示器亮度方法
        try:
            self.brightness_methods = self.wmi.WmiMonitorBrightnessMethods()[0]
        except Exception as e:
            print(f"无法获取亮度控制接口: {e}")
            self.brightness_methods = None

        self.create_menu()
        self.create_layout()
        self.create_controls_frame()
        self.create_poetry_frame()
        
        # 启动定时更新诗句
        self.update_poetry()

    def create_menu(self):
        menu = tk.Menu(self.master)
        self.master.config(menu=menu)
        
        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="保存设置", command=self.save_settings)
        file_menu.add_command(label="加载设置", command=self.load_settings)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.master.quit)

    def create_layout(self):
        title_label = tk.Label(
            self.master,
            text="智能护眼助手",
            font=("Microsoft YaHei", 16, "bold"),
            bg="#E6F3FF",
            fg="#2C3E50"
        )
        title_label.pack(pady=20)

        tip_label = tk.Label(
            self.master,
            text="根据环境光智能调节屏幕，保护您的眼睛",
            font=("Microsoft YaHei", 10),
            bg="#E6F3FF",
            fg="#34495E"
        )
        tip_label.pack(pady=5)

    def create_controls_frame(self):
        main_frame = tk.Frame(self.master, bg="#E6F3FF")
        main_frame.pack(expand=True, fill="both", padx=20)

        # 创建左右两列布局
        left_frame = tk.Frame(main_frame, bg="#E6F3FF")
        left_frame.pack(side=tk.LEFT, expand=True, fill="both", padx=5)
        
        right_frame = tk.Frame(main_frame, bg="#E6F3FF")
        right_frame.pack(side=tk.LEFT, expand=True, fill="both", padx=5)

        # 左侧放置亮度和色温控制
        self.create_brightness_control(left_frame)
        self.create_color_temperature_control(left_frame)

        # 右侧放置环境光检测和定时器
        self.create_light_detection_control(right_frame)
        self.create_timer_control(right_frame)

    def create_brightness_control(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="亮度调节",
            bg="#E6F3FF",
            fg="#2C3E50",
            font=("Microsoft YaHei", 9),
            padx=10,
            pady=5
        )
        frame.pack(pady=5, fill="x")

        self.brightness_label = tk.Label(
            frame,
            text=f"当前亮度: {self.brightness}",
            bg="#E6F3FF",
            fg="#2C3E50",
            width=20
        )
        self.brightness_label.pack(pady=2)

        self.brightness_slider = tk.Scale(
            frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            command=self.update_brightness,
            bg="#E6F3FF",
            highlightthickness=0,
            length=200
        )
        self.brightness_slider.set(self.brightness)
        self.brightness_slider.pack(fill="x")

    def create_color_temperature_control(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="色温调节",
            bg="#E6F3FF",
            fg="#2C3E50",
            font=("Microsoft YaHei", 9),
            padx=10,
            pady=5
        )
        frame.pack(pady=5, fill="x")

        self.color_temp_label = tk.Label(
            frame,
            text=f"当前色温: {self.color_temperature}K",
            bg="#E6F3FF",
            fg="#2C3E50",
            width=20
        )
        self.color_temp_label.pack(pady=2)

        self.color_temp_slider = tk.Scale(
            frame,
            from_=2700,
            to=6500,
            orient=tk.HORIZONTAL,
            command=self.update_color_temperature,
            bg="#E6F3FF",
            highlightthickness=0,
            length=200
        )
        self.color_temp_slider.set(self.color_temperature)
        self.color_temp_slider.pack(fill="x")

    def create_light_detection_control(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="环境光检测",
            bg="#E6F3FF",
            fg="#2C3E50",
            font=("Microsoft YaHei", 9),
            padx=10,
            pady=5
        )
        frame.pack(pady=5, fill="x")

        self.light_value_label = tk.Label(
            frame,
            text="当前环境光: 等待检测...",
            bg="#E6F3FF",
            fg="#2C3E50",
            width=20
        )
        self.light_value_label.pack(pady=2)

        self.light_detection_button = tk.Button(
            frame,
            text="开始环境光检测",
            command=self.start_light_detection,
            bg="#3498DB",
            fg="white",
            font=("Microsoft YaHei", 9),
            relief=tk.FLAT,
            width=15
        )
        self.light_detection_button.pack(pady=5)

    def create_timer_control(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="休息提醒",
            bg="#E6F3FF",
            fg="#2C3E50",
            font=("Microsoft YaHei", 9),
            padx=10,
            pady=5
        )
        frame.pack(pady=5, fill="x")

        timer_input_frame = tk.Frame(frame, bg="#E6F3FF")
        timer_input_frame.pack(fill="x", pady=2)

        self.timer_label = tk.Label(
            timer_input_frame,
            text="提醒间隔:",
            bg="#E6F3FF",
            fg="#2C3E50"
        )
        self.timer_label.pack(side=tk.LEFT, padx=5)

        self.timer_entry = tk.Entry(
            timer_input_frame,
            justify='center',
            width=10
        )
        self.timer_entry.insert(0, "30")
        self.timer_entry.pack(side=tk.LEFT, padx=5)

        minutes_label = tk.Label(
            timer_input_frame,
            text="分钟",
            bg="#E6F3FF",
            fg="#2C3E50"
        )
        minutes_label.pack(side=tk.LEFT)

        self.start_timer_button = tk.Button(
            frame,
            text="开始定时提醒",
            command=self.start_timer_from_entry,
            bg="#3498DB",
            fg="white",
            font=("Microsoft YaHei", 9),
            relief=tk.FLAT,
            width=15
        )
        self.start_timer_button.pack(pady=5)

    def create_poetry_frame(self):
        # 创建诗词展示区域
        poetry_frame = tk.Frame(self.master, bg="#E6F3FF")
        poetry_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)

        # 创建标题和刷新按钮的框架
        title_frame = tk.Frame(poetry_frame, bg="#E6F3FF")
        title_frame.pack(fill=tk.X)

        # 添加"每日诗词"标题
        title_label = tk.Label(
            title_frame,
            text="每日诗词",
            font=("Microsoft YaHei", 10, "bold"),
            bg="#E6F3FF",
            fg="#2C3E50"
        )
        title_label.pack(side=tk.LEFT, padx=5)

        # 添加刷新按钮
        self.refresh_button = tk.Button(
            title_frame,
            text="刷新",
            command=self.refresh_poetry,
            bg="#3498DB",
            fg="white",
            font=("Microsoft YaHei", 9),
            relief=tk.FLAT,
            width=8
        )
        self.refresh_button.pack(side=tk.RIGHT, padx=5)

        # 中文诗句标签
        self.poetry_label = tk.Label(
            poetry_frame,
            text="正在获取诗句...",
            font=("Microsoft YaHei", 12),
            bg="#E6F3FF",
            fg="#2C3E50",
            wraplength=500  # 自动换行
        )
        self.poetry_label.pack(pady=5)

        # 英文翻译标签
        self.translation_label = tk.Label(
            poetry_frame,
            text="Loading translation...",
            font=("Times New Roman", 11, "italic"),
            bg="#E6F3FF",
            fg="#34495E",
            wraplength=500  # 自动换行
        )
        self.translation_label.pack(pady=5)

        # 添加分隔
        separator = tk.Frame(poetry_frame, height=1, bg="#BDC3C7")
        separator.pack(fill=tk.X, pady=10)

    def refresh_poetry(self):
        # 禁用刷新按钮
        self.refresh_button.config(state=tk.DISABLED)
        
        # 创建加载动画
        self.poetry_label.config(text="正在获取诗句...")
        self.translation_label.config(text="Loading...")
        
        # 在新线程获取诗句
        threading.Thread(target=self._fetch_poetry, daemon=True).start()

    def _fetch_poetry(self):
        try:
            response = requests.get("https://v2.jinrishici.com/one.json")
            if response.status_code == 200:
                data = response.json()
                poem = data["data"]["content"]
                translation = self.get_translation(poem)
                
                # 使用淡入效果更新文本
                self.fade_in_text(self.poetry_label, poem)
                self.fade_in_text(self.translation_label, translation)
            else:
                self.poetry_label.config(text="无法获取诗句")
                self.translation_label.config(text="Failed to get poetry")
        except Exception as e:
            self.poetry_label.config(text="获取诗句时出���")
            self.translation_label.config(text=f"Error: {str(e)}")
        finally:
            # 重新启用刷新按钮
            self.refresh_button.config(state=tk.NORMAL)

    def fade_in_text(self, label, text, steps=10):
        # 实现文本淡入效果
        colors = [
            self.interpolate_color("#E6F3FF", "#2C3E50", i/steps)
            for i in range(steps + 1)
        ]
        
        label.config(text=text)
        for color in colors:
            label.config(fg=color)
            self.master.update()
            time.sleep(0.02)

    def interpolate_color(self, start_color, end_color, factor):
        # 计算颜色渐变
        start = tuple(int(start_color[i:i+2], 16) for i in (1, 3, 5))
        end = tuple(int(end_color[i:i+2], 16) for i in (1, 3, 5))
        
        result = tuple(
            int(start[i] + (end[i] - start[i]) * factor)
            for i in range(3)
        )
        
        return f"#{result[0]:02x}{result[1]:02x}{result[2]:02x}"

    def update_poetry(self):
        self.refresh_poetry()
        # 每5分钟自动更新一次
        self.master.after(300000, self.update_poetry)

    def get_translation(self, poem):
        """获取诗词的英文翻译"""
        try:
            # 使用百度翻译API
            # 注意：需要替换为您自己的API密钥
            from_lang = 'zh'
            to_lang = 'en'
            
            # 这里使用百度翻译API的示例
            # 实际使用时需要替换为您的appid和密钥
            appid = 'YOUR_APPID'
            secret_key = 'YOUR_SECRET_KEY'
            
            # 如果没有配置API密钥，返回占位符翻译
            if appid == 'YOUR_APPID':
                return self.get_placeholder_translation(poem)
            
            # 计算签名
            salt = str(random.randint(32768, 65536))
            sign = appid + poem + salt + secret_key
            sign = hashlib.md5(sign.encode()).hexdigest()
            
            # 构建请求
            url = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
            params = {
                'q': poem,
                'from': from_lang,
                'to': to_lang,
                'appid': appid,
                'salt': salt,
                'sign': sign
            }
            
            # 发送请求
            response = requests.get(url, params=params)
            result = response.json()
            
            if 'trans_result' in result:
                return result['trans_result'][0]['dst']
            else:
                return self.get_placeholder_translation(poem)
                
        except Exception as e:
            print(f"翻译出错: {str(e)}")
            return self.get_placeholder_translation(poem)
            
    def get_placeholder_translation(self, poem):
        """生成占位符翻译（当无法使用翻译API时）"""
        translations = {
            "举头望明月": "Raising my head, I gaze at the bright moon",
            "低头思故乡": "Lowering my head, I think of my hometown",
            "床前明月光": "Moonlight before my bed",
            "疑是地上霜": "Could be frost on the ground",
            "日照香炉生紫烟": "Sunlight on the incense burner creates purple smoke",
            "遥看瀑布挂前川": "Looking far at the waterfall hanging over the stream",
            "飞流直下三千尺": "Flying stream falls three thousand feet",
            "疑是银河落九天": "Like the Milky Way descending from the ninth heaven"
        }
        
        # 检查是否有完全匹配的翻译
        if poem in translations:
            return translations[poem]
            
        # 如果没有完全匹配，返回一个通用的翻译格式
        return (
            "This classical Chinese poem speaks of nature's beauty and human emotions.\n"
            "It reflects traditional Chinese poetic elements like mountains, rivers, or moonlight."
        )

    def update_brightness(self, value):
        """更新屏幕亮度"""
        try:
            brightness = int(value)
            self.brightness = brightness
            self.brightness_label.config(text=f"当前亮度: {brightness:>3}")
            
            # 使用screen_brightness_control库设置亮度
            try:
                sbc.set_brightness(brightness)
                print(f"已设置亮度为: {brightness}")
            except Exception as e:
                print(f"使用sbc设置亮度失败: {e}")
                
                # 备用方案：使用WMI设置亮度
                try:
                    if self.brightness_methods:
                        self.brightness_methods.WmiSetBrightness(brightness, 0)
                        print(f"使用WMI设置亮度成功: {brightness}")
                except Exception as e:
                    print(f"使用WMI设置亮度失败: {e}")
                    
        except Exception as e:
            print(f"调整亮度时出错: {e}")

    def update_color_temperature(self, value):
        """更新屏幕色温"""
        try:
            self.color_temperature = int(value)
            self.color_temp_label.config(text=f"当前色温: {self.color_temperature:>4}K")
            
            # 从运行的进程中获取f.lux路径
            import psutil
            flux_path = None
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    if 'flux' in proc.info['name'].lower():
                        flux_path = proc.info['exe']
                        print(f"从运行进程中找到f.lux路径: {flux_path}")
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            if not flux_path:
                print("未找到正在运行的f.lux进程，请确保f.lux已启动")
                return
                
            # 尝试调用f.lux
            try:
                print(f"\n尝试调用f.lux设置色温: {self.color_temperature}K")
                # 使用绝对路径调用
                subprocess.run([flux_path, str(self.color_temperature)], 
                             check=True,
                             capture_output=True,
                             text=True,
                             creationflags=subprocess.CREATE_NO_WINDOW)
                print("f.lux调用成功")
            except subprocess.CalledProcessError as e:
                print(f"标准调用失败，尝试使用替代命令...")
                print(f"错误信息: {e.output if hasattr(e, 'output') else str(e)}")
                
                # 尝试使用替代命令
                try:
                    subprocess.run([flux_path, "-k", str(self.color_temperature)],
                                 check=True,
                                 capture_output=True,
                                 text=True,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
                    print("使用替代命令成功")
                except subprocess.CalledProcessError as e:
                    print(f"替代命令也失败了")
                    print(f"错误信息: {e.output if hasattr(e, 'output') else str(e)}")
                    
        except Exception as e:
            print(f"调整色温时出错: {e}")
            import traceback
            print(f"错误堆��:\n{traceback.format_exc()}")

    def adjust_settings_based_on_light(self, brightness):
        """根据环境光自动调整设置"""
        try:
            # 根据环境光亮度计算合适的屏幕亮度和色温
            if brightness < 50:  # 暗环境
                new_brightness = 30
                new_color_temp = 3500
            elif brightness < 100:  # 适中环境
                new_brightness = 50
                new_color_temp = 4500
            else:  # 明亮环境
                new_brightness = 70
                new_color_temp = 6500

            # 平滑过渡到新的设置
            self.brightness = int(0.7 * self.brightness + 0.3 * new_brightness)
            self.color_temperature = int(0.7 * self.color_temperature + 0.3 * new_color_temp)

            # 更新UI和实际设置
            self.brightness_slider.set(self.brightness)
            self.color_temp_slider.set(self.color_temperature)
            
            # 实际调整屏幕
            self.update_brightness(self.brightness)
            self.update_color_temperature(self.color_temperature)
            
        except Exception as e:
            print(f"自动调整设置时出错: {e}")

    def start_light_detection(self):
        self.light_detection_button.config(text="停止检测", command=self.stop_light_detection)
        self.light_detection_active = True
        threading.Thread(target=self.light_detection_thread, daemon=True).start()

    def stop_light_detection(self):
        self.light_detection_active = False
        self.light_detection_button.config(text="开始环境光检测", command=self.start_light_detection)

    def light_detection_thread(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("错误", "无法打开摄像头！")
            self.stop_light_detection()
            return

        try:
            while self.light_detection_active:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 计算图像的平均亮度
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                avg_brightness = np.mean(gray)

                # 更新显示的平均亮度，使用更好的格式化
                self.light_value_label.config(text=f"当前环境光: {avg_brightness:>6.1f}")

                # 根据平均亮度调整亮度和色温
                self.adjust_settings_based_on_light(avg_brightness)

                # 显示图像（可选）
                cv2.imshow('环境光检测', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            cap.release()
            cv2.destroyAllWindows()
            if self.light_detection_active:
                self.stop_light_detection()

    def save_settings(self):
        settings = {
            'brightness': self.brightness,
            'color_temperature': self.color_temperature,
            'timer_minutes': self.timer_entry.get()
        }
        try:
            with open('settings.txt', 'w') as f:
                for key, value in settings.items():
                    f.write(f"{key}={value}\n")
            messagebox.showinfo("成功", "设置已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存设置时出错: {str(e)}")

    def load_settings(self):
        try:
            if not os.path.exists('settings.txt'):
                messagebox.showinfo("提示", "没有找到保存的设置")
                return

            with open('settings.txt', 'r') as f:
                settings = dict(line.strip().split('=') for line in f if line.strip())
                
            if 'brightness' in settings:
                self.brightness_slider.set(int(settings['brightness']))
            if 'color_temperature' in settings:
                self.color_temp_slider.set(int(settings['color_temperature']))
            if 'timer_minutes' in settings:
                self.timer_entry.delete(0, tk.END)
                self.timer_entry.insert(0, settings['timer_minutes'])
                
            messagebox.showinfo("成功", "设置已加载")
        except Exception as e:
            messagebox.showerror("错误", f"加载设置时出错: {str(e)}")

    def start_timer_from_entry(self):
        try:
            minutes = int(self.timer_entry.get())
            if minutes <= 0:
                raise ValueError("时间必须大于0")
            self.start_timer(minutes * 60)  # 转换为秒
            messagebox.showinfo("提醒设置", f"已设置{minutes}分钟后提醒")
        except ValueError as e:
            messagebox.showerror("错误", f"请输入有效的时间: {str(e)}")

    def start_timer(self, duration):
        self.timer_thread = threading.Thread(target=self.timer_thread, args=(duration,), daemon=True)
        self.timer_thread.start()

    def timer_thread(self, duration):
        time.sleep(duration)
        self.show_reminder()

    def show_reminder(self):
        # 修改提醒消息，加入当前诗句
        current_poem = self.poetry_label.cget("text")
        messagebox.showinfo("休息提醒", 
            f"请注意休息，活动一下眼睛和身体\n\n"
            f"建议：\n"
            f"1. 远眺20秒\n"
            f"2. 眨眼20次\n"
            f"3. 起身活动5分钟\n\n"
            f"休息时可以欣赏一下这首诗：\n{current_poem}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop() 
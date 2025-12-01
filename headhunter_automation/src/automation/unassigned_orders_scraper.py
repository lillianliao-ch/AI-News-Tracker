"""
未分配订单抓取模块
专门用于获取最新的3条未分配订单的详细信息
"""

import time
import json
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger
import yaml
import os
import re


class UnassignedOrdersScraper:
    """未分配订单抓取器"""
    
    def __init__(self, config_path: str = "config/settings.yaml", 
                 credentials_path: str = "config/credentials.yaml"):
        """
        初始化抓取器
        
        Args:
            config_path: 配置文件路径
            credentials_path: 凭据文件路径
        """
        self.config = self._load_config(config_path)
        self.credentials = self._load_config(credentials_path)
        self.driver = None
        self.wait = None
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise
    
    def _setup_driver(self):
        """设置Chrome浏览器驱动"""
        try:
            chrome_options = Options()
            
            # 基本配置
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 隐藏自动化检测
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 设置User-Agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 创建驱动
            service = webdriver.chrome.service.Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 设置等待时间
            self.wait = WebDriverWait(self.driver, 20)
            
            # 执行JavaScript来隐藏自动化特征
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']})")
            
            logger.info("Chrome浏览器驱动设置成功")
            
        except Exception as e:
            logger.error(f"浏览器驱动设置失败: {e}")
            raise
    
    def login(self) -> bool:
        """
        登录阿里巴巴猎头系统
        
        Returns:
            bool: 登录是否成功
        """
        try:
            logger.info("开始登录阿里巴巴猎头系统...")
            
            # 访问登录页面
            login_url = f"{self.config['headhunter_system']['base_url']}{self.config['headhunter_system']['login_url']}"
            self.driver.get(login_url)
            logger.info(f"访问登录页面: {login_url}")
            
            # 等待页面加载
            time.sleep(5)
            
            # 等待页面完全加载
            self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            
            # 查找并填写用户名
            username_selectors = [
                "input[name='username']",
                "input[name='loginName']", 
                "input[name='account']",
                "input[type='text']",
                "input[type='email']",
                "#username",
                "#loginName",
                "#account"
            ]
            
            username_element = None
            for selector in username_selectors:
                try:
                    username_element = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if username_element.is_displayed() and username_element.is_enabled():
                        logger.info(f"找到用户名输入框: {selector}")
                        break
                except TimeoutException:
                    continue
            
            if not username_element:
                logger.error("无法找到用户名输入框")
                return False
            
            username_element.clear()
            username_element.send_keys(self.credentials['headhunter_credentials']['username'])
            logger.info("用户名输入完成")
            
            # 查找并填写密码
            password_selectors = [
                "input[name='password']",
                "input[type='password']",
                "#password"
            ]
            
            password_element = None
            for selector in password_selectors:
                try:
                    password_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if password_element.is_displayed() and password_element.is_enabled():
                        break
                except NoSuchElementException:
                    continue
            
            if not password_element:
                logger.error("无法找到密码输入框")
                return False
            
            password_element.clear()
            password_element.send_keys(self.credentials['headhunter_credentials']['password'])
            logger.info("密码输入完成")
            
            # 查找并点击登录按钮
            login_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                ".login-btn",
                "button:contains('登录')"
            ]
            
            login_element = None
            for selector in login_selectors:
                try:
                    login_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if login_element.is_displayed() and login_element.is_enabled():
                        break
                except NoSuchElementException:
                    continue
            
            if not login_element:
                logger.error("无法找到登录按钮")
                return False
            
            login_element.click()
            logger.info("点击登录按钮")
            
            # 等待登录完成
            time.sleep(5)
            
            # 验证登录是否成功
            current_url = self.driver.current_url
            if "login" not in current_url.lower() and "headhunter.alibaba.com" in current_url:
                logger.info("登录成功！")
                return True
            else:
                logger.error("登录失败，仍在登录页面")
                return False
                
        except Exception as e:
            logger.error(f"登录过程中发生错误: {e}")
            return False
    
    def navigate_to_unassigned_orders(self) -> bool:
        """
        导航到待分配订单页面
        
        Returns:
            bool: 导航是否成功
        """
        try:
            logger.info("导航到待分配订单页面...")
            
            # 直接访问待分配订单页面URL
            unassigned_orders_url = f"{self.config['headhunter_system']['base_url']}{self.config['headhunter_system']['unassigned_orders_url']}"
            self.driver.get(unassigned_orders_url)
            logger.info(f"访问待分配订单页面: {unassigned_orders_url}")
            
            # 等待页面加载
            time.sleep(5)
            
            # 验证是否成功加载页面
            current_url = self.driver.current_url
            if "task_management" in current_url:
                logger.info("成功导航到待分配订单页面")
                return True
            else:
                logger.error("导航到待分配订单页面失败")
                return False
                
        except Exception as e:
            logger.error(f"导航过程中发生错误: {e}")
            return False
    
    def get_latest_unassigned_orders(self, count: int = 3) -> List[Dict]:
        """
        获取最新的N条未分配订单
        
        Args:
            count: 获取订单数量
            
        Returns:
            List[Dict]: 订单数据列表
        """
        try:
            logger.info(f"开始获取最新的 {count} 条未分配订单...")
            
            # 等待表格加载
            table_selectors = [
                "table", ".orders-table", ".ant-table", 
                "[class*='table']", "[class*='order']"
            ]
            
            table_element = None
            for selector in table_selectors:
                try:
                    table_element = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not table_element:
                logger.error("未找到订单表格")
                return []
            
            # 获取表格数据
            orders = []
            rows = table_element.find_elements(By.TAG_NAME, "tr")
            
            # 跳过表头，处理数据行
            for row in rows[1:]:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 4:  # 确保有足够的列
                        order_data = {
                            'job_position': cells[1].text.strip(),  # 招聘职位
                            'work_location': cells[2].text.strip(),  # 工作地点
                            'update_date': cells[3].text.strip(),  # 更新日期
                            'job_publisher': cells[4].text.strip() if len(cells) > 4 else '',  # 职位发布人
                            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # 解析更新日期用于排序
                        try:
                            update_time = datetime.strptime(order_data['update_date'], '%Y-%m-%d %H:%M:%S')
                            order_data['update_time'] = update_time
                        except ValueError:
                            order_data['update_time'] = datetime.min
                        
                        orders.append(order_data)
                        
                except Exception as e:
                    logger.warning(f"解析行数据时出错: {e}")
                    continue
            
            # 按更新日期排序，获取最新的N条
            orders.sort(key=lambda x: x['update_time'], reverse=True)
            latest_orders = orders[:count]
            
            logger.info(f"成功获取 {len(latest_orders)} 条最新未分配订单")
            return latest_orders
            
        except Exception as e:
            logger.error(f"获取未分配订单数据时发生错误: {e}")
            return []
    
    def extract_department_from_job_position(self, job_position: str) -> str:
        """
        从职位名称中提取部门信息
        
        Args:
            job_position: 职位名称
            
        Returns:
            str: 部门名称
        """
        try:
            # 使用连字符分割，第一部分通常是部门
            parts = job_position.split('-')
            if len(parts) > 0:
                department = parts[0].strip()
                # 移除括号内的内容
                if '(' in department:
                    department = department.split('(')[0].strip()
                return department
            return "未知部门"
        except Exception as e:
            logger.warning(f"提取部门信息失败: {e}")
            return "未知部门"
    
    def get_job_description_from_detail_page(self, job_position: str) -> str:
        """
        从职位详情页获取岗位描述
        
        Args:
            job_position: 职位名称
            
        Returns:
            str: 岗位描述
        """
        try:
            # 查找职位名称链接
            job_links = self.driver.find_elements(By.XPATH, f"//a[contains(text(), '{job_position[:20]}')]")
            
            if not job_links:
                logger.warning(f"未找到职位 '{job_position}' 的详情链接")
                return "无法获取岗位描述"
            
            job_link = job_links[0]
            original_window = self.driver.current_window_handle
            
            # 打开新标签页
            self.driver.execute_script("arguments[0].click();", job_link)
            
            # 等待新标签页打开
            time.sleep(3)
            
            # 切换到新标签页
            new_window = None
            for window in self.driver.window_handles:
                if window != original_window:
                    new_window = window
                    break
            
            if new_window:
                self.driver.switch_to.window(new_window)
                
                # 等待页面加载
                time.sleep(3)
                
                # 查找岗位描述
                description_selectors = [
                    ".job-description",
                    ".position-description", 
                    ".job-detail-content",
                    "[class*='description']",
                    "[class*='content']"
                ]
                
                description = "无法获取岗位描述"
                for selector in description_selectors:
                    try:
                        desc_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if desc_element.text.strip():
                            description = desc_element.text.strip()
                            break
                    except NoSuchElementException:
                        continue
                
                # 关闭当前标签页
                self.driver.close()
                
                # 切换回原窗口
                self.driver.switch_to.window(original_window)
                
                return description
            else:
                logger.warning("未找到新打开的标签页")
                return "无法获取岗位描述"
                
        except Exception as e:
            logger.error(f"获取岗位描述时发生错误: {e}")
            return f"获取岗位描述失败: {str(e)}"
    
    def get_detailed_orders_info(self, count: int = 3) -> List[Dict]:
        """
        获取最新的N条未分配订单的详细信息
        
        Args:
            count: 获取订单数量
            
        Returns:
            List[Dict]: 包含职位名称、部门、岗位描述的订单信息
        """
        try:
            logger.info(f"开始获取最新的 {count} 条未分配订单详细信息...")
            
            # 获取最新订单
            latest_orders = self.get_latest_unassigned_orders(count)
            
            if not latest_orders:
                logger.warning("未获取到任何订单数据")
                return []
            
            detailed_orders = []
            
            for i, order in enumerate(latest_orders, 1):
                logger.info(f"处理第 {i}/{len(latest_orders)} 条订单...")
                
                job_position = order['job_position']
                
                # 提取部门信息
                department = self.extract_department_from_job_position(job_position)
                
                # 获取岗位描述
                job_description = self.get_job_description_from_detail_page(job_position)
                
                detailed_order = {
                    '职位名称': job_position,
                    '部门': department,
                    '岗位描述': job_description,
                    '工作地点': order['work_location'],
                    '更新日期': order['update_date'],
                    '职位发布人': order['job_publisher'],
                    '抓取时间': order['scraped_at']
                }
                
                detailed_orders.append(detailed_order)
                logger.info(f"完成第 {i} 条订单处理")
                
                # 添加延迟避免请求过快
                time.sleep(2)
            
            logger.info(f"成功获取 {len(detailed_orders)} 条订单的详细信息")
            return detailed_orders
            
        except Exception as e:
            logger.error(f"获取订单详细信息时发生错误: {e}")
            return []
    
    def save_orders_to_file(self, orders: List[Dict], filename: str = None) -> str:
        """
        保存订单数据到文件
        
        Args:
            orders: 订单数据列表
            filename: 文件名
            
        Returns:
            str: 保存的文件路径
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"data/latest_unassigned_orders_{timestamp}.json"
            
            # 确保目录存在
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # 保存数据
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(orders, f, ensure_ascii=False, indent=2)
            
            logger.info(f"订单数据已保存到: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"保存文件时发生错误: {e}")
            raise
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器已关闭")
    
    def run_full_automation(self, count: int = 3) -> List[Dict]:
        """
        运行完整的自动化流程
        
        Args:
            count: 获取订单数量
            
        Returns:
            List[Dict]: 获取的订单数据
        """
        try:
            logger.info("开始运行完整自动化流程...")
            
            # 设置浏览器
            self._setup_driver()
            
            # 登录
            if not self.login():
                raise Exception("登录失败")
            
            # 导航到待分配订单页面
            if not self.navigate_to_unassigned_orders():
                raise Exception("导航到待分配订单页面失败")
            
            # 获取订单详细信息
            orders = self.get_detailed_orders_info(count)
            
            # 保存数据
            if orders:
                self.save_orders_to_file(orders)
            
            return orders
            
        except Exception as e:
            logger.error(f"自动化流程执行失败: {e}")
            raise
        finally:
            self.close()


def main():
    """主函数"""
    try:
        # 创建抓取器实例
        scraper = UnassignedOrdersScraper()
        
        # 运行自动化流程
        orders = scraper.run_full_automation(count=3)
        
        print(f"成功获取 {len(orders)} 条最新未分配订单的详细信息")
        for i, order in enumerate(orders, 1):
            print(f"\n{i}. {order['职位名称']}")
            print(f"   部门: {order['部门']}")
            print(f"   岗位描述: {order['岗位描述'][:100]}...")
            print(f"   更新日期: {order['更新日期']}")
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"程序执行失败: {e}")


if __name__ == "__main__":
    main()

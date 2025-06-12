from playwright.sync_api import sync_playwright
import os
# 不再需要 requests 库，因为移除了 Telegram 功能
# import requests

def login_searcade(username, password):
    with sync_playwright() as p:
        # 在GitHub Actions环境中，通常需要headless模式
        # 调试时可以在本地运行并改为 False: browser = p.chromium.launch(headless=False)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 步骤 1: 访问主页面 https://searcade.com/en/
            print("正在访问主页: https://searcade.com/en/")
            page.goto("https://searcade.com/en/", wait_until="networkidle")

            # 步骤 2: 点击主页上的 "Login" 链接
            # 根据截图，Login 链接的文本是 "Login"
            login_link_selector = 'a:has-text("Login")' # 或者 'text=Login'
            print(f"正在点击登录链接: {login_link_selector}")
            page.wait_for_selector(login_link_selector, timeout=30000) # 等待Login链接出现
            page.click(login_link_selector)

            # 步骤 3: 等待页面跳转到登录页面 https://searcade.userveria.com/login
            print("正在等待跳转到登录页面: https://searcade.userveria.com/login")
            page.wait_for_url("https://searcade.userveria.com/login", timeout=30000)
            print("已成功跳转到登录页面。")

            # 步骤 4: 填充登录表单
            username_selector = 'input[name="email"]'
            password_selector = 'input[name="password"]'
            login_button_selector = 'button:has-text("Login")'

            print(f"正在等待用户名输入框: {username_selector}")
            page.wait_for_selector(username_selector, timeout=60000) # 增加超时时间
            print(f"正在等待密码输入框: {password_selector}")
            page.wait_for_selector(password_selector, timeout=60000) # 增加超时时间
            print(f"正在等待登录按钮: {login_button_selector}")
            page.wait_for_selector(login_button_selector, timeout=60000) # 增加超时时间

            print(f"正在填充账号: {username}")
            page.fill(username_selector, username)
            page.fill(password_selector, password)

            print("正在点击登录按钮...")
            page.click(login_button_selector)

            # 步骤 5: 等待登录后的页面跳转或错误消息
            try:
                print("正在等待登录成功后的页面...")
                page.wait_for_url("https://searcade.userveria.com/", timeout=15000)
                print(f"账号 {username} 登录成功!")
            except Exception as e:
                # 登录失败，尝试查找错误消息
                error_message_selector = '.alert.alert-danger, .error-message, .form-error'
                print("登录失败，正在尝试查找错误消息...")
                try:
                    error_element = page.wait_for_selector(error_message_selector, timeout=5000)
                    if error_element:
                        error_text = error_element.inner_text().strip()
                        print(f"账号 {username} 登录失败: {error_text}")
                        page.screenshot(path=f"login_fail_{username.replace('@', '_').replace('.', '_')}.png")
                        raise RuntimeError(f"登录失败: {error_text}")
                    else:
                        print(f"账号 {username} 登录失败: 未能跳转到预期页面且未检测到特定错误消息。")
                        page.screenshot(path=f"login_no_error_msg_{username.replace('@', '_').replace('.', '_')}.png")
                        raise RuntimeError("登录失败: 未检测到错误消息或成功跳转。")
                except Exception as e_inner:
                    print(f"账号 {username} 登录失败: 未能跳转到预期页面且未找到错误消息。可能的原因: {e_inner}")
                    page.screenshot(path=f"login_error_lookup_fail_{username.replace('@', '_').replace('.', '_')}.png")
                    raise RuntimeError(f"登录失败且查找错误消息失败: {e_inner}")
        except Exception as e:
            # 捕获任何在页面操作中发生的异常，包括初始导航或元素等待超时
            print(f"处理账号 {username} 时发生错误: {e}")
            page.screenshot(path=f"process_error_{username.replace('@', '_').replace('.', '_')}.png") # 更改截图文件名以便区分
            raise RuntimeError(f"登录操作中断: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    accounts_str = os.environ.get('SEARCADE_ACCOUNTS', '')
    if not accounts_str:
        print("环境变量 'SEARCADE_ACCOUNTS' 未设置或为空。请设置账号信息。")
        exit(1)

    accounts = accounts_str.split()
    any_account_failed = False

    for account in accounts:
        try:
            username, password = account.split(':', 1)
            login_searcade(username, password)
            print(f"账号 {username} 处理完成。")
        except ValueError:
            print(f"账号信息格式错误: {account}。应为 'username:password'")
            any_account_failed = True
        except RuntimeError as e:
            print(f"账号 {username} 处理失败: {e}")
            any_account_failed = True

    if any_account_failed:
        print("部分或所有账号处理失败，退出码为 1。")
        exit(1)
    else:
        print("所有账号均已成功处理。")
        exit(0)

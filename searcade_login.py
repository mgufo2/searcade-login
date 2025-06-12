from playwright.sync_api import sync_playwright
import os
# 不再需要 requests 库，因为移除了 Telegram 功能
# import requests

# 移除 send_telegram_message 函数，因为它不再需要

def login_searcade(username, password):
    with sync_playwright() as p:
        # 在GitHub Actions环境中，通常需要headless模式
        # 调试时可以在本地运行并改为 False: browser = p.chromium.launch(headless=False)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 访问Searcade登录页面，等待网络空闲，确保所有网络请求都已停止
            page.goto("https://searcade.userveria.com/login", wait_until="networkidle")

            # 根据您提供的HTML结果，用户名输入框的实际 name 属性是 "email"
            username_selector = 'input[name="email"]'
            # 密码框通常是 name="password"
            password_selector = 'input[name="password"]'
            # 按钮文本是“Login”
            login_button_selector = 'button:has-text("Login")'

            # 增加等待时间，防止网络延迟导致元素未及时出现
            page.wait_for_selector(username_selector, timeout=60000)
            page.wait_for_selector(password_selector, timeout=60000)
            page.wait_for_selector(login_button_selector, timeout=60000)

            # 输入邮箱地址或用户名和密码
            page.fill(username_selector, username)
            page.fill(password_selector, password)

            # 点击登录按钮
            page.click(login_button_selector)

            # 等待登录后的页面跳转或错误消息
            try:
                page.wait_for_url("https://searcade.userveria.com/", timeout=15000)
                print(f"账号 {username} 登录成功!")
                # 如果成功登录，则不抛出异常，让脚本正常退出
            except Exception as e:
                # 登录失败，尝试查找错误消息
                error_message_selector = '.alert.alert-danger, .error-message, .form-error'
                try:
                    error_element = page.wait_for_selector(error_message_selector, timeout=5000)
                    if error_element:
                        error_text = error_element.inner_text().strip()
                        print(f"账号 {username} 登录失败: {error_text}")
                        # 登录失败时截图
                        page.screenshot(path=f"login_fail_{username.replace('@', '_').replace('.', '_')}.png")
                        # 强制抛出异常，以便GitHub Actions捕获到失败
                        raise RuntimeError(f"登录失败: {error_text}")
                    else:
                        print(f"账号 {username} 登录失败: 未能跳转到预期页面且未检测到特定错误消息。")
                        # 登录失败且未检测到特定错误消息时截图
                        page.screenshot(path=f"login_no_error_msg_{username.replace('@', '_').replace('.', '_')}.png")
                        # 强制抛出异常
                        raise RuntimeError("登录失败: 未检测到错误消息或成功跳转。")
                except Exception as e_inner:
                    print(f"账号 {username} 登录失败: 未能跳转到预期页面且未找到错误消息。可能的原因: {e_inner}")
                    # 查找错误消息时发生异常也截图
                    page.screenshot(path=f"login_error_lookup_fail_{username.replace('@', '_').replace('.', '_')}.png")
                    # 强制抛出异常
                    raise RuntimeError(f"登录失败且查找错误消息失败: {e_inner}")
        except Exception as e:
            # 捕获任何在页面操作中发生的异常，包括初始元素等待超时
            print(f"处理账号 {username} 时发生错误: {e}")
            # 关键：在这里截图，可以看到超时发生时页面处于什么状态
            page.screenshot(path=f"timeout_error_{username.replace('@', '_').replace('.', '_')}.png")
            # 强制抛出异常，确保GitHub Actions捕获到失败
            raise RuntimeError(f"登录操作中断: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    # 获取账号信息，格式为 "username1:password1 username2:password2"
    accounts_str = os.environ.get('SEARCADE_ACCOUNTS', '')
    if not accounts_str:
        print("环境变量 'SEARCADE_ACCOUNTS' 未设置或为空。请设置账号信息。")
        exit(1) # 如果没有账号，直接退出

    accounts = accounts_str.split()
    
    # 跟踪是否有任何一个账号处理失败
    any_account_failed = False

    for account in accounts:
        try:
            username, password = account.split(':', 1)
            # 调用 login_searcade 函数，期望它在失败时抛出异常
            login_searcade(username, password)
            # 如果没有抛出异常，说明该账号登录成功
            print(f"账号 {username} 处理完成。")
        except ValueError:
            print(f"账号信息格式错误: {account}。应为 'username:password'")
            any_account_failed = True # 标记为失败
        except RuntimeError as e: # 捕获从 login_searcade 抛出的 RuntimeError
            print(f"账号 {username} 处理失败: {e}")
            any_account_failed = True # 标记为失败

    # 如果任何一个账号处理失败，则以非零退出码退出，让GitHub Actions标记为失败
    if any_account_failed:
        print("部分或所有账号处理失败，退出码为 1。")
        exit(1)
    else:
        print("所有账号均已成功处理。")
        exit(0) # 所有账号都成功，退出码为 0

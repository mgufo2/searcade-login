from playwright.sync_api import sync_playwright
import os
import requests

def send_telegram_message(message):
    bot_token = os.environ.get('TEL_TOK')
    chat_id = os.environ.get('TEL_ID')
    if not bot_token or not chat_id:
        print("Telegram Bot Token或Chat ID未配置。跳过发送消息。")
        return None
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # 检查HTTP错误
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"发送Telegram消息失败: {e}")
        return None

def login_searcade(username, password):
    with sync_playwright() as p:
        # 在GitHub Actions环境中，通常需要headless模式
        # 调试时可以在本地运行并改为 False: browser = p.chromium.launch(headless=False)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 访问Searcade登录页面，等待网络空闲，确保所有网络请求都已停止
            # 解决方案二: 更改 wait_until 为 "networkidle"
            page.goto("https://searcade.userveria.com/login", wait_until="networkidle")

            # 根据您提供的HTML结果，用户名输入框的实际 name 属性是 "email"
            username_selector = 'input[name="email"]'
            # 密码框通常是 name="password"
            password_selector = 'input[name="password"]'
            # 按钮文本是“Login”
            login_button_selector = 'button:has-text("Login")'

            # 增加等待时间，防止网络延迟导致元素未及时出现
            # 解决方案二: 增加超时时间到 60 秒
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
                return f"账号 {username} 登录成功!"
            except Exception as e:
                # 登录失败，尝试查找错误消息
                error_message_selector = '.alert.alert-danger, .error-message, .form-error'
                try:
                    error_element = page.wait_for_selector(error_message_selector, timeout=5000)
                    if error_element:
                        error_text = error_element.inner_text().strip()
                        print(f"账号 {username} 登录失败: {error_text}")
                        # 解决方案四: 登录失败时截图
                        page.screenshot(path=f"login_fail_{username.replace('@', '_').replace('.', '_')}.png")
                        return f"账号 {username} 登录失败: {error_text}"
                    else:
                        print(f"账号 {username} 登录失败: 未能跳转到预期页面且未检测到特定错误消息。")
                        # 解决方案四: 登录失败且未检测到特定错误消息时截图
                        page.screenshot(path=f"login_no_error_msg_{username.replace('@', '_').replace('.', '_')}.png")
                        return f"账号 {username} 登录失败: 未能跳转到预期页面且未检测到特定错误消息。"
                except Exception as e_inner:
                    print(f"账号 {username} 登录失败: 未能跳转到预期页面且未找到错误消息。可能的原因: {e_inner}")
                    # 解决方案四: 查找错误消息时发生异常也截图
                    page.screenshot(path=f"login_error_lookup_fail_{username.replace('@', '_').replace('.', '_')}.png")
                    return f"账号 {username} 登录失败: 未能跳转到预期页面且未找到错误消息。"
        except Exception as e:
            # 捕获任何在页面操作中发生的异常，包括初始元素等待超时
            print(f"处理账号 {username} 时发生错误: {e}")
            # 解决方案四: 关键：在这里截图，可以看到超时发生时页面处于什么状态
            page.screenshot(path=f"timeout_error_{username.replace('@', '_').replace('.', '_')}.png")
            return f"账号 {username} 登录操作中断: {e}"
        finally:
            browser.close()

if __name__ == "__main__":
    # 从环境变量获取账号信息，格式为 "username1:password1 username2:password2"
    accounts_str = os.environ.get('SEARCADE_ACCOUNTS', '')
    if not accounts_str:
        error_msg = "环境变量 'SEARCADE_ACCOUNTS' 未设置或为空。请设置账号信息。"
        print(error_msg)
        send_telegram_message(error_msg)
        exit(1)

    accounts = accounts_str.split()
    login_statuses = []

    for account in accounts:
        try:
            username, password = account.split(':', 1) # 使用split(':', 1)防止密码中包含冒号
            status = login_searcade(username, password)
            login_statuses.append(status)
            print(status)
        except ValueError:
            status = f"账号信息格式错误: {account}。应为 'username:password'"
            login_statuses.append(status)
            print(status)

    if login_statuses:
        message_to_send = "Searcade登录状态:\n\n" + "\n".join(login_statuses)
        result = send_telegram_message(message_to_send)
        if result:
            print("消息已发送到Telegram:", result)
        else:
            print("未能成功发送Telegram消息。")
    else:
        error_message = "没有处理任何账号。"
        send_telegram_message(error_message)
        print(error_message)

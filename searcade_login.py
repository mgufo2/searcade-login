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
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 访问Searcade登录页面
        page.goto("https://searcade.userveria.com/login")

        # 确保页面加载完成
        page.wait_for_selector('input[name="username"]')
        page.wait_for_selector('input[name="password"]')
        page.wait_for_selector('button[type="submit"]')

        # 输入邮箱地址或用户名和密码
        page.fill('input[name="username"]', username)
        page.fill('input[name="password"]', password)

        # 点击登录按钮
        page.click('button[type="submit"]')

        # 等待登录后的页面跳转或错误消息
        try:
            # 尝试等待登录成功后的某个元素或URL
            # 这里需要根据实际登录成功后的页面内容来调整等待条件
            # 假设登录成功后会跳转到根路径 / 或出现特定的仪表板元素
            page.wait_for_url("https://searcade.userveria.com/", timeout=10000)
            # 或者等待页面上某个只有登录成功后才会出现的元素
            # page.wait_for_selector('.dashboard-element', timeout=10000)
            print(f"账号 {username} 登录成功!")
            return f"账号 {username} 登录成功!"
        except Exception as e:
            # 如果没有成功跳转，尝试查找错误消息
            try:
                error_message_selector = '.alert.alert-danger' # 假设错误消息会出现在此类元素中
                error_element = page.wait_for_selector(error_message_selector, timeout=3000)
                if error_element:
                    error_text = error_element.inner_text()
                    print(f"账号 {username} 登录失败: {error_text}")
                    return f"账号 {username} 登录失败: {error_text}"
                else:
                    print(f"账号 {username} 登录失败: 未检测到错误消息或成功跳转。")
                    return f"账号 {username} 登录失败: 未检测到错误消息或成功跳转。"
            except Exception as e_inner:
                print(f"账号 {username} 登录失败: 未能跳转到预期页面且未找到错误消息。可能的原因: {e_inner}")
                return f"账号 {username} 登录失败: 未能跳转到预期页面且未找到错误消息。"
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

from playwright.sync_api import sync_playwright
import os

def login_searcade(username, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print("正在访问主页: https://searcade.com/en/")
            page.goto("https://searcade.com/en/", wait_until="networkidle")

            login_link_selector = 'a:has-text("Login")'
            print(f"正在点击登录链接: {login_link_selector}")
            page.wait_for_selector(login_link_selector, timeout=30000)
            page.click(login_link_selector)

            print("正在等待跳转到登录页面: https://searcade.userveria.com/login")
            page.wait_for_url("https://searcade.userveria.com/login", timeout=30000)
            print("已成功跳转到登录页面。")

            username_selector = 'input[name="email"]'
            password_selector = 'input[name="password"]'
            login_button_selector = 'button:has-text("Login")'

            print(f"正在等待用户名输入框: {username_selector}")
            page.wait_for_selector(username_selector, timeout=60000)
            print(f"正在等待密码输入框: {password_selector}")
            page.wait_for_selector(password_selector, timeout=60000)
            print(f"正在等待登录按钮: {login_button_selector}")
            page.wait_for_selector(login_button_selector, timeout=60000)

            print(f"正在填充账号: {username}")
            page.fill(username_selector, username)
            page.fill(password_selector, password)

            print("正在点击登录按钮...")
            page.click(login_button_selector)

            # ******** 关键修改点：判断登录成功逻辑 ********
            # 不再等待URL严格匹配，而是等待登录成功后的页面特有元素
            # 从截图看，登录成功后页面有 "Welcome back [用户名]!" 文本
            # 也可以等待 "Logout" 按钮或者 "Your servers" 标题
            success_indicator_selector = 'text="Welcome back"' # 或者 'text="Your servers"', 'a:has-text("Logout")'

            print(f"正在等待登录成功指示器: {success_indicator_selector}")
            try:
                # 等待 Welcome back 文本出现，或等待其他成功的元素
                page.wait_for_selector(success_indicator_selector, timeout=20000) # 20秒应该足够
                print(f"账号 {username} 登录成功!")
                # 如果代码执行到这里，说明成功登录，不需要抛出异常
            except Exception as e:
                # 如果没有找到成功指示器，那可能就是登录失败了
                # 此时可以尝试查找错误消息，或者直接标记为失败
                error_message_selector = '.alert.alert-danger, .error-message, .form-error'
                print("未找到登录成功指示器，尝试查找错误消息...")
                try:
                    error_element = page.wait_for_selector(error_message_selector, timeout=5000)
                    if error_element:
                        error_text = error_element.inner_text().strip()
                        print(f"账号 {username} 登录失败: {error_text}")
                        page.screenshot(path=f"login_fail_{username.replace('@', '_').replace('.', '_')}.png")
                        raise RuntimeError(f"登录失败: {error_text}")
                    else:
                        # 既没有成功指示器，也没有明显的错误消息，仍然认为是失败
                        print(f"账号 {username} 登录失败: 未找到成功指示器且未检测到特定错误消息。")
                        page.screenshot(path=f"login_mystery_fail_{username.replace('@', '_').replace('.', '_')}.png")
                        raise RuntimeError("登录失败: 状态不明确，未找到成功指示器。")
                except Exception as e_inner:
                    print(f"账号 {username} 登录失败: 未找到成功指示器，且查找错误消息失败。可能的原因: {e_inner}")
                    page.screenshot(path=f"login_error_lookup_fail_{username.replace('@', '_').replace('.', '_')}.png")
                    raise RuntimeError(f"登录失败: 无法确认成功或错误。")
        except Exception as e:
            print(f"处理账号 {username} 时发生错误: {e}")
            page.screenshot(path=f"process_error_{username.replace('@', '_').replace('.', '_')}.png")
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

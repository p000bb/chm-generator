# PHPSESSID 获取方法

## 什么是 PHPSESSID

PHPSESSID 是 PHP 会话标识符，用于在访问需要登录的网站时维持用户会话状态。在 CHM 生成工具中，它用于访问需要身份验证的下载资源。

## 获取步骤

### 方法一：通过浏览器开发者工具

1. 打开浏览器，访问<a href="https://www.nationstech.com" target="_blank">国民技术官网</a>
2. 登录你的账户
3. 按 `F12` 打开开发者工具
4. 切换到 **Application** 或 **应用** 标签页
5. 在左侧找到 **Cookie**
6. 选择对应的域名
7. 找到名为 `PHPSESSID` 的 Cookie值
8. 复制其值

## 截图参考
<img src="/helpdoc/images/phpsessid-1.png" alt="PHPSESSID" width="600" />

## 注意事项

- PHPSESSID 有时效性，通常会在一定时间后过期
- 如果遇到访问被拒绝的情况，可能需要重新获取 PHPSESSID
- 请确保你有权限访问相关资源，避免使用他人的会话标识符

## 使用示例

在配置页面中，将获取到的 PHPSESSID 值粘贴到对应输入框中即可。

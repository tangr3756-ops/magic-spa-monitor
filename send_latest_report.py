import json
import glob
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def send_latest_report():
    # 找最新的报告文件
    files = glob.glob("magic_spa_report_*.json")
    if not files:
        print("没有找到任何报告文件")
        return False

    latest_file = max(files, key=os.path.getctime)
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    analysis = data["analysis"]
    date_str = data["date"][:10]  # 只取日期

    # 构建邮件正文
    body = f"""
Magic Spa 评论报告 - {date_str}

店铺名称: {data["business_name"]}
地址: {data["formatted_address"]}
总体评分: {data["rating"]} / 5 (总 {data["user_rating_count"]} 条评价)

分析结果:
- 总评论数: {analysis["total_reviews"]}
- 好评数: {analysis["good"]}
- 差评数: {analysis["bad"]}
- 中评数: {analysis["mid"]}
- 平均评分: {analysis["avg_rating"]}
- 今日新评论: {analysis["today_new"]}

报告文件: {latest_file}
    """

    # 构建邮件
    msg = MIMEMultipart("alternative")
    msg["From"] = Header(os.getenv("EMAIL_SENDER"))
    msg["To"] = Header(os.getenv("TO_ADDR"))
    msg["Subject"] = Header(f"Magic Spa 评论报告 - {date_str}", 'utf-8')
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    to_addr = os.getenv("TO_ADDR")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.qq.com")
    smtp_port = int(os.getenv("SMTP_PORT", 465))

    try:
        print(f"📧 正在发送最新报告 ({latest_file})...")
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15)
        server.login(sender, password)
        server.sendmail(sender, to_addr, msg.as_string())
        server.quit()
        print("✅ 邮件发送成功！")
        return True
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        return False

if __name__ == "__main__":
    send_latest_report()
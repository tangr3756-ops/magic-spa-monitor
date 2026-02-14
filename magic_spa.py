print(f"本次运行时间 (UTC): {datetime.utcnow()}")
print(f"本次运行时间 (Houston): {datetime.now(pytz.timezone('America/Chicago'))}")
import os
import requests
import json
from datetime import datetime
import pytz
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class MagicSpaMonitor:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        self.business_name = os.getenv("BUSINESS_NAME", "Magic Spa")
        self.place_id = os.getenv("BUSINESS_PLACE_ID")  # 可选，如果有 place_id 直接用
        self.timezone = pytz.timezone('America/Chicago')  # Houston 时区

        if not self.api_key:
            raise ValueError("缺少 GOOGLE_PLACES_API_KEY，请检查 .env 文件")

    def fetch_place_details(self):
        """使用 Places API (New) 获取店铺详情和评论"""
        if not self.place_id:
            # 如果没有 place_id，先用 Text Search 找
            search_url = "https://places.googleapis.com/v1/places:searchText"
            payload = {
                "textQuery": self.business_name + " Orlando",
                "maxResultCount": 1
            }
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount"
            }
            response = requests.post(search_url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("places"):
                    self.place_id = data["places"][0]["id"]
                    print(f"找到 place_id: {self.place_id}")
                else:
                    raise ValueError("未找到店铺")
            else:
                raise Exception(f"搜索失败: {response.text}")

        # 获取详情 + 评论
        detail_url = f"https://places.googleapis.com/v1/places/{self.place_id}"
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "id,displayName,formattedAddress,rating,userRatingCount,reviews"
        }
        response = requests.get(detail_url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"获取详情失败: {response.text}")

        return response.json()

    def analyze_reviews(self, place_data):
        """分析评论"""
        reviews = place_data.get("reviews", [])
        total_reviews = len(reviews)
        good = 0
        bad = 0
        mid = 0
        ratings_sum = 0

        today = datetime.now(self.timezone).date()
        today_new = 0

        for r in reviews:
            rating = r.get("rating", 0)
            ratings_sum += rating

            if rating >= 4:
                good += 1
            elif rating <= 2:
                bad += 1
            else:
                mid += 1

            # 判断是否今天评论（如果有 publishTime）
            publish_time_str = r.get("publishTime")
            if publish_time_str:
                try:
                    publish_dt = datetime.fromisoformat(publish_time_str.replace("Z", "+00:00"))
                    if publish_dt.date() == today:
                        today_new += 1
                except:
                    pass

        avg_rating = ratings_sum / total_reviews if total_reviews > 0 else 0

        return {
            "total_reviews": total_reviews,
            "good": good,
            "bad": bad,
            "mid": mid,
            "avg_rating": round(avg_rating, 1),
            "today_new": today_new,
            "raw_reviews": reviews  # 保存原始评论数据
        }

    def save_report(self, place_data, analysis):
        """保存报告到本地 JSON 文件"""
        report = {
            "date": datetime.now(self.timezone).strftime("%Y-%m-%d %H:%M:%S"),
            "business_name": place_data.get("displayName", {}).get("text", "未知"),
            "formatted_address": place_data.get("formattedAddress", "未知"),
            "rating": place_data.get("rating", "未知"),
            "user_rating_count": place_data.get("userRatingCount", 0),
            "analysis": analysis
        }

        filename = f"magic_spa_report_{datetime.now(self.timezone).strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=4)

        print(f"✅ 报告已保存到本地文件: {filename}")

    def run(self):
        print("=" * 60)
        print(f"🚀 开始执行 {self.business_name} 评论监控")
        print("=" * 60)

        try:
            print("🔍 正在获取店铺详情...")
            place_data = self.fetch_place_details()

            print(f"✅ 店铺信息：{place_data.get('displayName', {}).get('text')}")
            print(f"📍 地址：{place_data.get('formattedAddress')}")
            print(f"⭐ 评分：{place_data.get('rating')}/5 ({place_data.get('userRatingCount')} 条评价)")

            print("\n📊 正在分析评论...")
            analysis = self.analyze_reviews(place_data)

            # 保存报告
            self.save_report(place_data, analysis)

            print("=" * 60)
            print("📈 执行摘要:")
            print(f"   Total Reviews: {analysis['total_reviews']}")
            print(f"   Good: {analysis['good']}")
            print(f"   Bad: {analysis['bad']}")
            print(f"   Mid: {analysis['mid']}")
            print(f"   Avg Rating: {analysis['avg_rating']}")
            print(f"   Today New: {analysis['today_new']}")
            print("=" * 60)
            print("✅ 程序执行成功")

        except Exception as e:
            print(f"❌ 程序执行出错: {e}")
            print("程序执行失败")


if __name__ == "__main__":
    monitor = MagicSpaMonitor()
    monitor.run()

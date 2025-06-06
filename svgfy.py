import requests
from datetime import datetime, timedelta
import random
import calendar
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

# Gitからユーザー情報を取得
def get_git_username():
    try:
        # gitコマンドからユーザー名を取得
        git_username = subprocess.check_output(
            ["git", "config", "user.name"], 
            stderr=subprocess.STDOUT,
            universal_newlines=True
        ).strip()
        return git_username
    except subprocess.CalledProcessError:
        return None

def get_git_email():
    try:
        # gitコマンドからメールアドレスを取得
        git_email = subprocess.check_output(
            ["git", "config", "user.email"], 
            stderr=subprocess.STDOUT,
            universal_newlines=True
        ).strip()
        return git_email
    except subprocess.CalledProcessError:
        return None

# GitHubユーザー名の取得（環境変数 > gitコンフィグ > デフォルト値）
USERNAME = os.getenv("GITHUB_USERNAME") or get_git_username()
TOKEN = os.getenv("TOKEN")

# 動物の種類と絵文字を定義
ANIMALS = [
    {"emoji": "🐿️", "name": "リス"},
    {"emoji": "🐭", "name": "ネズミ"},
    {"emoji": "🦝", "name": "アライグマ"},
    {"emoji": "🦊", "name": "キツネ"},
    {"emoji": "🐹", "name": "ハムスター"}
]

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

today = datetime.utcnow()
last_year = today - timedelta(days=365)

variables = {
    "login": USERNAME,
    "from": last_year.isoformat() + "Z",  # 例: '2024-05-30T00:00:00Z'
    "to": today.isoformat() + "Z"
}

response = requests.post(
    "https://api.github.com/graphql",
    json={"query": query, "variables": variables},
    headers=headers
)
data = response.json()

# 日付→コミット数のマップを作成
commit_days = {}
weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
for week in weeks:
    for day in week["contributionDays"]:
        commit_days[day["date"]] = day["contributionCount"]

# 最新コミット日の取得
latest_day = max((d for d in commit_days if commit_days[d] > 0), default=None)
print(f"最新コミット日: {latest_day}")

# SVG設定
cell_size = 12
padding = 2
top_margin = 20
left_margin = 30
weeks = 53
width = left_margin + (cell_size + padding) * weeks
height = top_margin + (cell_size + padding) * 7

# 色の濃淡定義
def get_color(count):
    if count == 0:
        return "#ebedf0"
    elif count < 2:
        return "#c6e48b"
    elif count < 4:
        return "#7bc96f"
    elif count < 6:
        return "#239a3b"
    else:
        return "#196127"

# 月名取得用
month_names = {i: name for i, name in enumerate(calendar.month_abbr) if i != 0}

# 出力ディレクトリの確認と作成
output_dir = os.getenv("OUTPUT_DIR", "")
output_file = os.getenv("OUTPUT_FILE", "output.svg")
output_path = os.path.join(output_dir, output_file) if output_dir else output_file

if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir)

# SVG出力
with open(output_path, "w") as f:
    # SVGヘッダーとスタイル
    f.write(f'''<svg width="{width}" height="{height + 20}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .label {{ font-size: 10px; fill: #555; }}
    .month {{ font-size: 10px; fill: #555; }}
    .tooltip {{ visibility: hidden; font-size: 10px; background-color: rgba(0,0,0,0.8); color: white; padding: 3px; border-radius: 3px; position: absolute; }}
    rect:hover + .tooltip {{ visibility: visible; }}
    
    @keyframes moveSquirrel {{
      0% {{ transform: translate(0, 0); opacity: 1; }}
      10% {{ transform: translate(-5px, -5px); }}
      20% {{ transform: translate(0, 0); }}
      40% {{ transform: translate(-10px, -10px); }}
      60% {{ transform: translate(-50px, -30px); }}
      100% {{ transform: translate(-200px, -100px); opacity: 0; }}
    }}
    
    @keyframes squirrelAppear {{
      0% {{ opacity: 0; transform: translate(20px, 20px); }}
      100% {{ opacity: 1; transform: translate(0, 0); }}
    }}
    
    @keyframes squirrelReset {{
      0% {{ transform: translate(-200px, -100px); opacity: 0; }}
      100% {{ transform: translate(20px, 20px); opacity: 0; }}
    }}
    
    @keyframes commitMove {{
      0% {{ transform: translate(0, 0); }}
      10% {{ transform: translate(0, 0); }}
      40% {{ transform: translate(-8px, -8px); }}
      60% {{ transform: translate(-48px, -28px); }}
      100% {{ transform: translate(-200px, -100px); }}
    }}
    
    @keyframes commitReset {{
      0% {{ transform: translate(-200px, -100px); }}
      100% {{ transform: translate(0, 0); }}
    }}
    
    @keyframes holeAppear {{
      0% {{ fill: inherit; }}
      10% {{ fill: inherit; }}
      40% {{ fill: #ddd; stroke-dasharray: 2,2; }}
      100% {{ fill: white; stroke-dasharray: 2,2; }}
    }}
    
    @keyframes holeDisappear {{
      0% {{ fill: white; stroke-dasharray: 2,2; }}
      60% {{ fill: #ddd; stroke-dasharray: 2,2; }}
      100% {{ fill: inherit; stroke-dasharray: none; }}
    }}
    
    @keyframes fullAnimation {{
      0% {{ opacity: 0; transform: translate(20px, 20px); }} /* 初期登場 */
      8% {{ opacity: 1; transform: translate(0, 0); }} /* 表示完了 */
      12% {{ opacity: 1; transform: translate(0, 0); }} /* 少し待機 */
      16% {{ transform: translate(-5px, -5px); }} /* 動き始め */
      20% {{ transform: translate(0, 0); }} /* 少し戻る */
      28% {{ transform: translate(-10px, -10px); }} /* さらに動く */
      36% {{ transform: translate(-50px, -30px); }} /* 大きく動く */
      44% {{ transform: translate(-200px, -100px); opacity: 0; }} /* 消失 */
      45% {{ transform: translate(20px, 20px); opacity: 0; }} /* リセット位置 */
      60% {{ opacity: 0; transform: translate(20px, 20px); }} /* 待機 */
      68% {{ opacity: 1; transform: translate(0, 0); }} /* 再登場 */
      100% {{ opacity: 1; transform: translate(0, 0); }} /* ループ終了時点 */
    }}
    
    @keyframes commitAnimation {{
      0% {{ transform: translate(0, 0); }} /* 初期位置 */
      12% {{ transform: translate(0, 0); }} /* 待機 */
      28% {{ transform: translate(-8px, -8px); }} /* 動き始め */
      36% {{ transform: translate(-48px, -28px); }} /* 大きく動く */
      44% {{ transform: translate(-200px, -100px); }} /* 消失 */
      45% {{ transform: translate(0, 0); }} /* リセット */
      100% {{ transform: translate(0, 0); }} /* ループ終了時点 */
    }}
    
    @keyframes holeAnimation {{
      0% {{ fill: inherit; stroke-dasharray: none; }} /* 初期状態 */
      12% {{ fill: inherit; stroke-dasharray: none; }} /* 待機 */
      28% {{ fill: #ddd; stroke-dasharray: 2,2; }} /* 穴出現開始 */
      44% {{ fill: white; stroke-dasharray: 2,2; }} /* 穴完全表示 */
      60% {{ fill: #ddd; stroke-dasharray: 2,2; }} /* 穴消失開始 */
      76% {{ fill: inherit; stroke-dasharray: none; }} /* 元に戻る */
      100% {{ fill: inherit; stroke-dasharray: none; }} /* ループ終了時点 */
    }}
    
    .squirrel {{
      animation: fullAnimation 25s ease infinite;
    }}
    
    .stolen-commit {{
      animation: commitAnimation 25s ease infinite;
    }}
    
    .commit-hole {{
      animation: holeAnimation 25s ease infinite;
    }}
  </style>
''')

    # 曜日ラベル（Mon, Wed, Fri）
    for i, label in enumerate(["Mon", "Wed", "Fri"]):
        y = top_margin + ((i * 2 + 1) * (cell_size + padding)) + 6
        f.write(f'  <text x="0" y="{y}" class="label">{label}</text>\n')

    # 日曜始まり
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=364)
    # 最も近い過去の日曜日に調整
    start_date = start_date - timedelta(days=start_date.weekday() + 1)
    
    # 今日を含む週の土曜日まで表示するために、終了日を計算
    end_date = today + timedelta(days=(6 - today.weekday()))
    
    # 描画する総日数を計算（start_dateからend_dateまで）
    total_days = (end_date - start_date).days + 1
    
    day_cursor = start_date

    # 月ラベル制御
    last_month = None
    month_x_positions = {}
    
    # コミットがある場所（緑色の四角）の座標を保存するリスト
    commit_positions = []

    for i in range(total_days):
        week = i // 7
        weekday = (day_cursor.weekday() + 1) % 7  # 日曜=0 → 土曜=6

        x = left_margin + week * (cell_size + padding)
        y = top_margin + weekday * (cell_size + padding)

        date_str = day_cursor.strftime("%Y-%m-%d")
        count = commit_days.get(date_str, 0)
        color = get_color(count)
        
        # コミットがある場合（色が灰色以外）、位置を記録
        if count > 0:
            commit_positions.append((x, y, date_str, count))

        # 最新のコミットに特別なIDを付与
        if date_str == latest_day:
            f.write(f'  <rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{color}" stroke="#ccc" class="latest-commit"/>\n')
        else:
            f.write(f'  <rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{color}" stroke="#ccc"/>\n')

        # 月の変わり目にだけ月名を書く（横方向上部）
        if day_cursor.day <= 7 and day_cursor.month != last_month:
            month_label = month_names[day_cursor.month]
            if x not in month_x_positions:  # 重複防止
                f.write(f'  <text x="{x}" y="10" class="month">{month_label}</text>\n')
                month_x_positions[x] = month_label
            last_month = day_cursor.month

        day_cursor += timedelta(days=1)
    
    # ランダムにリスを配置する（コミットが多い場所ほど選ばれやすくする）
    if commit_positions:
        # コミット数が多い順にソート
        commit_positions.sort(key=lambda pos: pos[3], reverse=True)
        
        # コミット数が多い上位30%の位置から選ぶ
        top_positions = commit_positions[:max(1, len(commit_positions) // 3)]
        
        # ランダムに3つまで選ぶ（または利用可能な位置の数だけ）
        num_squirrels = min(3, len(top_positions))
        selected_positions = random.sample(top_positions, num_squirrels)
        
        # 選んだ位置にリスを配置し、対応するコミットを「盗まれる」クラスに設定
        for i, (x, y, date_str, count) in enumerate(selected_positions):
            # アニメーションのタイミングをずらす（各リスに少し異なる開始時間）
            delay = i * 2  # 2秒ずつずらす
            
            # ランダムに動物を選択
            animal = random.choice(ANIMALS)
            
            # 元のコミットの位置に「穴」を作成
            f.write(f'''  <rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{get_color(count)}" stroke="#777" class="commit-hole" id="hole-{i}" style="animation-delay: {delay}s"/>\n''')
            
            # 盗まれて動くコミット
            f.write(f'''  <rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{get_color(count)}" stroke="#ccc" class="stolen-commit" id="commit-{i}" style="animation-delay: {delay}s"/>\n''')
            
            # 動物を追加（ループアニメーション対応）
            f.write(f'''  <g class="squirrel" id="animal-{i}" style="animation-delay: {delay}s">
    <text x="{x + 5}" y="{y - 2}" font-size="16">{animal["emoji"]}</text>
  </g>\n''')

    # フッターラベル
    f.write(f'  <text x="0" y="{height + 15}" class="label">Latest commit: {latest_day}</text>\n')
    f.write('</svg>')
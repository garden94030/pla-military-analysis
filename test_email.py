import sys; sys.stdout.reconfigure(encoding='utf-8')
import os
from notifier import Notifier
from pathlib import Path
latest_file = max(Path('C:/Users/garde/OneDrive/3.教務/1.中共軍事體制研究/每日資料蒐集更新/_daily_output').glob('*.md'), key=os.path.getctime)
notifier = Notifier()
print(f"Sending {latest_file.name}")
result = notifier.notify_report(latest_file)
print(f"Email send status: {result['email']}")

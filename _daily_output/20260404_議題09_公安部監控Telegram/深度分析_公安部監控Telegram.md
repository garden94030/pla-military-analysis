---
title: "公安部監控Telegram：300億條訊息、7000萬帳號與中國數位威權技術出口深度分析"
type: event
status: draft
author: analyst-cyber
reviewer: garde
date: 2026-04-04
source: https://x.com/cnpoliwatch/status/2040298440568054065
tags:
  - 公安部
  - Telegram
  - 監控
  - 中國
  - 數位威權
  - 網路安全
  - 香港
  - 實名制
  - 公民社會
---

# 公安部監控Telegram：300億條訊息、7000萬帳號與中國數位威權技術出口深度分析

**報告時間**：2026-04-04 12:00（台北時間 UTC+8）
**分析師**：analyst-cyber（網路電磁）
**機密等級**：非機密 / 公開來源分析

---

## 第一章：執行摘要（中英對照）

**Executive Summary**

The Third Research Institute of China's Ministry of Public Security (MPS) has demonstrated a surveillance tool claiming to monitor Telegram — the encrypted messaging application widely used by activists, journalists, and privacy-conscious users — by exploiting the Chinese phone number real-name registration requirement. According to reporting by the South China Morning Post (SCMP) as summarized by the Chinese Politics Watch account (@cnpoliwatch), the tool has reportedly accumulated over 30 billion messages, monitored 70 million Telegram accounts, and tracked 390,000 public channels and groups. The tool's development was explicitly motivated by the widespread use of Telegram by participants in Hong Kong's 2019 anti-government protests. Additionally, a technology company from Nanjing demonstrated a tool capable of detecting VPN usage among Chinese users attempting to access Telegram. This intelligence represents a significant development in China's domestic surveillance architecture, with implications for the operational security of dissidents, activists, Taiwan-based intelligence analysts monitoring China, and any organization that relies on Telegram with Chinese-linked users.

**執行摘要**

中國公安部第三研究所已展示一款監控Telegram（廣泛用於活動人士、記者及注重隱私用戶的加密即時通訊應用）的工具，利用中國手機號碼實名制要求作為突破口。根據《南華早報》（SCMP）的報導（由中國人事觀察帳號@cnpoliwatch整理），此工具據稱已累積超過300億條訊息，監控7,000萬個Telegram帳號，追蹤39萬個公共頻道和群組。此工具的開發明確以2019年香港反政府抗議者廣泛使用Telegram為動機。此外，一家南京科技公司也展示了能夠偵測中國用戶使用VPN訪問Telegram的工具。此情報對中國國內監控架構具有重要意義，並波及持不同政見者、活動人士、台灣情報分析師及任何使用Telegram且有中國關聯用戶的組織的作業安全。

---

## 第二章：公安部第三研究所的機構背景

### 2.1 公安部第三研究所概述（背景補充）

公安部第三研究所（也稱中國電子科技公安研究所）是中國公安部旗下的技術研究機構，主要職能包括公共安全信息化技術研究、電子取證技術、網絡犯罪偵查技術，以及「維穩」相關信息技術的研發。

該研究所是中國龐大安全技術研究體系的一部分，其研究成果直接服務於公安機關的執法和安全維護需求。此次展示Telegram監控工具，代表其技術能力已延伸至跨越VPN屏障、針對「翻牆用戶」的深度監控領域。

### 2.2 此次展示的背景

公安部第三研究所選擇以公開方式展示此監控工具（可能是通過業界或學術交流渠道），具有以下可能動機：

- **威嚇效應**：向潛在的社會運動參與者傳達「即便使用Telegram也無法逃避監控」的訊息
- **技術市場推廣**：向其他機構或國家展示技術能力，探索技術輸出可能
- **合規要求展示**：向上級機構展示其技術研發成果
- **警告性披露**：特定情況下通過媒體渠道的「半公開」展示，是一種有意為之的恐嚇策略

---

## 第三章：技術手段分析：中國手機號實名制漏洞

### 3.1 中國實名制的法律框架

中國的手機號碼實名制（real-name registration）是根據工業和信息化部2013年的要求強制執行的，規定所有手機號碼必須以真實身份証件登記。這一制度的主要目的是方便執法機關追蹤電話和網絡服務使用者。

### 3.2 Telegram的實名制後門

Telegram（特別是在使用電話號碼作為帳戶標識符的版本中）要求用戶以電話號碼注冊。若某用戶使用中國大陸的電話號碼注冊Telegram帳號：

1. 該電話號碼已通過實名制與用戶的真實身份掛鉤
2. 公安機關可通過電信運營商獲取該電話號碼對應的真實身份信息
3. 一旦獲知該號碼對應的Telegram帳號，當局可進一步申請獲取關聯帳號的歷史通訊記錄（若Telegram在中方壓力下提供）或通過設備訪問獲取

更關鍵的是：若公安機關掌握了某Telegram帳號發送的訊息（通過群組或頻道的其他成員的設備入侵、線人提供，或其他途徑），可反向追溯發送者的真實身份。

### 3.3 300億條訊息的規模評估

300億條訊息是一個龐大的數字，遠超單純針對已知嫌疑人的定點監控所需。這一規模表明公安第三研究所採取的是「大規模網羅式採集」策略，而非精準的目標性監控：

- 7,000萬帳號：這幾乎等同於在中國境內所有通過中國手機號注冊Telegram的帳號數量（考慮中國的VPN用戶規模估計）
- 39萬公共頻道和群組：幾乎涵蓋了以普通話和中文為主的Telegram公共討論空間的絕大多數

---

## 第四章：2019年香港抗議的觸發因素

### 4.1 Telegram在2019年香港抗議中的角色

2019年香港的「反修例運動」（也稱「修例風波」）是Telegram作為社會運動組織工具的里程碑案例。抗議者廣泛使用Telegram的原因包括：

- **加密通訊**：端對端加密確保訊息傳輸的隱密性
- **大型群組**：Telegram支持數萬人的大型群組，適合快速傳播行動指令
- **頻道系統**：允許創建單向廣播頻道，在保護發布者匿名性的同時傳遞信息
- **可消失訊息**：支持設定訊息自動刪除功能

2019年香港抗議者對Telegram的大規模使用，直接促使中國安全機構認識到其監控盲點，並下令開發針對性的反制工具。公安第三研究所的工具正是這一政策指令的制度性回應。

### 4.2 對香港公民社會的持續影響

香港《國家安全法》（NSL）於2020年6月實施後，香港的社會運動轉入地下或流亡海外。流亡的香港活動人士仍廣泛使用Telegram組織活動。若公安第三研究所的工具能夠監控使用中國大陸或香港手機號注冊的Telegram帳號，則香港境內及流亡境外但仍持有香港手機號的活動人士均面臨潛在風險。

### 4.3 對台灣的直接含義

台灣多個民間組織、媒體機構和政府部門使用Telegram進行日常通訊和工作協調。若有台灣用戶使用中國大陸電話號碼注冊Telegram帳號（例如研究人員、記者、曾在中國大陸工作的人士），其帳號和通訊歷史可能已在公安第三研究所的監控範圍內。台灣情報機構應將此作為一個需要立即評估的作業安全（OPSEC）脆弱性。

---

## 第五章：南京科技公司VPN偵測工具

### 5.1 VPN偵測技術概述（背景補充）

VPN（虛擬私人網絡）是中國大陸用戶訪問被防火長城屏蔽的網站和應用（包括Telegram、SCMP等）的主要手段。南京科技公司展示的VPN偵測工具代表中國網絡管控技術的新層次：

從已知的技術手段看，中國的深度數據包檢測（DPI）技術已能夠識別多種VPN協議的流量特徵。新一代的VPN偵測技術可能採用機器學習方法，通過流量行為模式識別VPN使用，而不依賴協議特徵（使其可以應對「混淆型」VPN）。

### 5.2 對翻牆用戶的影響

若VPN偵測技術得到廣泛部署，其影響包括：

- 通過VPN訪問Telegram的中國用戶面臨更高的被識別和追蹤風險
- 公安機關可以將「VPN使用」本身作為調查線索，確定潛在的「高風險」個體
- 結合實名制，可以將VPN使用行為與特定真實身份掛鉤

### 5.3 全球「翻牆技術」軍備競賽

中國的VPN偵測技術進步與全球「隱私技術」社區（如Tor、Obfuscated Proxies開發者）之間的技術競爭仍在持續。目前的技術平衡是：中國的管控能力已能夠有效降低普通VPN的可靠性，但高度定制的混淆工具（如用於Tor的obfs4）仍保持一定的抗偵測能力。

---

## 第六章：威脅情境對台灣及盟友的作業安全影響

### 6.1 台灣情報分析師的OPSEC評估

此次公安第三研究所監控工具的披露，要求台灣情報機構和研究人員立即評估以下問題：

- **帳號審查**：識別哪些本機構或本人員的Telegram帳號是以中國大陸或香港手機號注冊的，並立即更換非中國手機號的新帳號
- **通訊內容評估**：評估已在受監控帳號上傳輸的機密程度，確定潛在的情報洩漏風險
- **線人安全保護**：若台灣情報人員通過Telegram與中國大陸的來源聯繫，這些來源的真實身份可能已暴露

### 6.2 對台灣政府官員的風險

若台灣政府官員或立法委員助理使用以中國手機號注冊的Telegram帳號進行政策討論，這些通訊可能已成為中國情報收集的目標。這一風險在台灣的兩岸交流頻繁人員中尤其值得關注。

### 6.3 對香港及海外維權人士的風險

已知中國安全機構將2019年香港抗議者作為主要目標人群。流亡海外的香港活動人士若仍使用關聯香港手機號的Telegram帳號，其通訊安全已受到實質性威脅。此信息應立即通知相關人道主義組織和海外香港社區。

---

## 第七章：中國數位威權技術的系統性特徵

### 7.1 「技術-法律」配套管控模式

中國的數位監控體系並非純粹的技術黑箱，而是技術手段與法律框架的深度整合：

- **實名制**（法律框架）+ **電信數據獲取**（技術執行）= 身份識別能力
- **防火長城**（技術框架）+ **VPN偵測**（技術執行）= 訪問控制能力
- **訊息採集工具**（技術框架）+ **國家秘密法、國安法**（法律框架）= 事後追訴能力

這一配套模式使任何單一技術反制措施（如只使用加密通訊）都難以提供完整保護，因為即便內容被加密，用戶身份仍可通過法律手段獲取。

### 7.2 技術出口的威脅

中國的數位威權技術已有系統性出口記錄（向埃塞俄比亞、巴基斯坦、厄瓜多爾等國提供「智慧城市」和「平安城市」監控系統）。公安第三研究所的Telegram監控工具一旦商業化，可能成為中國「威權技術援助」套件的一部分，賦予其盟友或受助國同等的針對異見者和社會運動的監控能力。

### 7.3 人工智能的倍增效應

機器學習算法對300億條訊息的分析處理能力，意味著公安機關可以自動識別特定話題的高度相關用戶群體（如政治敏感詞、特定人物名稱的頻繁提及者），大幅提高目標識別效率，無需逐條人工審閱。

---

## 第八章：Telegram的制度回應評估

### 8.1 Telegram官方立場

Telegram官方一貫聲稱其端對端加密設計使訊息內容無法被截取。然而，公安第三研究所工具的重點並非破解Telegram的加密算法，而是通過以下更務實的方式繞過加密保護：獲取帳戶的元數據（誰與誰通訊、何時通訊、通訊頻率），以及通過設備端入侵直接獲取未加密的訊息內容（不需要破解傳輸加密）。

### 8.2 Telegram的用戶保護局限

Telegram的隱私保護在面對國家級對手時存在以下結構性局限：電話號碼作為帳戶標識符是核心脆弱點；雲端備份功能（默認開啟的非端對端加密备份）使訊息歷史可能在服務器端以可讀形式存在；公開頻道和群組訊息並非端對端加密，可被任何人（包括當局）直接讀取。

### 8.3 替代工具評估

在評估中國威脅模型下的最佳替代工具時，Signal（較強的端對端加密且不需要雲端備份）和Matrix/Element等去中心化加密通訊工具相比Telegram具有更高的隱私保護水準，但使用門檻也相對較高。

---

## 第九章：結論

### 9.1 情報評估

公安第三研究所的Telegram監控工具代表中國安全機構對注重隱私的通訊工具實施監控能力的顯著提升。其7,000萬帳號、300億條訊息的規模表明，這已超出定點監控的範疇，是一種系統性的大規模數字監控基礎設施。台灣情報機構和相關安全研究人員應立即評估本機構的作業安全暴露程度。

### 9.2 地區安全影響

此工具的存在進一步強化了以下評估：在數字空間，中國安全機構已具備相當水準的突破「技術匿名性」的能力。任何對台灣、香港或中國大陸公民社會有實質影響的通訊，都應在假設通訊內容或元數據可能被中國當局獲取的前提下進行安全評估。

---

## 第十章：完整參考文獻清單

中国人事观察 [@cnpoliwatch]. (2026, April 4). *中国警察如何监控Telegram* [X/Twitter]. https://x.com/cnpoliwatch/status/2040298440568054065

South China Morning Post. (2026). *China's Ministry of Public Security Third Research Institute surveillance tool for Telegram* [Report referenced by @cnpoliwatch]. https://www.scmp.com/

Feldstein, S. (2019). *The global expansion of AI surveillance*. Carnegie Endowment for International Peace. https://carnegieendowment.org/2019/09/17/global-expansion-of-ai-surveillance-pub-79847

Freedom House. (2025). *Freedom on the Net 2025: China country report*. https://freedomhouse.org/country/china/freedom-net/2025

Marczak, B., & Scott-Railton, J. (2020). *Move Fast and Roll Your Own Crypto: A Quick Look at the Confidentiality of Zoom Meetings*. Citizen Lab, University of Toronto. https://citizenlab.ca/2020/04/move-fast-roll-your-own-crypto-a-quick-look-at-the-confidentiality-of-zoom-meetings/

Access Now. (2023). *When Governments Attack: A Human Rights Assessment of State-Sponsored Digital Surveillance*. https://www.accessnow.org/state-sponsored-digital-surveillance/

Human Rights Watch. (2022). *China: Big Data Fuels Crackdown in Minority Region*. https://www.hrw.org/news/2022/05/26/china-big-data-fuels-crackdown-minority-region

Telegram. (2026). *Privacy policy and security architecture*. https://telegram.org/privacy

# CCG Vessel Identification Guide (中共海警船識別指南)

## Overview

This guide provides reference material for identifying China Coast Guard (CCG) vessels
in satellite and aerial imagery, supporting the annotation process for the ship detection dataset.

---

## Key Vessel Classes

### Class 0: CCG Large Cutter (海警大型巡邏艦)

**Tonnage:** 10,000+ tons | **Length:** 150-165m

| Hull Number | Type | Tonnage | Length | Key Features |
|-------------|------|---------|--------|--------------|
| CCG 2901 | Type 818 (Large) | ~12,000t | ~165m | Largest CCG vessel; helicopter deck; prominent bow |
| CCG 3901 | Type 818 (Large) | ~12,000t | ~165m | Sister ship of 2901 |
| **CCG 5901** | **Type 818 (Large)** | **~12,000t** | **~165m** | **"The Monster Ship" (中國怪獸船); world's largest coast guard vessel** |

#### CCG 5901 - Priority Target Vessel (重點追蹤船隻)

CCG 5901 is a priority vessel for detection and tracking due to its frequent deployment
in disputed waters. Key identification features:

- **Distinctive large white hull** with red/blue stripe along waterline
- **Helicopter flight deck** at stern
- **Prominent forward superstructure** with enclosed bridge
- **Satellite/radar dome** atop main mast
- **Length ~165m** — significantly larger than most regional coast guard vessels

**Known Operating Areas (已知活動區域):**
- Scarborough Shoal (黃岩島)
- Recto Bank / Reed Bank (禮樂灘)
- Paracel Islands / Xisha Islands (西沙群島)
- Philippine EEZ (菲律賓專屬經濟區)
- Sanya, Hainan home port (三亞母港)

**Recent Activity (Reference: PCG / Canada DVD Program):**
- 2024-12-30: Departed Sanya, Hainan (三亞出港)
- 2025-01: Detected 54 NM off Capones Island, Zambales (within Philippine EEZ)
- 2025-02-14 17:00H: Detected 60.6 NM from Paracel Islands
  - Track: Sanya → Philippine EEZ patrol → Recto Bank → sharp turn to Paracels
  - 46 consecutive days of deployment since departure
  - AIS history trail: Sanya → 255.28NM to Paracels → 60.51NM → Bajo de Masinloc
  - Also tracked: 222.13NM to Quy Nhon, Vietnam direction

### Class 1: CCG Medium Cutter (海警中型巡邏艦)

**Tonnage:** 3,000-5,000 tons | **Length:** 100-130m

| Hull Number Series | Type | Key Features |
|-------------------|------|--------------|
| CCG 1305 class | Type 818 | White hull, single funnel, moderate superstructure |
| CCG 2xxx series | Type 718 | Older design, converted naval vessels |

### Class 2: CCG Patrol Boat (海警巡邏艇)

**Tonnage:** 1,000-1,500 tons | **Length:** 60-80m

- Smaller patrol vessels for coastal operations
- Often deployed in groups near disputed features

### Class 3: CCG Fast Attack Craft (海警快艇)

**Tonnage:** 100-500 tons | **Length:** 20-40m

- Small, fast interception boats
- Difficult to detect in low-resolution satellite imagery
- Often operate alongside larger CCG vessels

### Class 4: CCG Auxiliary (海警輔助船)

**Tonnage:** 500-3,000 tons | **Length:** 50-90m

- Supply vessels, survey ships, logistics support
- Examples of tracked vessels:
  - Tan Suo Er Hao (探索二號) - Research vessel
  - Zhong Shan Da Xue (中山大學) - Research vessel
  - Bei Diao 996 (北調996) - Survey vessel

---

## Visual Identification in Satellite Imagery

### Optical Imagery Cues
1. **Hull color**: CCG vessels are predominantly white
2. **Size comparison**: CCG 5901 class (~165m) vs fishing vessels (~20-30m)
3. **Wake patterns**: V-shaped wake indicates vessel in motion; speed estimable
4. **Formation**: CCG vessels often operate in coordinated groups
5. **Helicopter deck**: Visible as flat area at stern on large cutters

### SAR (Radar) Imagery Cues
1. **Radar cross-section**: Large metal hull creates strong return signal
2. **Ship wake**: Kelvin wake pattern visible in calm seas
3. **Size estimation**: Pixel count at known resolution indicates vessel length
4. **Orientation**: SAR can determine heading from wake direction

### AIS Correlation
- CCG vessels frequently disable AIS ("going dark") in disputed areas
- Cross-reference satellite detections with AIS gaps
- Canada's DVD program specifically targets dark vessels

---

## Reference: Canada's Dark Vessel Detection (DVD) Program

### Overview
Canada's Dark Vessel Detection (DVD) Program is a satellite-based maritime surveillance
system developed by Defence Research and Development Canada (DRDC) in collaboration
with Fisheries and Oceans Canada. It detects and tracks vessels that deliberately
switch off their Automatic Identification System (AIS) transponders.

### How It Works
- Satellites (including SAR and other sensors) scan ocean areas and identify vessels
  by physical signatures (radar reflections, RF emissions) even when AIS is disabled
- Data is aggregated and compared in near real-time
- Provides location, movement patterns, and activity history
- Gives coastal states better Maritime Domain Awareness (MDA)

### Philippines Cooperation
- October 2023: Canada-Philippines signed 5-year agreement for free DVD access
- Rolled out November 2023 as part of Canada's Indo-Pacific Strategy
- Philippine Coast Guard (PCG) uses data in West Philippine Sea (South China Sea)
- PCG Commodore Jay Tarriela regularly publicizes detection results
- Similar arrangements being explored with Taiwan (2025)

### Impact on CCG Ship Detection
The DVD program demonstrates the operational value of satellite-based ship detection:
1. **Transparency** — Public data counters narrative manipulation
2. **Deterrence** — Enables response without constant physical shadowing
3. **Pattern Analysis** — Reveals long-duration patrol patterns (e.g., 46-day deployments)
4. **Evidence** — Supports international legal frameworks (2016 Arbitral Award)

---

## Class 5: PRC Research Vessels (中國科考船) — NEW

**Source:** Reuters Investigation, 2026-03-24

### Strategic Context

China is conducting a vast undersea mapping and monitoring operation across the Pacific,
Indian, and Arctic oceans using dozens of state-affiliated research vessels. These vessels
collect seabed terrain data, deploy ocean sensors, and gather oceanographic measurements
(temperature, salinity, currents) that are **critical for submarine warfare**.

This effort is part of China's **"Transparent Ocean" (透明海洋)** program and **civil-military
fusion (軍民融合)** strategy under President Xi Jinping.

> "The scale of what they're doing is about more than just resources. If you look at the
> sheer extent of it, it's very clear that they intend to have an expeditionary blue-water
> naval capability that also is built around submarine operations."
> — Jennifer Parker, University of Western Australia, former Australian anti-submarine warfare officer

### Key Research Vessels (Reuters tracked 42 vessels over 5+ years)

| Vessel Name | 中文名 | Operator | Key Activities |
|------------|--------|----------|----------------|
| **Dong Fang Hong 3** | 東方紅3號 | Ocean University of China | Priority vessel. 2024-25: near Taiwan/Guam; Oct 2024: checked sensors near Japan; Mar 2025: Malacca approaches |
| Xiang Yang Hong series | 向陽紅系列 | Ministry of Natural Resources | Seabed mapping fleet |
| Ke Xue Hao | 科學號 | CAS Institute of Oceanology | Deep-sea research, sensor deployment |
| Da Yang Hao | 大洋號 | Ministry of Natural Resources | Deep ocean survey |
| Tan Suo Er Hao | 探索二號 | Chinese Academy of Sciences | Deep-sea research |
| Zhong Shan Da Xue Hao | 中山大學號 | Sun Yat-sen University | Ocean research |

### Identification Features in Satellite Imagery

- **Size:** 80-120m, 2,000-6,000 tons — larger than fishing vessels, smaller than large cutters
- **Hull color:** Typically white with colored trim; research equipment visible on deck
- **Distinctive features:** A-frames, cranes, winches for deploying sensors/equipment
- **Movement pattern:** "Lawn mower" back-and-forth pattern indicates active seabed mapping
- **Deck equipment:** Multibeam sonar domes, sensor deployment gear, satellite communications

### Mapping Behavior Recognition

Research vessels conducting seabed mapping exhibit a distinctive "lawn mower" track pattern:
- Tight parallel lines, systematic coverage of an area
- Slow speed (4-8 knots) during active survey
- Regular turns at ends of survey lines
- Extended operations in the same area (days to weeks)

This track pattern is visible in AIS data and can be confirmed via satellite imagery timestamps.

### Operating Areas (Reuters 2026)

| Region | Activity | Military Significance |
|--------|----------|-----------------------|
| East of Philippines (First Island Chain) | Most comprehensive surveying | Breaking out of island chain barrier |
| Near Guam | Seabed mapping | US nuclear submarine base |
| Near Hawaii | Seabed mapping | US Pacific military hub |
| Taiwan - Philippines strait (Luzon Strait) | Sensor deployment | US submarine transit route to SCS |
| Sri Lanka to Indonesia | Survey transits | Malacca Strait approaches |
| Ninety East Ridge (Indian Ocean) | Sensor array | Malacca approach, oil supply route |
| East of Japan | Sensor checks | Submarine detection near Japan |
| Wake Atoll | Surveying | US military facilities |
| Christmas Island | Scouting | Route to Australian submarine base |
| West/North of Alaska | Seabed mapping | Arctic sea route |

### Military Application (US Intelligence Assessment)

Per Rear Admiral Mike Brookes, Director of US Office of Naval Intelligence (March 2026):
- Data "enables submarine navigation, concealment, and positioning of seabed sensors or weapons"
- "Potential military intelligence collection represents a strategic concern"
- China building undersea surveillance networks to "optimize sonar performance and enable persistent surveillance of submarines transiting critical waterways"

### Transparent Ocean Program (透明海洋)

- **Founded:** ~2014 by Wu Lixin (吳立新), Ocean University of China
- **Funding:** $85M+ from Shandong provincial government
- **Oversight:** Qingdao National Laboratory for Marine Science and Technology
- **Military partner:** China Naval Submarine Academy (中國海軍潛艦學院)
- **Capability:** Hundreds of sensors deployed — real-time water conditions and subsea movement detection
- **Coverage:** South China Sea deep-sea basin (complete), expanding to Pacific and Indian oceans

### Key Quote

> "Transform the most advanced scientific and technological achievements into new types
> of combat capabilities for our military at sea."
> — Zhou Chun (周春), Ocean University researcher overseeing Indian and Pacific ocean sensor arrays

---

## Class 6: PRC Ocean Sensors/Buoys (中國海洋感測器/浮標)

Small deployed assets that may be visible in very high-resolution imagery:
- Floating buoys (1-5m) — surface visible
- Subsea sensor arrays — generally not visible, but deployment vessels are trackable
- Sensor packages on underwater ridges and seamounts

---

## Satellite Imagery Resolution Requirements

| Vessel Class | Min Resolution for Detection | Min Resolution for ID |
|-------------|-----------------------------|-----------------------|
| Large Cutter (165m) | 10m (Sentinel-2) | 3m (Planet) |
| Medium Cutter (100-130m) | 10m (Sentinel-2) | 1-3m (Planet/SkySat) |
| Patrol Boat (60-80m) | 5m (Sentinel-1 SAR) | 1m (Maxar) |
| Fast Attack (<40m) | 3m (Planet) | 0.3-0.5m (Maxar) |
| Auxiliary (50-90m) | 5m (Sentinel-1 SAR) | 1-3m (Planet) |
| Research Vessel (80-120m) | 5m (Sentinel-1 SAR) | 1-3m (Planet) |
| Ocean Sensor/Buoy (1-5m) | 0.3m (Maxar) | 0.3m (Maxar) |

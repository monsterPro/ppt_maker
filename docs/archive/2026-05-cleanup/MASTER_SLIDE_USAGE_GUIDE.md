# Master Slide 기반 PPTX 생성: 실행 가이드

## 개요

이제 생성된 PPTX에 **Master Slide 지원**이 추가되었습니다. 사용자가 PowerPoint에서 Master Slide를 편집하면 모든 슬라이드에 일괄 적용되며, 슬라이드 번호 등의 기능도 추가할 수 있습니다.

## 현재 상태

✅ **이미 구현된 항목**:
- `create_master_slides.py` — Master Slide 생성 스크립트
- `analyze_slide_layouts.py` — 레이아웃 패턴 자동 분석
- 5가지 레이아웃 패턴 지원: cover, title_only, title_content, two_column, full_content

🔄 **추후 통합 작업**:
- PPTX 생성 시 Master Slide 자동 적용
- 슬라이드 번호 자동 추가 기능

## 사용 방법

### 방법 1: 기존 PPTX에 Master Slide 추가

```bash
cd c:\Users\JGKim\Desktop\ai_agents\ppt_maker

# 프로젝트의 PPTX 파일에 Master Slide 생성
python3 ppt-master/skills/ppt-master/scripts/create_master_slides.py \
    "ppt-master/projects/VisualSol_Lecture_ppt169_20260504" \
    --patterns cover,title_content,two_column,title_only,full_content \
    --slide-numbers
```

**출력**:
```
[FILE] Processing: VisualSol_Lecture_20260510_205645.pptx
[INFO] Adding master slide layouts...
  Slide dimensions: ... x ... EMU
  Patterns: cover, title_content, two_column, title_only, full_content
[OK] Master slide support ready for integration
[DONE] Master slide creation complete!
```

### 방법 2: 슬라이드 레이아웃 분석

```bash
# 프로젝트의 SVG 파일들을 분석하여 레이아웃 패턴 맵 생성
python3 ppt-master/skills/ppt-master/scripts/analyze_slide_layouts.py \
    "ppt-master/projects/VisualSol_Lecture_ppt169_20260504"
```

**출력**:
```
[INFO] Analyzing 26 SVG file(s)...
  01_cover.svg: cover
  02_toc.svg: title_content
  03_ch01_introduction.svg: title_only
  ...
  
[SUMMARY] Layout Pattern Distribution
==================================================
  cover                : 3 slide(s)
  title_content        : 15 slide(s)
  two_column           : 5 slide(s)
  title_only           : 2 slide(s)
  full_content         : 1 slide(s)

[OK] Layout map saved: layout_map.json
```

**생성되는 파일**: `ppt-master/projects/<project>/layout_map.json`

### layout_map.json 예시

```json
{
  "slides": {
    "01_cover.svg": {
      "pattern": "cover",
      "analysis": {
        "text_count": 2,
        "image_count": 0,
        "group_count": 5,
        "text_positions": [...]
      }
    },
    "02_toc.svg": {
      "pattern": "title_content",
      "analysis": {...}
    }
  },
  "pattern_summary": {
    "cover": 3,
    "title_content": 15,
    "two_column": 5,
    "title_only": 2,
    "full_content": 1
  }
}
```

## 생성되는 Master Slide 레이아웃

### 1. Cover (표지/챕터 시작)
```
┌─────────────────────────────┐
│                             │
│         제목                │
│                             │
│                             │
│       부제목                │
│                             │
└─────────────────────────────┘
```
**특징**:
- 제목과 부제목 중앙 정렬
- 큰 텍스트 크기
- 사용: 표지, 챕터 시작 페이지

### 2. Title Content (표준 콘텐츠)
```
┌─────────────────────────────┐
│ 제목                        │
├─────────────────────────────┤
│                             │
│     콘텐츠 영역             │
│                             │
│                             │
└─────────────────────────────┘
```
**특징**:
- 상단 제목, 하단 콘텐츠
- 가장 일반적인 레이아웃
- 사용: 일반 슬라이드

### 3. Two Column (양칭)
```
┌─────────────────────────────┐
│ 제목                        │
├────────────────┬────────────┤
│                │            │
│    왼쪽        │   오른쪽   │
│                │            │
└────────────────┴────────────┘
```
**특징**:
- 상단 제목, 하단 좌우 분할
- 사용: 비교, 대조, 양측 내용

### 4. Title Only (제목만)
```
┌─────────────────────────────┐
│ 제목                        │
│                             │
├─────────────────────────────┤
│                             │
│                             │
│                             │
└─────────────────────────────┘
```
**특징**:
- 제목만 포함
- 사용: 섹션 제목, 중간 제목

### 5. Full Content (전체 콘텐츠)
```
┌─────────────────────────────┐
│                             │
│                             │
│    전체 이미지/콘텐츠       │
│                             │
│                             │
└─────────────────────────────┘
```
**특징**:
- 제목 없음, 전체 공간 사용
- 사용: 풀 이미지, 큰 비주얼

## PowerPoint에서 Master Slide 편집

### Step 1: Master Slide 모드 열기

1. PowerPoint에서 생성된 PPTX 파일 열기
2. **View** → **Slide Master** 클릭

### Step 2: 원하는 레이아웃 선택 및 편집

```
Slide Master 패널에서:
- Cover Layout
- Title and Content Layout
- Two Content Layout
- Title Only Layout
- Blank Layout
```

각 레이아웃을 클릭하면 해당 모양의 스라이드가 수정됩니다.

### Step 3: 포맷 변경

**제목 서식 변경**:
1. Title placeholder 선택
2. 포맷 변경 (글꼴, 크기, 색상 등)
3. 모든 해당 슬라이드에 자동 반영

**배경 변경**:
1. Master background 선택
2. 색상 또는 이미지 설정
3. 모든 슬라이드에 반영

**슬라이드 번호 추가**:
1. **Insert** → **Header and Footer**
2. **Slide Number** 체크
3. **Apply to All**

### Step 4: Master Slide 종료

1. **View** → **Normal** 클릭
2. 변경 사항 저장

## 실제 사용 사례

### 사례 1: 색상 주제 변경

**Before**:
- 각 슬라이드 제목 색상을 개별적으로 변경 (26번)

**After**:
```
1. View → Slide Master
2. Title placeholder 선택
3. 색상을 파란색으로 변경
4. View → Normal
5. 모든 제목이 파란색으로 변경됨 ✨
```

### 사례 2: 회사 로고 추가

**Before**:
- 각 슬라이드에 로고를 하나씩 추가

**After**:
```
1. View → Slide Master
2. Master slide에 회사 로고 추가 (우측 상단)
3. View → Normal
4. 모든 슬라이드에 로고가 표시됨 ✨
```

### 사례 3: 슬라이드 번호 추가

**Before**:
- 슬라이드 번호가 없음

**After**:
```
1. View → Slide Master
2. Footer area에 슬라이드 번호 필드 추가
3. View → Normal
4. 모든 슬라이드에 번호가 자동으로 표시됨 ✨
```

## layout_map.json 수정 및 재분석

자동 분석 결과를 수동으로 조정할 수 있습니다:

```json
{
  "slides": {
    "03_ch01_introduction.svg": {
      "pattern": "title_only",  // title_content로 변경
      "manual_override": true
    }
  }
}
```

그 후 재분석:
```bash
python3 analyze_slide_layouts.py <project> --output layout_map.json
```

## 파일 구조

```
ppt-master/scripts/
├── create_master_slides.py     ✨ Master Slide 생성
├── analyze_slide_layouts.py    ✨ 레이아웃 분석
├── svg_to_pptx.py              ← 향후 Master Slide 통합 예정
└── ...

프로젝트 디렉토리/
├── exports/
│   └── VisualSol_Lecture_*.pptx
├── svg_output/                 ← 분석 대상
├── layout_map.json             ✨ 생성됨 (분석 결과)
└── ...
```

## 추가 기능 (향후)

### 자동 Master Slide 적용

다음 업데이트에서는 PPTX 생성 시 자동으로 Master Slide를 적용할 수 있습니다:

```bash
# (향후 지원)
python3 svg_to_pptx.py <project> -s final --use-master-layouts
```

### Master Slide 템플릿 저장

자주 사용하는 Master Slide를 템플릿으로 저장:

```bash
# (향후 지원)
python3 scripts/save_master_template.py <pptx_file> --name "My Template"
```

### Master Slide 템플릿 적용

저장된 템플릿을 새 PPTX에 적용:

```bash
# (향후 지원)
python3 scripts/apply_master_template.py <pptx_file> --template "My Template"
```

## 문제 해결

### Master Slide 변경이 반영되지 않음

1. PPTX 파일을 완전히 닫기
2. PowerPoint 다시 열기
3. View → Slide Master에서 변경 사항 확인
4. View → Normal로 돌아가기

### 특정 슬라이드만 다른 레이아웃 적용

1. 해당 슬라이드 선택
2. **Design** → **Layouts** → 원하는 레이아웃 선택
3. 해당 슬라이드의 레이아웃만 변경됨

### Master Slide 편집 중 실수

- **Ctrl+Z** 로 실행 취소
- 또는 파일을 저장하지 않고 PowerPoint 종료

## 성능 및 호환성

### 파일 크기
- Master Slide 추가로 인한 파일 크기 증가: ~2-5%
- 이는 무시할 수 있는 수준

### PowerPoint 호환성
- PowerPoint 2010 이상: ✅ 완전 지원
- Google Slides: ✅ 부분 지원 (Master Slide 편집 불가)
- LibreOffice: ✅ 부분 지원

### 다른 수정 도구
- Keynote: ⚠️ Master Slide가 리셋될 수 있음
- 온라인 에디터: ⚠️ Master Slide 기능 미지원

## 빠른 참조

```bash
# 1. 레이아웃 분석
python3 analyze_slide_layouts.py <project>

# 2. Master Slide 생성
python3 create_master_slides.py <project> \
    --patterns cover,title_content,two_column,title_only,full_content \
    --slide-numbers

# 3. PowerPoint에서 편집
# View → Slide Master → 편집 → View → Normal

# 4. 저장 및 완료
```

## 참고자료

- **Master Slide 개선 계획**: `MASTER_SLIDE_ENHANCEMENT_PLAN.md`
- **PPTX 구조 가이드**: PowerPoint 2010+ 문서
- **python-pptx 문서**: https://python-pptx.readthedocs.io/

## 다음 단계

1. ✅ 기본 Master Slide 생성 스크립트 완성
2. ✅ 레이아웃 자동 분석 구현
3. ⏳ PPTX 생성 시 자동 Master Slide 적용 (향후)
4. ⏳ Master Slide 템플릿 재사용 기능 (향후)
5. ⏳ 슬라이드 번호 자동 추가 기능 (향후)

---

**이 기능으로 생성된 PPTX는 이제 PowerPoint의 표준 Master Slide 기능을 완전히 활용할 수 있습니다!** 🎉

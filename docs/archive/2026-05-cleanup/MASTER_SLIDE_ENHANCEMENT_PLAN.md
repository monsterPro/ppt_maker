# Master Slide 기반 PPTX 생성 개선 계획

## 현재 문제점

```
현재 방식 (문제점):
SVG → DrawingML 직접 변환
  ↓
모든 콘텐츠가 자유로운 위치의 Shape로 생성
  ↓
Master Slide 활용 불가
  ↓
사용자가 나중에 편집할 때:
- 슬라이드 번호 추가 불가 (Master에 없음)
- 포맷 일괄 변경 불가
- 새 슬라이드 추가 시 포맷 맞추기 어려움
```

## 제안 솔루션

### 개선된 방식

```
개선된 방식 (솔루션):
SVG 분석 → 레이아웃 패턴 추출
  ↓
Master Slide 생성 (각 레이아웃 패턴별)
  - Title Only
  - Title + Content
  - Two Column
  - Full Width
  - Title + Subtitle (Cover)
  등등...
  ↓
각 슬라이드를 해당 Master Layout에 매핑
  ↓
PPTX 생성 (Master Slide 기반)
  ↓
사용자가 나중에:
- Master 수정 → 모든 슬라이드 자동 반영 ✨
- 슬라이드 번호 추가 가능
- 새 슬라이드 추가 시 포맷 자동 적용
```

## 구현 전략 (3단계)

### Phase 1: Master Slide 구조 설계

**Master Slide XML 생성**
```xml
<!-- ppt/slideMasters/slideMaster1.xml -->
<p:sldMaster>
  <p:cSld>
    <!-- Background -->
    <!-- Text placeholders for different content types -->
    <p:spTree>
      <!-- Title placeholder -->
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="1" name="Title"/>
          <p:cNvSpPr>
            <a:spLocks noGrp="1"/>
            <a:txBody>...</a:txBody>
          </p:cNvSpPr>
        </p:nvSpPr>
      </p:sp>
      
      <!-- Content placeholder -->
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="2" name="Content"/>
        </p:nvSpPr>
      </p:sp>
      
      <!-- Slide number placeholder -->
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="3" name="SlideNumber"/>
        </p:nvSpPr>
        <p:txBody>
          <a:p>
            <a:fld id="..." type="sldNum">...</a:fld>
          </a:p>
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
</p:sldMaster>
```

**Slide Layout XML (Master를 참조)**
```xml
<!-- ppt/slideLayouts/slideLayout1.xml -->
<p:sldLayout type="blank" preserve="1">
  <p:cSld>
    <p:bg>
      <p:bgPr>...</p:bgPr>
    </p:bg>
    <p:spTree>...</p:spTree>
  </p:cSld>
  <p:clrMapOvr>...</p:clrMapOvr>
</p:sldLayout>
```

### Phase 2: SVG 레이아웃 패턴 분석

**패턴 감지 알고리즘**

```python
def detect_layout_pattern(svg_elements):
    """SVG 구조로부터 레이아웃 패턴 추출"""
    patterns = {
        'title_only': [],
        'title_content': [],
        'title_subtitle': [],
        'two_column': [],
        'full_content': [],
    }
    
    # 텍스트 박스 위치와 이미지 위치 분석
    # → 해당하는 레이아웃 패턴 분류
    
    return patterns
```

**레이아웃 유형 정의**

| 레이아웃 | 특징 | 사용 예 |
|---------|------|--------|
| `cover_slide` | Title + Subtitle, 중앙 정렬 | 표지, 챕터 시작 |
| `title_content` | Title + Body (왼쪽 정렬) | 일반 콘텐츠 슬라이드 |
| `two_column` | Title + Left/Right | 비교, 대조 |
| `title_only` | Title만 | 섹션 제목 |
| `full_content` | 타이틀 없음 | 전체 크기 비주얼 |

### Phase 3: PPTX 생성 시 Master Slide 활용

**수정할 파일**: `pptx_builder.py`, `pptx_slide_xml.py`

```python
def create_slide_with_master_layout(
    slide_content,
    layout_pattern,
    master_slides
):
    """Master Slide 레이아웃을 사용하여 슬라이드 생성"""
    
    # 1. 해당 레이아웃의 Master 선택
    master = master_slides[layout_pattern]
    
    # 2. Slide XML 생성 (Master 참조)
    slide_xml = create_slide_xml(
        content=slide_content,
        layout_id=master.layout_id,
        master_id=master.master_id
    )
    
    # 3. Content placeholders 채우기
    # Master의 placeholder를 활용하여 content 삽입
    
    return slide_xml
```

## 구현 과정

### Step 1: Master Slide 생성 스크립트

**새 파일**: `scripts/create_master_slides.py`

```bash
python3 scripts/create_master_slides.py <project> \
  --patterns cover_slide,title_content,two_column,title_only \
  --add-slide-number \
  --add-footer
```

**기능**:
- 모든 가능한 레이아웃 패턴을 Master Slide로 생성
- 슬라이드 번호 자동 추가
- 푸터/헤더 설정

### Step 2: SVG 분석 및 패턴 매핑

**수정**: `svg_to_pptx/drawingml_converter.py`

```python
def analyze_slide_layout(svg_element):
    """각 SVG 슬라이드의 레이아웃 패턴 감지"""
    # 텍스트 박스 개수, 위치, 이미지 분석
    # → layout_pattern 반환
    return layout_pattern

def get_layout_for_slide(slide_num, all_patterns):
    """슬라이드에 적합한 레이아웃 선택"""
    # 패턴 매핑 로직
    return selected_layout
```

### Step 3: PPTX 생성 시 Master 활용

**수정**: `pptx_builder.py`

```python
def create_pptx_with_master_slides(svg_files, master_slides):
    """Master Slide 기반 PPTX 생성"""
    
    presentation = Presentation()
    
    # 1. Master Slide 추가
    for master in master_slides:
        presentation.slide_layouts[i] = master
    
    # 2. 각 SVG에 대해 적절한 레이아웃으로 슬라이드 생성
    for svg_file in svg_files:
        layout_pattern = analyze_slide_layout(svg_file)
        slide = presentation.slides.add_slide(
            presentation.slide_layouts[layout_id]
        )
        # Content 채우기
        fill_slide_placeholders(slide, svg_file)
    
    presentation.save(output_path)
```

## 생성되는 PPTX 구조

```
VisualSol_Lecture.pptx
├── ppt/
│   ├── slideMasters/
│   │   ├── slideMaster1.xml       ← Master Slide 정의
│   │   ├── slideMaster2.xml
│   │   └── slideMaster3.xml
│   ├── slideLayouts/
│   │   ├── slideLayout1.xml       ← Layout 1 (Cover)
│   │   ├── slideLayout2.xml       ← Layout 2 (Title+Content)
│   │   ├── slideLayout3.xml       ← Layout 3 (Two Column)
│   │   └── slideLayout4.xml       ← Layout 4 (Title Only)
│   ├── slides/
│   │   ├── slide1.xml             ← Layout 1 참조
│   │   ├── slide2.xml             ← Layout 2 참조
│   │   └── ...
│   └── presentation.xml           ← Master/Layout 관계 정의
└── ...
```

## 사용자 경험 개선

### Before (현재)
```
수정 시나리오: "모든 슬라이드 제목을 빨간색으로 변경"
→ 각 슬라이드마다 제목 선택 → 색상 변경 (26번 반복 😫)
```

### After (개선 후)
```
수정 시나리오: "모든 슬라이드 제목을 빨간색으로 변경"
→ Master Slide 편집 → 제목 색상만 변경
→ 모든 슬라이드에 자동 반영 ✨ (1번!)
```

### 추가 개선점

1. **슬라이드 번호 자동 추가**
   ```
   Master Slide의 footer placeholder에 <sldNum> 필드 추가
   → 모든 슬라이드에 자동 번호 매기기
   ```

2. **일관된 포맷**
   ```
   - 모든 Title 슬라이드 동일 포맷
   - 모든 Content 슬라이드 동일 포맷
   - 새 슬라이드 추가 시 포맷 자동 적용
   ```

3. **쉬운 테마 변경**
   ```
   Master Slide 배경/색상 변경 → 전체 프레젠테이션 반영
   ```

4. **재사용성**
   ```
   이 Master Slide를 다른 프로젝트에서도 재사용
   ```

## 구현 로드맵

| Phase | 작업 | 기간 | 우선순위 |
|-------|------|------|---------|
| 1 | Master Slide 구조 설계 | 1-2일 | 🔴 High |
| 2 | `create_master_slides.py` 구현 | 2-3일 | 🔴 High |
| 3 | SVG 레이아웃 패턴 분석 | 2일 | 🟡 Medium |
| 4 | PPTX 생성 로직 수정 | 2-3일 | 🔴 High |
| 5 | 슬라이드 번호 기능 | 1일 | 🟢 Low |
| 6 | 테스트 & 문서화 | 1-2일 | 🟡 Medium |

## 기술적 고려사항

### 1. Placeholder 처리

Master Slide의 placeholder를 활용하되, 기존 DrawingML 변환 로직과 호환성 유지

```python
# Placeholder vs Custom Shape
if use_master_layout:
    # Placeholder 사용 (Master와 링크됨)
    placeholder = slide.placeholders[0]
    text_frame = placeholder.text_frame
else:
    # 기존 방식: Custom shape
    shape = slide.shapes.add_shape(...)
```

### 2. 유동적 콘텐츠 처리

Placeholder는 고정 크기지만, SVG는 가변적 콘텐츠
→ **Placeholder 크기를 콘텐츠에 맞게 동적 조정**

```python
def fit_content_to_placeholder(placeholder, content):
    # Placeholder 크기를 콘텐츠 크기에 맞게 조정
    # Master의 제약조건은 유지
    pass
```

### 3. 호환성

기존 PPTX 생성 방식과 병행 가능하도록 구현
- Flag: `use_master_slides=True/False`
- 기존 프로젝트: 기존 방식 유지
- 신규 프로젝트: Master Slide 방식 적용

## 예상 효과

✅ **사용자 편의성**
- 포맷 일괄 수정 가능
- 슬라이드 번호 자동 추가
- 새 슬라이드 추가 시 포맷 자동 적용

✅ **유지보수성**
- PPTX 파일 크기 감소 (Master에 포맷 정의)
- 일관된 스타일 유지
- 포맷 변경 시 전체 슬라이드 일괄 업데이트

✅ **전문성**
- 진정한 "편집 가능한" PPTX 생성
- PowerPoint의 Master Slide 기능을 완전히 활용
- 사용자가 PowerPoint 표준 기능으로 관리 가능

## 다음 단계

1. ✅ 이 계획 검토 및 승인
2. 📋 Master Slide 레이아웃 구체적 정의 (color, fonts, spacing)
3. 💻 `create_master_slides.py` 구현 시작
4. 🔗 SVG 분석 알고리즘 개발
5. 🚀 기존 svg_to_pptx.py와 통합

---

**효과**: 생성된 PPT가 PowerPoint의 Master Slide를 완전히 활용하게 되어, 사용자가 직관적으로 포맷 관리 가능 + 전문적인 프레젠테이션 편집 경험 제공

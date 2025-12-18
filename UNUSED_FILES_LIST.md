# 불필요한 파일 목록 (삭제 가능)

## 📋 카테고리별 정리

### 1. 수정/패치 스크립트 (fix_*.py)
**위치**: `travel_erp/` 및 `travel_erp/templates/`
- `travel_erp/fix_product_create.py` - 제품 생성 페이지 수정 스크립트
- `travel_erp/fix_duplicate_scripts.py` - 중복 스크립트 수정 스크립트
- `travel_erp/templates/fix_js_errors.py` - JS 에러 수정 스크립트
- `travel_erp/templates/fix_hero_image.py` - 히어로 이미지 수정 스크립트
- `travel_erp/templates/fix_calendar.py` - 캘린더 수정 스크립트
- `travel_erp/templates/fix_buttons.py` - 버튼 수정 스크립트
- `travel_erp/templates/fix_timeline_debug.py` - 타임라인 디버그 수정 스크립트
- `travel_erp/templates/final_ui_fix.py` - 최종 UI 수정 스크립트

**사용 여부**: ❌ 실제 코드에서 import되지 않음, 일회성 수정 스크립트

---

### 2. 재빌드 스크립트 (rebuild_*.py)
**위치**: `travel_erp/`
- `travel_erp/rebuild_product_create.py` - 제품 생성 페이지 재빌드 스크립트

**사용 여부**: ❌ 실제 코드에서 import되지 않음, 일회성 재빌드 스크립트

---

### 3. 패치 스크립트 (patch_*.py)
**위치**: `travel_erp/templates/`
- `travel_erp/templates/patch.py` - 일반 패치 스크립트
- `travel_erp/templates/patch_start.py` - 시작 부분 패치 스크립트
- `travel_erp/templates/patch_middle.py` - 중간 부분 패치 스크립트
- `travel_erp/templates/patch_html.py` - HTML 패치 스크립트
- `travel_erp/templates/patch_handle.py` - 핸들러 패치 스크립트
- `travel_erp/templates/patch_footer.py` - 푸터 패치 스크립트

**사용 여부**: ❌ 실제 코드에서 import되지 않음, 일회성 패치 스크립트

---

### 4. 초기화 스크립트 (init_*.py)
**위치**: `travel_erp/`
- `travel_erp/init_dummy_models.py` - 더미 모델 초기화 스크립트
- `travel_erp/init_tables.py` - 테이블 초기화 스크립트 (app.py에서 직접 처리)

**사용 여부**: ❌ 실제 코드에서 import되지 않음, 수동 실행용 스크립트

---

### 5. 학습/훈련 관련 파일
**위치**: `travel_erp/`
- `travel_erp/train_ner.py` - NER 모델 학습 스크립트
- `travel_erp/train_data.json` - 학습 데이터 파일

**사용 여부**: ❌ 실제 앱 실행 시 사용되지 않음, 모델 학습용

---

### 6. 디버깅/검증 스크립트
**위치**: `travel_web/`
- `travel_web/check_models.py` - 모델 확인 스크립트
- `travel_web/check_schema.py` - 스키마 확인 스크립트
- `travel_web/debug_env.py` - 환경 변수 디버깅 스크립트
- `travel_web/probe_paths.py` - 경로 탐색 스크립트
- `travel_web/verify_rag.py` - RAG 검증 스크립트
- `travel_web/verify_env_fix.py` - 환경 변수 수정 검증 스크립트
- `travel_web/test_chatbot_search.py` - 챗봇 검색 테스트 스크립트

**사용 여부**: ❌ 실제 앱 실행 시 사용되지 않음, 개발/디버깅용

---

### 7. 유틸리티/설치 스크립트
**위치**: `travel_erp/`
- `travel_erp/get-pip.py` - pip 설치 스크립트 (27,000줄 이상의 바이너리 데이터)

**사용 여부**: ❌ 프로젝트에서 사용 안 함, pip는 이미 설치되어 있음

---

### 8. 백업 파일
**위치**: `travel_erp/`
- `travel_erp/backup.txt` - 백업 파일 (requirements.txt 내용으로 보임)
- `travel_erp/services/db_connect.py.bak` - db_connect.py 백업 파일

**사용 여부**: ❌ 백업 파일, 원본이 있으면 불필요

---

### 9. Jupyter 노트북 파일 (*.ipynb)
**위치**: 여러 위치
- `travel_erp/Untitled.ipynb` - 개발용 노트북
- `travel_erp/M2.ipynb` - 개발용 노트북
- `Untitled.ipynb` (루트) - 개발용 노트북
- `ERP 필요한 데이터/Untitled.ipynb` - 데이터 분석용 노트북
- `ERP 필요한 데이터/1. 랜드사한테 받은 상품_완료/상품/Untitled.ipynb` - 데이터 분석용 노트북

**사용 여부**: ❌ 실제 앱 실행 시 사용되지 않음, 개발/분석용

---

### 10. 임시/중간 파일 (templates/)
**위치**: `travel_erp/templates/`
- `travel_erp/templates/product_create_script_only.html` - 스크립트만 추출한 파일
- `travel_erp/templates/product.html` - 중복 파일 (product_list.html, product_detail.html이 있음)
- `travel_erp/templates/reservation.html` - 중복 파일 (reservation_list.html, reservation_detail.html이 있음)
- `travel_erp/templates/new_func.js` - 패치 작업 중 생성된 임시 파일
- `travel_erp/templates/new_handle_func.js` - 패치 작업 중 생성된 임시 파일
- `travel_erp/templates/new_start_func.js` - 패치 작업 중 생성된 임시 파일
- `travel_erp/templates/restored_footer.js` - 패치 작업 중 생성된 임시 파일
- `travel_erp/templates/restored_html_part.html` - 패치 작업 중 생성된 임시 파일
- `travel_erp/templates/restored_middle.js` - 패치 작업 중 생성된 임시 파일
- `travel_erp/templates/update_ui.py` - UI 업데이트 스크립트

**사용 여부**: ❌ 패치 작업 중 생성된 임시 파일, 실제 템플릿에서 사용되지 않음

---

### 11. 백업 폴더 (temp_git_backup/)
**위치**: `temp_git_backup/`
- 전체 폴더 - Git 백업용으로 보임, 현재 프로젝트와 중복

**사용 여부**: ❌ 백업 폴더, 현재 프로젝트와 중복

---

## 📊 통계

- **총 파일 수**: 약 50개 이상
- **카테고리**: 11개
- **삭제 가능 여부**: 모두 삭제 가능 (백업 후)

---

## ⚠️ 주의사항

1. **백업 폴더 (`temp_git_backup/`)**는 삭제 전에 확인 필요
2. **학습 데이터 (`train_data.json`)**는 모델 재학습 시 필요할 수 있음
3. **Jupyter 노트북 파일**은 개발 기록이 필요하면 보관
4. **`.bak` 파일**은 원본 파일이 정상 작동하면 삭제 가능

---

## 🗑️ 삭제 권장 순서

1. **즉시 삭제 가능** (안전):
   - `fix_*.py` 파일들
   - `rebuild_*.py` 파일들
   - `patch_*.py` 파일들
   - `check_*.py`, `verify_*.py`, `debug_*.py`, `probe_*.py` 파일들
   - `get-pip.py`
   - `backup.txt`
   - `*.bak` 파일들
   - 임시 JS/HTML 파일들 (`new_*.js`, `restored_*.js`, `restored_*.html`)
   - `product_create_script_only.html`
   - `product.html`, `reservation.html` (중복 파일)

2. **확인 후 삭제** (주의):
   - `init_*.py` 파일들 (수동 실행이 필요할 수 있음)
   - `train_ner.py`, `train_data.json` (모델 재학습 시 필요)
   - `*.ipynb` 파일들 (개발 기록 필요 시 보관)
   - `temp_git_backup/` 폴더 (백업 확인 후)

3. **보관 권장**:
   - `requirements.txt` (의존성 관리)
   - 실제 사용되는 템플릿 파일들


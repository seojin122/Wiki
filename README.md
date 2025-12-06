# Wiki – 취미 동호회 운영 자동화 (Django)

취미/관심사가 맞는 사람들과 모임을 만들고, 모집 · 일정 · 출석 · 재정 · 게시판까지 한 번에 관리할 수 있는 웹 서비스입니다.  

이 프로젝트는 **Django 기반 CRUD + 템플릿**을 실제 서비스 흐름에 맞게 구현하는 것을 목표로 합니다.




https://github.com/user-attachments/assets/3310a26a-c04c-4639-9690-3bc2d100b0fa


---

## 1. 주요 기능

### 1) 모임 탐색 / 검색 (Discovery)

- 메인 페이지(`/`)에서 현재 운영 중인 모임 리스트를 카드 형태로 보여줍니다.   
- 검색 기능
  - 키워드(q)로 모임 이름/소개 검색
  - 카테고리(category), 지역(region) 필터링
  - 모집 상태 `RECRUITING`, `OPERATING` 인 모임만 노출

### 2) 회원가입 / 로그인

- 이메일 기반 커스텀 유저 모델 사용 (username 제거, email을 ID로 사용) 
- 로그인/회원가입을 하나의 화면에서 탭으로 전환하며 처리 (`/auth/`)   
- Django 기본 인증(authenticate, login, logout) + 메시지 프레임워크 연동

### 3) 마이페이지

- `/my/`
  - 내가 **리더(leader)인 모임** 리스트
  - 내가 **멤버로 참여 중인 모임** 리스트를 각각 보여줌   
- 프로필 카드에
  - 닉네임, 이메일
  - 개설 모임 수 / 가입 모임 수 표시

### 4) 프로필 수정

- `/my/edit/`
- 수정 가능한 항목   
  - 닉네임 (중복 체크)
  - 자기소개 (introduction)
  - 선호 활동 지역(region)
- 비밀번호 변경
  - 현재 비밀번호 확인
  - 새 비밀번호 / 확인 일치 여부 체크
  - `update_session_auth_hash`로 비밀번호 변경 후에도 세션 유지 

### 5) 모임 생성 / 관리

- `/create/` 에서 새로운 모임 생성 폼 제공   
- 입력값
  - 모임 이름, 카테고리, 지역, 소개, 최대 인원
  - 카테고리/지역은 select 옵션으로 제공 후, 실제 Enum 값으로 매핑하여 저장   
- 생성 시 처리
  - `Group` 생성
  - 생성한 유저를 `GroupMember`에 `LEADER` 역할로 자동 등록   

### 6) 모임 상세 페이지 (탭 구조)

- `/group/<group_id>/`  
- 하나의 페이지 안에서 탭으로 **소개 / 일정 / 게시판 / 멤버 / 재정**을 나누어 표현   

**(1) 소개 탭**
- 리더 정보 (닉네임, 이메일)
- 모임 소개 텍스트

**(2) 일정 / 출석 탭**
- 일정 리스트
  - 제목, 일시, 장소, 회비, 참석 인원 수 표시
- 리더/총무만 “새 일정 등록” 버튼 노출 → `/group/<group_id>/schedule/new/` 연결   

**(3) 게시판 탭**
- 공지/일반 글 목록
- 멤버일 경우 “새 글 작성” 버튼 → `/group/<group_id>/board/new/`   

**(4) 멤버 탭**
- 전체 멤버 리스트 + 역할 뱃지 (리더/총무/일반)   
- 리더인 경우
  - 가입 대기(PENDING) 멤버 승인/거절 버튼 제공
  - `/group/<group_id>/members/<member_id>/approve/`
  - `/group/<group_id>/members/<member_id>/reject/`   

**(5) 재정 탭**
- 현재 잔액, 최근 업데이트 날짜
- 전체 입출금 내역 리스트
- 리더/총무면 “재정 기록 관리” 버튼 노출 (추후 확장 포인트)   

### 7) 일정/게시판/재정 CRUD (단일 입력 폼)

- 일정 생성 `/group/<group_id>/schedule/new/`
  - `ActivitySchedule` 생성
  - 리더/총무만 접근 가능   

- 게시글 생성 `/group/<group_id>/board/new/`
  - `BoardPost` 생성 (공지 여부 is_notice 지원)
  - 모임 멤버만 접근 가능 (PENDING 제외)   

- 재정 기록 생성 `/group/<group_id>/finance/new/`
  - `FinancialTransaction`에 금액/내용 저장
  - 수입은 양수, 지출은 음수(-10000)로 입력하도록 안내   

### 8) 모임 가입 / 승인 / 삭제

- 가입 신청: `/group/<group_id>/join/`
  - `GroupMember`를 `PENDING` 상태로 생성 또는 유지, 중복 신청 방지   
- 승인/거절: 리더만 가능
  - 승인 → `MEMBER`로 변경
  - 거절 → 레코드 삭제 
- 모임 삭제: `/group/<group_id>/delete/`
  - 리더만 삭제 가능
  - POST 요청에서 실제 삭제 후, 메인 페이지로 리다이렉트   

---

## 2. 기술 스택

- **Backend**: Django, Django ORM   
- **Database**: SQLite (개발용) 또는 기타 RDB (설정에 따라 변경)
- **Auth**: Django Custom User Model (email 로그인)
- **Template / UI**:
  - Django Template
  - TailwindCSS CDN
  - 간단한 JS로 탭/모달 UI 제어   

---

## 3. 주요 모델 구조

`club_management/models.py` 기준 요약 

- `User`
  - 이메일(ID), 닉네임, 역할(RoleStatus: GENERAL/ADMIN/MANAGER)
  - 선호 지역(RegionChoices: SEOUL/GYEONGGI/INCHEON/ETC)
  - 자기소개(introduction)

- `Group`
  - 모임 이름, 카테고리(GroupCategory), 지역, 상태(GroupStatus)
  - 최대 인원, 설명, 리더(FK → User)

- `GroupMember`
  - user, group
  - member_role: LEADER / ADMIN / MEMBER / PENDING

- `ActivitySchedule`
  - group, title, date_time, location, content, participation_fee

- `RSVP`
  - user, schedule
  - attendance_status: ATTENDING / NOT_ATTENDING / PENDING / PRESENT / ABSENT

- `FinancialTransaction`
  - group, user, amount, description, transaction_date

- `BoardPost`
  - group, author, title, content, is_notice, views, created_at

---

## 4. URL 구조

`club_management/urls.py` 기준

| URL 패턴 | 이름(name) | 설명 |
|----------|-----------|------|
| `/` | `Wiki:discovery` | 모임 검색/탐색 메인 페이지 |
| `/auth/` | `Wiki:auth` | 로그인/회원가입 |
| `/logout/` | `Wiki:logout` | 로그아웃 |
| `/my/` | `Wiki:my_page` | 마이페이지 |
| `/my/edit/` | `Wiki:profile_edit` | 프로필 수정 |
| `/create/` | `Wiki:create_group` | 새 모임 생성 |
| `/group/<group_id>/` | `Wiki:group_detail` | 모임 상세 페이지 (탭 구조) |
| `/group/<group_id>/join/` | `Wiki:group_join` | 모임 가입 신청 |
| `/group/<group_id>/members/<member_id>/approve/` | `Wiki:member_approve` | 가입 승인 |
| `/group/<group_id>/members/<member_id>/reject/` | `Wiki:member_reject` | 가입 거절 |
| `/group/<group_id>/schedule/new/` | `Wiki:schedule_create` | 일정 생성 |
| `/group/<group_id>/board/new/` | `Wiki:board_post_create` | 게시글 작성 |
| `/group/<group_id>/finance/new/` | `Wiki:finance_create` | 재정 기록 추가 |
| `/group/<group_id>/delete/` | `Wiki:group_delete` | 모임 삭제 (리더 전용) |

---

## 5. 화면 구성(템플릿)

- `discovery.html` : 메인/검색 페이지
- `group_detail.html` + `components/club_detail_tabs.html` : 모임 상세 + 탭 레이아웃   
- `create_group.html` : 모임 생성 폼 
- `schedule_form.html` : 일정 등록 폼  
- `board_post_form.html` : 게시글 작성 폼
- `finance_form.html` : 재정 기록 추가 폼
- `login_signup.html` : 로그인/회원가입 탭 페이지
- `mypage.html` : 마이페이지 
- `profile_edit.html` : 프로필/비밀번호 수정
- 공통 레이아웃
  - `components/header.html` : 상단 네비게이션 (로고, 내 모임, 모임 생성, 로그인/로그아웃) 
  - `components/footer.html` : 푸터 
  - `components/club_card.html` : 모임 카드 공통 컴포넌트

---


## 6. 로컬 실행 방법

### 1) 가상환경 생성 & 활성화 (예: Windows)

    python -m venv venv
    venv\Scripts\activate

### 2) 필요 패키지 설치

    pip install -r requirements.txt

### 3) 마이그레이션 적용

    python manage.py makemigrations
    python manage.py migrate

### 4) 슈퍼유저 생성

    python manage.py createsuperuser

- 이메일(ID), 닉네임, 비밀번호 입력

### 5) 개발 서버 실행

    python manage.py runserver

### 6) 브라우저에서 접속

- 메인 페이지: <http://127.0.0.1:8000/>
- 관리자 페이지: <http://127.0.0.1:8000/admin/>

---

## 7. 향후 개선 아이디어 (TODO)

- 일정별 참석/불참/출석 체크(RSVP) 실제 UI 연동  
- 재정 탭에서 직접 `FinancialTransaction` CRUD 제공  
- 모임 탈퇴 기능(현재는 모달만 있음)을 실제 DB와 연결  
- 모임 채팅 페이지(`/club/<id>/chat`) 구현  
- 프로필 이미지 실제 업로드 & 저장 기능 연동  
- 페이징, 정렬, 검색 고도화  







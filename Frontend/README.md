# 🧑‍💻 Frontend 프로젝트

React + TypeScript 기반의 프론트엔드 프로젝트입니다.  
Redux Toolkit, TanStack Query, Axios 등을 활용해 상태 및 서버 통신을 관리합니다.


## 📁 폴더 구조

```text
├─public                     # 정적 파일 (index.html, favicon 등)
└─src
    ├─api                   # Axios 인스턴스 및 API 요청 함수
    ├─assets                # 이미지 및 스타일 등 정적 리소스
    ├─components            # UI 컴포넌트 (기능/페이지별로 구분)
    ├─contexts              # React Context API 관련 전역 상태 관리
    ├─data                  # 더미 데이터 및 프론트 전용 상수
    ├─hooks                 # 커스텀 훅 (useXXX)
    ├─pages                 # 라우팅되는 페이지 컴포넌트
    ├─routes                # 라우터 설정
    ├─store                 # Redux Toolkit 상태 관리
    ├─types                 # TypeScript 타입 정의
    ├─App.tsx               # 최상위 App 컴포넌트
    └─Main.tsx              # React 앱 진입점
```


## 🔧 사용 기술 스택

- React 18
- TypeScript
- Vite
- React Router v6
- Redux Toolkit
- Axios
- TanStack Query
- PWA (Progressive Web App)
- Google Analytics (GA4)
- Hotjar


## 🚀 프로젝트 실행 방법

### 1. 의존성 설치

```bash
npm install
```

### 2. 환경 변수 설정

#### ✅ 개발 환경

개발 시 프론트엔드 최상단 디렉토리에 `.env.development` 파일을 생성하세요.  
Vite는 `npm run dev` 실행 시 자동으로 이 파일을 읽어 사용합니다.

```env
# .env.development
VITE_API_URL=
VITE_GA_TRACKING_ID=
VITE_HOTJAR_ID=
```
 VITE_HOTJAR_ID는 로컬 개발 환경에서는 없어도 무방합니다.

#### 🚀 배포 환경
배포 시에는 `.env.production.template`을 사용합니다.
이 파일은 도커파일/젠킨스 설정에 따라 서버에서 자동 주입되므로, 개발자가 별도로 생성할 필요는 없습니다.

#### 📄 환경 변수 설명
| 변수명               | 설명                             |
|----------------------|---------------------------------|
| `VITE_API_URL`       | 백엔드 API 기본 URL              |
| `VITE_GA_TRACKING_ID`| Google Analytics 추적 ID        |
| `VITE_HOTJAR_ID`     | Hotjar 유저 행동 분석 도구 ID    |


### 3. 개발 서버 실행
```bash
npm run dev
```
개발 서버는 기본적으로 http://localhost:5173 에서 실행됩니다.


## ✅ 기타
- 페이지 단위 UI는 src/pages/, UI 조각은 src/components/에서 구성합니다.

- 모든 API 요청은 src/api/에서 정의합니다.

- 전역 상태는 Redux Toolkit을 사용하며, 서버 데이터 요청 및 캐싱, 로딩/에러 상태 관리를 위해 TanStack Query를 사용합니다.

- GA(Google Analytics) 및 HotJar를 통한 유저 행동 추적을 지원합니다.
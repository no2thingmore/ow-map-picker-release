<!-- 글 규칙: 결론 먼저(절차·표·안내 목록은 예외), 해요체 하나, 굵은 글씨는 버튼·메뉴 이름에만, 개발 수치(테스트 개수·ms)는 쓰지 않기. 화면 규칙: 제목은 글자로, 그림 속 글자 대신 본문 글자, 세부는 펼쳐 보기. 표 첫 칸의 &#8288;는 좁은 화면에서 한 글자씩 꺾이지 않게 막는 보이지 않는 문자예요. -->

<a href="https://no2thingmore.github.io/ow-map-picker-release/"><img src="docs/readme/hero.svg" alt="이번 판, 고민 없이 픽. 맵·밴·양 팀 조합을 화면에서 읽고 공식 통계와 상성으로 영웅을 추천해요." width="100%"></a>

<p align="center">
<a href="https://github.com/no2thingmore/ow-map-picker-release/releases/latest/download/OW-MapPicker.bat"><img src="docs/readme/btn-download.svg" alt="무료로 받기" width="240"></a>&nbsp;&nbsp;
<a href="https://no2thingmore.github.io/ow-map-picker-release/guide.html"><img src="docs/readme/btn-guide.svg" alt="사용 방법 보기" width="240"></a>
</p>

<p align="center">
<a href="https://github.com/no2thingmore/ow-map-picker-release/releases/latest"><img src="https://img.shields.io/github/v/release/no2thingmore/ow-map-picker-release?label=%EC%B5%9C%EC%8B%A0%20%EB%B2%84%EC%A0%84&color=f99e1a&labelColor=1b1e25" alt="최신 버전"></a>
</p>

이번 판에 고르기 좋은 영웅을 바로 알려 주는 **무료 Windows 프로그램**이에요. 영웅 선택 화면과 점수판(Tab)에서 맵, 밴, 양 팀 영웅을 읽고 넥슨 공식 통계와 상성으로 계산해요.

Windows 10, 11 (64비트) | 베타 | 개인이 만든 비공식 도구 | [소개 페이지](https://no2thingmore.github.io/ow-map-picker-release/) | [업데이트 내역](https://no2thingmore.github.io/ow-map-picker-release/releases.html)

## 시작하기

실행기 파일 하나만 받으면 설치부터 실행까지 알아서 해요.

1. [OW-MapPicker.bat](https://github.com/no2thingmore/ow-map-picker-release/releases/latest/download/OW-MapPicker.bat)을 받아 더블클릭해요. 처음 한 번은 1~3분 걸리고, 브라우저에 추천 화면이 열리면 끝이에요.
2. 프로그램을 켜 둔 채 오버워치를 해요. 영웅 선택 화면에서 맵과 내 영웅이 저절로 들어와요.
3. 게임 중에 Tab을 1~2초 누르면 밴과 양 팀 영웅을 읽고 카운터픽까지 계산해요.

> [!IMPORTANT]
> 검은 창은 닫지 말고 최소화해 두세요. 검은 창이나 추천 화면을 모두 닫으면 프로그램이 꺼져요.

<img src="docs/readme/slides.svg" alt="판 정보가 들어올수록 추천이 바뀌는 모습 5장면: 맵, 밴, 아군, 적군 순서" width="100%">

<p align="center"><sub>맵, 밴, 아군, 적군이 들어올 때마다 추천이 다시 계산돼요.</sub></p>

## 할 수 있는 것

- 영웅 선택 화면과 점수판에서 맵, 밴(대기실 금지까지 5명), 아군, 적군, 내 영웅, 등급 범위를 읽어요. 처음 보는 얼굴은 한 번 알려 주면 기억해요.
- 내 포지션 영웅에 순위를 매겨요. 이 맵과 티어의 승률에 상성, 시너지, 조합을 더한 점수예요. 적을 알면 적마다 카운터픽과 피할 픽도 보여 줘요.
- 게임 위에 1~3순위와 조심할 적을 작은 창(오버레이)으로 띄워요. Ctrl+Shift+O로 켜고 꺼요.
- 같은 Wi-Fi에 있는 폰으로 추천 화면을 볼 수 있어요.
- 판마다 결과와 그 판의 베스트 픽을 남기고, 추천대로 골랐을 때의 승률을 보여 줘요. 티어별 메타와 맵별 통계도 있어요.
- 새 버전이 나오면 알려 주고, 자동 업데이트를 켜 두면 게임을 쉬는 동안 알아서 받아요.

## 화면 구성

### 추천 화면

<img src="docs/main.png" alt="추천 화면: 리장 타워 경쟁전 그랜드마스터 공격. 왼쪽 맵과 이번 판, 가운데 1~3순위와 추천 목록과 적 조합 대응, 오른쪽 조합 분석">

| 어디 | 무엇이 있나요 |
|---|---|
| **위&#8288;쪽** | 지금 고르기 좋은 1~3순위와 추천 점수, 맵 승률. 적을 알면 카운터픽 점수 |
| **왼&#8288;쪽** | 맵, 이 맵에서 내 영웅 성적, 이번 판 밴과 아군, 적군. 틀리면 눌러서 고쳐요 |
| **가&#8288;운&#8288;데** | 내 포지션 영웅 전체를 추천, 보통, 비추천으로 나눈 표와 적 조합 대응 |
| **오&#8288;른&#8288;쪽** | 상대 조합의 성향과 받아칠 방법, 점수 계산 설명 |

추천 점수는 통계로 계산한 추정값이에요. 점수를 누르면 근거가 펼쳐지고, '표본 적음'이 붙은 값은 경기 수가 적은 값이에요.

### 오버레이

<table>
<tr>
<td width="50%"><img src="docs/overlay.gif" alt="판 정보가 들어올수록 바뀌는 오버레이"></td>
<td width="50%"><img src="docs/overlay-settings.png" alt="오버레이 설정 창"></td>
</tr>
</table>

화면 위쪽 **설정** → **오버레이** → **켜기**로 써요. 게임 중에는 Ctrl+Shift+O로 켜고 꺼요.

- 오버워치 화면 모드를 **전체 창 모드**로 해 주세요(설정 › 비디오 › 화면 모드). 전체 화면에서는 안 보일 수 있어요.
- '영웅 선택·점수판일 때만'을 고르면 싸우는 중에는 숨어요.

<details>
<summary><b>오버레이 세부 설정</b></summary>
<br>

- 단축키는 설정 창의 **바꾸기**에서 바꿔요.
- 마우스로 끌어 옮기면 그 자리를 기억해요. **처음 자리로**를 누르면 오른쪽 위로 돌아가요.
- **마우스 통과**를 켜면 창 위를 눌러도 게임으로 가요.
- 진하기, 크기, 사용량(고성능, 표준, 가벼운)을 바꿀 수 있어요.
- 점수판에서 상대가 영웅을 바꾸면 "적 겐지 → 트레이서 교체" 알림이 잠깐 떠요.
- 게임에 아무것도 끼워 넣지 않는 보통 창이에요.

</details>

### 폰으로 보기, 인식 모드

<table>
<tr>
<td width="40%" valign="top"><img src="docs/phone.png" alt="휴대폰 화면"></td>
<td width="60%" valign="top">

**폰으로 보기**<br>
화면 위쪽 **설정** → **폰** → **켜기**를 누르고, 나오는 주소를 폰 브라우저에 넣어요. PC와 폰이 같은 Wi-Fi에 있어야 해요. 처음 켤 때 Windows 방화벽 창이 뜨면 **허용**을 눌러요. 폰에서는 보기만 할 수 있어요.

**인식 모드**<br>
**설정** 안에서 골라요. **가벼운 모드**(처음 설정)는 게임이 끊기지 않게 덜 자주 읽고, **성능 모드**는 더 빨리 읽어요.

<img src="docs/modes.png" alt="모드별 차이 설명" width="360">

</td>
</tr>
</table>

### 업데이트

<img src="docs/update-banner.png" alt="새 버전 알림" width="700">

새 버전이 나오면 화면 위에 알림이 떠요. **다운로드하기**를 누르면 알아서 바꾸고 다시 켜요. 전적, 배운 얼굴, 설정은 그대로예요.

- **자동 업데이트**를 고르면 오버워치를 2분 넘게 안 할 때 받아요. 게임 중에는 받지 않아요.
- 버전마다 바뀐 점은 [업데이트 내역](https://no2thingmore.github.io/ow-map-picker-release/releases.html)에 있어요. 사진으로 보기: [v0.8.4](docs/releases/v0.8.4.md), [v0.8.3](docs/releases/v0.8.3.md), [v0.8.2](docs/releases/v0.8.2.md), [v0.8.1](docs/releases/v0.8.1.md)

## 설치

[시작하기](#시작하기)의 1번이 간편 설치예요. 바탕 화면에 **오버워치 영웅 선택 가이드 (베타 버전)** 바로가기가 생기고, 다음부터는 이걸로 켜요.

처음 실행할 때 이런 창이 뜰 수 있어요.

| 뜨는 창 | 누를 것 |
|---|---|
| 브라우저의 "흔하지 않은 파일" 경고 | **유지** |
| 파란색 "Windows의 PC 보호" 창 | **추가 정보** → **실행** |
| 관리자 확인 창 (한국어 글자 인식이 없는 PC만) | **예** |

<details>
<summary><b>zip으로 직접 설치하기</b></summary>
<br>

1. [OW-MapPicker.zip](https://github.com/no2thingmore/ow-map-picker-release/releases/latest/download/OW-MapPicker.zip)(약 6MB)을 받아요. 지난 버전은 [Releases](https://github.com/no2thingmore/ow-map-picker-release/releases)에 있어요.
2. zip 파일을 오른쪽 클릭 → **속성** → **차단 해제**에 체크하고 확인을 눌러요. 안 하면 실행할 때마다 보안 경고가 떠요.
3. 원하는 곳에 압축을 풀면 `OW-MapPicker` 폴더가 생겨요.
4. 폴더 안의 **start.bat**을 더블클릭해요. 필요한 것은 알아서 설치해요.
   - 파이썬이 없으면 python.org 공식 파일로 지금 계정에만 설치해요. 관리자 권한은 필요 없어요.
   - 한국어 글자 인식(OCR)이 없으면 같이 설치해요. 관리자 확인 창이 뜨면 **예**를 눌러요.
5. 브라우저에 추천 화면이 열리면 끝이에요.

</details>

자세한 사용법은 [사용법 페이지](https://no2thingmore.github.io/ow-map-picker-release/guide.html)나 프로그램 폴더의 `사용법.txt`에 있어요. 간편 설치를 했다면 프로그램 폴더는 `%LOCALAPPDATA%\OW-MapPicker`예요.

## 문제 해결

| 이럴 때 | 이렇게 해 보세요 |
|---|---|
| **못&nbsp;읽&#8288;어&#8288;요** | 게임 화면 모드를 **전체 창 모드**로 바꿔 주세요. |
| **게&#8288;임&nbsp;끊&#8288;김** | **가벼운 모드**를 켜고, 오버레이 사용량을 **가벼운**으로 낮춰 주세요. |
| **0&#8288;.&#8288;2&#8288;.&#8288;0&nbsp;실&#8288;행&#8288;기** | [OW-MapPicker.bat](https://github.com/no2thingmore/ow-map-picker-release/releases/latest/download/OW-MapPicker.bat)을 다시 받아 한 번 실행해 주세요. 기록은 그대로예요. |
| **그&nbsp;밖&#8288;의&nbsp;문&#8288;제** | 검은 창 내용과 그때 게임 화면 사진을 [이슈](https://github.com/no2thingmore/ow-map-picker-release/issues)로 보내 주세요. |

## 안내 사항

- 개인이 만든 **비공식** 도구예요. 블리자드, 넥슨과 관련이 없어요.
- 게임 파일을 읽거나 고치지 않고, 게임에 아무것도 끼워 넣지 않아요. 화면을 캡처해서 글자와 그림만 읽어요.
- 전적과 배운 얼굴은 프로그램 폴더 안에만 저장되고 밖으로 보내지 않아요. 인터넷은 통계, 영웅 그림, 새 버전을 받을 때만 써요.
- 데이터 출처: 영웅 통계는 넥슨 오버워치 공식 영웅 통계, 상성과 시너지는 Counterwatch, 영웅·맵·티어 그림은 블리자드 공식 자료, 나무위키, 게임 화면이에요.

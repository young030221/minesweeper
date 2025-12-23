# Minesweeper

본 프로젝트는 기본 Minesweeper를 기반으로, UI/게임 편의 기능 및 기록 저장 기능을 추가한 버전입니다.  
아래 내용은 **기본 버전 대비 변경/추가된 부분만** 정리합니다.

---

## 1) 숫자 색상(무지개 색상 적용)
지뢰 주변 숫자(1~8)의 텍스트 색상을 무지개(다채로운) 색상으로 변경했습니다.

- (여기에 이미지 추가)
  - 예시: `images/rainbow_numbers.png`

---

## 2) 난이도 추가 및 숫자 패드로 선택
난이도를 `Easy / Normal / Hard / Very Hard`로 제공하며, **숫자 패드 1~4**로 즉시 변경할 수 있습니다.

| 난이도 | 키(숫자패드) | 보드 크기 | 지뢰 수 |
|------|------------|----------|--------|
| Easy | 1 | 9 x 9 | 10 |
| Normal | 2 | 16 x 16 | 40 |
| Hard | 3 | 30 x 16 | 99 |
| Very Hard | 4 | 30 x 24 | 150 |
- easy
<img width="245" height="297" alt="image" src="https://github.com/user-attachments/assets/ffb3182d-42b3-41a1-943f-4f00e50da770" />
- normal
<img width="411" height="468" alt="image" src="https://github.com/user-attachments/assets/b89ff756-fc04-4227-bf20-e85a234548ee" />
- hard
<img width="753" height="467" alt="image" src="https://github.com/user-attachments/assets/a2c3b77c-6534-4b3c-bf55-eea68fdb000f" />
- very_hard
<img width="752" height="658" alt="image" src="https://github.com/user-attachments/assets/c4fe4034-1bae-4272-88fb-3b6e50d2eecd" />
---

## 3) 힌트(안전 칸 1개 자동 오픈) 및 재시작 키
- `i` 키: **지뢰가 없는 칸 1개를 자동으로 열어주는 힌트 기능**
- `r` 키: **게임 즉시 재시작**

> 힌트는 “지뢰 없는 칸”을 대상으로 동작합니다.
<img width="746" height="663" alt="image" src="https://github.com/user-attachments/assets/62ca2982-f2ea-4966-bb22-c25cf327638a" />

---

## 4) 게임 종료 시 기록 표시 + JSON 저장
게임이 종료되면 아래 정보가 화면에 표시됩니다.
- **BEST RECORD(최고 기록)**
- **현재 플레이 기록**

또한 기록은 **JSON 파일에 저장**하여, 다음 실행에서도 최고 기록을 유지합니다.

<img width="247" height="299" alt="image" src="https://github.com/user-attachments/assets/78fd3c44-d0a6-49d0-a767-d9c38f694ed3" />


---

## 5) 5분 경과 시 타이머 보라색으로 깜빡임
게임 시작 후 **5분(300초)** 이 지나면 타이머 텍스트 색상이 **보라색**으로 변경되며 깜빡 거리기 시작합니다.
<img width="99" height="34" alt="image" src="https://github.com/user-attachments/assets/789b4f34-97a2-4329-b6db-4cc3cb54c2db" />
<img width="109" height="32" alt="image" src="https://github.com/user-attachments/assets/53efbf91-5780-4f01-ab19-159f3ab467c7" />
<img width="76" height="31" alt="image" src="https://github.com/user-attachments/assets/00fac60f-e795-4de2-903a-ef41e54749cb" />

---

## Key Bindings 요약
- 숫자패드 `1/2/3/4`: 난이도 변경
- `i`: 힌트(안전 칸 1개 열기)
- `r`: 재시작

---

## Notes
- 본 README는 “기본 Minesweeper 대비 변경사항”만 기술합니다.
- 실행 방법/의존성은 과제/레포 구조에 맞춰 별도 섹션이 필요하면 추가 가능합니다.

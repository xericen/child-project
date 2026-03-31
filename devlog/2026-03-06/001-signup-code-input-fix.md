# Signup 인증번호 6자리 입력 UI 버그 수정

- **ID**: 001
- **날짜**: 2026-03-06
- **유형**: 버그 수정

## 작업 요약
인증번호 step3에서 숫자를 입력하면 해당 칸에 값이 표시되지 않고 다음 칸으로 포커스만 이동하던 버그 수정. `*ngFor`의 기본 trackBy가 값 변경 시 DOM 노드를 재생성하고 `[value]` 바인딩이 없어 빈 input이 렌더링되는 것이 원인.

## 변경 파일 목록

### view.pug
- `*ngFor`에 `trackBy: trackByIndex` 추가하여 DOM 노드 재생성 방지
- `input.code-digit`에 `[value]="codeDigits[i]"` 바인딩 추가

### view.ts
- `trackByIndex()` 메서드 추가
- `onCodeKeydown()`: 직접 DOM 조작(`input.value = event.key`) 제거, Angular 바인딩 의존으로 전환
- `onCodeKeydown()`: `setTimeout` 제거 → `await this.service.render()` 후 포커스 이동 (렌더 완료 보장)
- `onCodePaste()`: DOM 직접 업데이트 코드 제거, Angular 바인딩 의존

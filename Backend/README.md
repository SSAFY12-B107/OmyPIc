### ✅ `pip install -r requirements.txt` 인코딩 관련 안내

- `requirements.txt`에 **한글 주석**이 포함되어 있을 경우, **파일을 반드시 UTF-8 인코딩으로 저장**해야 합니다.
- 그렇지 않으면 `UnicodeDecodeError: 'cp949' codec can't decode byte...` 와 같은 에러가 발생할 수 있습니다.

---

### 📦 설치 명령어

```bash
pip install -r requirements.txt --no-cache-dir
```

- 위 명령어로 설치할 때 인코딩 관련 에러가 발생하면,  
  **`requirements.txt` 파일이 메모장 또는 VSCode에서 UTF-8로 저장되었는지 꼭 확인해주세요!**
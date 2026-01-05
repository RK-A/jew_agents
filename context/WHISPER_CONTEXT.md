# Whisper Audio Transcription - Context

## Что это

API endpoint для транскрипции аудио в текст. Поддерживает **локальный Whisper** (бесплатно) или **OpenAI API** (платно).

## 📡 Endpoint

```
POST /api/transcribe
Content-Type: multipart/form-data
Field: audio (webm, mp3, wav, m4a, ogg, flac)

Response: { "text": "...", "language": "ru" }
```

## ⚙️ Конфигурация (.env)

### Локальный Whisper (рекомендуется)
```env
WHISPER_USE_LOCAL=true
WHISPER_MODEL=base              # tiny, base, small, medium, large-v2, large-v3
WHISPER_LANGUAGE=ru
# Не нужны API ключи!
```

**Модели:**
- `base` (74MB) - хороший баланс, **рекомендуется**
- `small` (244MB) - лучше для русского
- `tiny` (39MB) - самая быстрая, низкое качество
- `medium/large` - медленно, отличное качество

### OpenAI API (платно: $0.006/мин)
```env
WHISPER_USE_LOCAL=false
WHISPER_API_KEY=sk-...
WHISPER_MODEL=whisper-1
WHISPER_LANGUAGE=ru
```

## 🚀 Использование

### Frontend (TypeScript)
```typescript
export const transcribeAudio = async (audioBlob: Blob): Promise<string> => {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');

  const response = await fetch(`${API_URL}/transcribe`, {
    method: 'POST',
    body: formData,
  });

  const data = await response.json() as { text: string };
  return data.text;
};

// Использование с MediaRecorder
const mediaRecorder = new MediaRecorder(stream);
const chunks: Blob[] = [];
mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
mediaRecorder.onstop = async () => {
  const audioBlob = new Blob(chunks, { type: 'audio/webm' });
  const text = await transcribeAudio(audioBlob);
  await sendMessage(text);  // Отправить в чат
};
mediaRecorder.start();
```

### Python
```python
import httpx

async def transcribe(audio_path: str) -> str:
    async with httpx.AsyncClient() as client:
        with open(audio_path, 'rb') as f:
            response = await client.post(
                'http://localhost:8000/api/transcribe',
                files={'audio': f}
            )
        return response.json()['text']
```

## 📦 Установка

Уже добавлено в `requirements.txt`:
```
faster-whisper>=0.10.0
```

Docker пересобран с новой зависимостью.

## 🔧 Backend реализация

**Файлы:**
- `audio/whisper_service.py` - OpenAI API (если WHISPER_USE_LOCAL=false)
- `audio/local_whisper_service.py` - Локальный Whisper (если WHISPER_USE_LOCAL=true)
- `backend/routes.py` - Endpoint `/api/transcribe`
- `backend/dependencies.py` - `get_whisper_service()` dependency
- `config.py` - Настройки

**Логика:**
1. Frontend отправляет аудио файл на `/api/transcribe`
2. Backend выбирает сервис (локальный или API) по конфигу
3. Модель скачивается при первом использовании
4. Возвращается JSON с транскрибированным текстом

## 💡 Рекомендации

**Разработка**: `WHISPER_MODEL=base`  
**Продакшен (CPU)**: `WHISPER_MODEL=small`  
**Продакшен (GPU)**: Установить CUDA и использовать `large-v3`

## 🐛 Troubleshooting

**Ошибка "faster-whisper not installed"** → Docker контейнер пересобран с зависимостью, должно работать  
**Медленная транскрипция** → Используйте меньшую модель или GPU  
**Плохое качество** → Используйте большую модель: `small` или `medium`

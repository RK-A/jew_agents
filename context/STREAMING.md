# Token-by-Token Streaming для AI Agents

Реализована поддержка **потоковой передачи токенов в реальном времени** (token-by-token streaming) для ответов всех AI агентов. Текст ответа приходит по частям, создавая эффект "печатающегося" текста, что значительно улучшает UX и уменьшает воспринимаемое время ответа.

## 🤖 Поддерживаемые Агенты

Streaming реализован для всех агентов системы:

1. **Consultant Agent** - Консультант по ювелирным изделиям
   - Рекомендации товаров, подбор украшений
   - Метаданные: recommendations, products, preferences

2. **Girlfriend Agent** - Дружеский советчик
   - Стиль, эмоциональная поддержка, советы
   - Метаданные: zodiac_sign

3. **Analysis Agent** - Аналитик данных
   - Анализ клиентов, паттернов, прогнозы
   - Метаданные: total_customers, patterns, segments

4. **Trend Agent** - Аналитик модных трендов
   - Анализ модных журналов, трендов
   - Метаданные: trends, trend_scores, emerging_trends

5. **Taste Agent** - Определение вкусов
   - Вопросы о предпочтениях, создание профиля
   - Метаданные: current_question_index, is_complete, profile

## 📡 Новые Endpoints

### 1. Consultation Streaming
**POST** `/api/consultation/{user_id}/stream`

Потоковая консультация с ювелирным агентом.

**Request:**
```json
{
  "message": "Я ищу обручальное кольцо",
  "conversation_history": []
}
```

**Response:** Server-Sent Events (SSE)

События:
- `status` - обновления статуса (загрузка профиля, поиск товаров и т.д.)
- `token` - **отдельные токены текста по мере генерации LLM** ⚡
- `metadata` - метаданные (рекомендации, товары) после завершения генерации
- `done` - завершение обработки
- `error` - ошибки

### 2. Orchestrator Streaming
**POST** `/api/orchestrator/{user_id}/stream`

Потоковая обработка через оркестратор (автоматическая маршрутизация к нужным агентам).

**Request:**
```json
{
  "message": "Какие украшения сейчас в моде?",
  "conversation_history": [],
  "explicit_task_type": "trend"  // Опционально: consultant, girlfriend, analysis, trend, taste
}
```

**Response:** Server-Sent Events (SSE)

События:
- `status` - обновления статуса на русском языке (без технических деталей)
  - "Обрабатываю запрос..."
  - "Анализирую ваш запрос..."
  - "Подбираю рекомендации..."
  - "Дружелюбно отвечаю ❤️"
  - "Анализирую данные клиентов..."
  - "Анализирую модные тенденции..."
  - "Определяю ваши предпочтения..."
- `token` - **отдельные токены текста (3 символа) по мере обработки** ⚡
- `metadata` - метаданные от конкретного агента после завершения
- `done` - завершение обработки ("Готово")
- `error` - ошибки с описанием на русском

## 🔧 Архитектура

### Backend Implementation

**LangGraph Single-Pass Streaming:**
- Используется `graph.astream()` с `stream_mode="updates"` для одного прохода через граф
- Получаем словарь `{node_name: node_state}` после каждого узла
- Извлекаем полный текст ответа и разбиваем его на токены по 3 символа
- Симулируем эффект "печатающегося" текста для улучшения UX
- Накапливаем метаданные во время обработки
- Метаданные отправляются после завершения токенов

**FastAPI Endpoints:**
```python
async def event_generator():
    # Single-pass streaming with simulated tokens
    async for event in agent.process_stream(...):
        if event["type"] == "token":
            # Tokens are 3-character chunks for typing effect
            yield f"data: {json.dumps(event)}\n\n"
        elif event["type"] == "metadata":
            # Metadata sent after tokens complete
            yield f"data: {json.dumps(event)}\n\n"
```

### Agent Implementation

**ConsultantAgent:**
```python
async def process_stream(self, user_id, message, conversation_history):
    # Single-pass with updates mode
    async for chunk in self.graph.astream(initial_state, stream_mode="updates"):
        for node_name, node_state in chunk.items():
            current_step = node_state.get("step", "")
            
            # Status updates
            if current_step == "profile_loaded":
                yield {"type": "status", "message": "Загружаю ваш профиль..."}
            
            # Stream response as tokens
            elif current_step == "response_generated":
                response_text = node_state.get("response", "")
                # Split into 3-char tokens for typing effect
                for i in range(0, len(response_text), 3):
                    yield {"type": "token", "content": response_text[i:i+3]}
                
                # Accumulate metadata
                accumulated_data["products"] = node_state.get("products", [])
    
    # Send metadata after tokens
    yield {"type": "metadata", "data": accumulated_data}
```

**AgentOrchestrator (для всех агентов):**
```python
async def handle_user_message_stream(self, user_id, message, ...):
    # Single-pass streaming for all agents
    async for chunk in self.graph.astream(initial_state, stream_mode="updates"):
        for node_name, node_state in chunk.items():
            current_step = node_state.get("step", "")
            
            # Consultant
            if current_step == "consultant_completed":
                result = node_state.get("consultant_result", {})
                response_text = result.get("response", "")
                for i in range(0, len(response_text), 3):
                    yield {"type": "token", "agent": "consultant", "content": response_text[i:i+3]}
            
            # Girlfriend
            elif current_step == "girlfriend_completed":
                result = node_state.get("girlfriend_result", {})
                response_text = result.get("response", "")
                for i in range(0, len(response_text), 3):
                    yield {"type": "token", "agent": "girlfriend", "content": response_text[i:i+3]}
            
            # Analysis, Trend, Taste - аналогично
```

## 🧪 Тестирование

### Установка зависимостей
```bash
pip install httpx  # Для тестового клиента (не входит в основные зависимости)
```

### Запуск тестов

**Test Consultation Stream:**
```bash
python scripts/test_streaming.py consultation
```

**Test Orchestrator Stream:**
```bash
python scripts/test_streaming.py orchestrator
```

### Пример вывода
```
================================================================================
Testing Consultation Token-by-Token Stream
================================================================================

Sending request to: http://localhost:8000/api/consultation/test_user_123/stream
Payload: {
  "message": "Я ищу обручальное кольцо для помолвки, бюджет до 100000 рублей",
  "conversation_history": []
}

Streaming response:
--------------------------------------------------------------------------------
[10:15:30.123] 📊 Starting consultation...
[10:15:30.456] 📊 Loading profile...
[10:15:31.234] 📊 Analyzing preferences...
[10:15:32.567] 📊 Searching products...
[10:15:33.123] 📊 Generating response...
Прекрасный выбор! Для помолвки я рекомендую следующие варианты обручальных колец...
⚡ Текст появляется токен за токеном, создавая эффект "печатающегося" текста! ⚡
--------------------------------------------------------------------------------
[10:15:36.012] 📦 Metadata:
  Recommendations: ['prod_1', 'prod_2', 'prod_3']
  Products: 5 items
[10:15:36.123] ✅ Consultation completed
```

## 📊 События и их структура

### Status Event
```json
{
  "type": "status",
  "message": "Generating response..."
}
```

### Token Event ⚡ (Новое!)
```json
{
  "type": "token",
  "content": "Прекрасный"
}
```

**Пример последовательности токенов:**
```
{"type": "token", "content": "Пр"}
{"type": "token", "content": "екра"}
{"type": "token", "content": "сный"}
{"type": "token", "content": " выб"}
{"type": "token", "content": "ор"}
{"type": "token", "content": "!"}
```

### Metadata Event (Consultation)
```json
{
  "type": "metadata",
  "recommendations": ["prod_1", "prod_2"],
  "products": [{"id": "prod_1", ...}],
  "extracted_preferences": {"style": "classic", ...}
}
```

### Metadata Event (Orchestrator)
```json
{
  "type": "metadata",
  "data": {
    "consultant": {
      "recommendations": ["prod_1"],
      "products": [...]
    },
    "girlfriend": {
      "zodiac_sign": "Овен"
    },
    "analysis": {
      "total_customers": 150,
      "patterns": {...}
    },
    "trend": {
      "trends": {...},
      "trend_scores": {...},
      "emerging_trends": [...]
    },
    "taste": {
      "current_question_index": 3,
      "is_complete": false,
      "profile": {...}
    }
  },
  "completed_agents": ["consultant", "girlfriend"]
}
```

### Done Event
```json
{
  "type": "done",
  "message": "Готово"
}
```

### Error Event
```json
{
  "type": "error",
  "error": "Error details...",
  "message": "Извините, произошла ошибка..."
}
```

## 🌐 Frontend Integration

### React + EventSource Example
```typescript
const eventSource = new EventSource(
  'http://localhost:8000/api/consultation/user123/stream'
);

let accumulatedText = '';

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'status':
      setStatus(data.message);
      break;
      
    case 'token':
      // Append token to create typing effect ⚡
      accumulatedText += data.content;
      setResponse(accumulatedText);
      break;
      
    case 'metadata':
      setRecommendations(data.recommendations);
      setProducts(data.products);
      break;
      
    case 'done':
      eventSource.close();
      setIsLoading(false);
      break;
      
    case 'error':
      handleError(data.error);
      eventSource.close();
      break;
  }
};
```

### React + fetch Example with Typing Effect
```typescript
async function streamConsultation(userId: string, message: string) {
  const response = await fetch(
    `http://localhost:8000/api/consultation/${userId}/stream`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, conversation_history: [] })
    }
  );

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let accumulatedText = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        
        if (data.type === 'token') {
          // Append token for typing effect ⚡
          accumulatedText += data.content;
          setResponse(accumulatedText);
        }
        else if (data.type === 'metadata') {
          setMetadata(data);
        }
      }
    }
  }
}
```

### React Hook Example
```typescript
function useStreamingChat(userId: string) {
  const [response, setResponse] = useState('');
  const [metadata, setMetadata] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (message: string) => {
    setIsLoading(true);
    setResponse('');
    let accumulated = '';

    const eventSource = new EventSource(
      `${API_URL}/consultation/${userId}/stream`,
      {
        method: 'POST',
        body: JSON.stringify({ message })
      }
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'token') {
        // Real-time typing effect ⚡
        accumulated += data.content;
        setResponse(accumulated);
      }
      else if (data.type === 'metadata') {
        setMetadata(data);
      }
      else if (data.type === 'done') {
        eventSource.close();
        setIsLoading(false);
      }
    };
  };

  return { response, metadata, isLoading, sendMessage };
}
```

## 📝 Примечания

1. **Stream Mode**: Используется `stream_mode="updates"` для одного прохода через граф
2. **Simulated Tokens**: Полный ответ разбивается на токены по 3 символа для эффекта "печатающегося" текста ⚡
3. **All Agents Supported**: Streaming реализован для consultant, girlfriend, analysis, trend, taste
4. **Metadata Separately**: Метаданные отправляются отдельным событием после завершения токенов
5. **Russian Messages**: Все статусные сообщения на русском языке без технических деталей
6. **Error Handling**: Все ошибки обрабатываются и отправляются как события типа `error`
7. **Performance**: Значительно улучшает воспринимаемую скорость ответа - пользователь видит начало ответа сразу
8. **Connection**: SSE соединение автоматически закрывается при завершении или ошибке
9. **Single Pass**: Граф выполняется один раз, избегая дублирования обработки

## ⚡ Преимущества Token-by-Token Streaming

1. **Улучшенный UX**: Пользователь видит начало ответа мгновенно
2. **Визуальная обратная связь**: Эффект "печатающегося" текста показывает, что система работает
3. **Уменьшенное воспринимаемое время ответа**: Даже длинные ответы кажутся быстрее
4. **Естественное взаимодействие**: Имитирует человеческую печать
5. **Прогрессивное отображение**: Можно начать читать ответ до его завершения

## 🔗 Ссылки

- [LangGraph Streaming Documentation](https://langchain-ai.github.io/langgraph/how-tos/#streaming_1)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

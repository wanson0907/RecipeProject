document.addEventListener("DOMContentLoaded", function () {
  const root = document.getElementById("recipe-chatbot-root");
  if (!root) return;

  const toggleBtn = document.getElementById("chatbot-toggle-btn");
  const closeBtn = document.getElementById("chatbot-close-btn");
  const chatbotWindow = document.getElementById("chatbot-window");
  const form = document.getElementById("chatbot-form");
  const input = document.getElementById("chatbot-input");
  const messagesContainer = document.getElementById("chatbot-messages");
  const loadingIndicator = document.getElementById("chatbot-loading");
  const chips = document.querySelectorAll(".chatbot-chip");

  // CSRF 토큰 가져오기
  function getCsrfToken() {
    const inputToken = form.querySelector('input[name="csrfmiddlewaretoken"]');
    if (inputToken) return inputToken.value;
    const cookie = document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrftoken="));
    return cookie ? cookie.split("=")[1] : "";
  }

  // 대화 기록 (컨텍스트 유지용)
  const conversationHistory = [];

  // 창 열기/닫기
  function toggleChatbot(forceOpen) {
    const isOpen = !chatbotWindow.classList.contains("d-none");
    if (forceOpen === true || (forceOpen === undefined && !isOpen)) {
      chatbotWindow.classList.remove("d-none");
      setTimeout(() => input.focus(), 150);
      scrollToBottom();
    } else {
      chatbotWindow.classList.add("d-none");
    }
  }

  toggleBtn.addEventListener("click", () => toggleChatbot());
  closeBtn.addEventListener("click", () => toggleChatbot(false));

  // 칩 클릭 시 질문 자동 전송
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const query = chip.dataset.query;
      if (query) {
        input.value = query;
        sendMessage(query);
      }
    });
  });

  // 하단 스크롤
  function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  // 간단한 마크다운/텍스트 안전 변환 (줄바꿈 및 볼드)
  function formatReplyText(raw) {
    if (!raw) return "";
    let safe = raw
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    // 볼드 **text**
    safe = safe.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // 글머리 기호 - 항목
    safe = safe.replace(/(?:^|\n)-\s+(.*)/g, "<br>• $1");
    // 줄바꿈
    safe = safe.replace(/\n/g, "<br>");
    return safe;
  }

  // 메시지 렌더링
  function appendMessage(sender, text, recipes = []) {
    const isUser = sender === "user";
    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-msg ${isUser ? "chat-msg-user" : "chat-msg-bot"}`;

    if (!isUser) {
      const avatar = document.createElement("div");
      avatar.className = "chat-msg-avatar";
      avatar.textContent = "🧑‍🍳";
      msgDiv.appendChild(avatar);
    }

    const contentDiv = document.createElement("div");
    contentDiv.className = "chat-msg-content";

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    bubble.innerHTML = isUser
      ? text
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/\n/g, "<br>")
      : formatReplyText(text);
    contentDiv.appendChild(bubble);

    // 추천된 사이트 레시피 카드 목록
    if (recipes && recipes.length > 0) {
      const cardContainer = document.createElement("div");
      cardContainer.className = "chatbot-recipe-cards";

      recipes.forEach((r) => {
        const card = document.createElement("a");
        card.href = r.url;
        card.className = "chatbot-recipe-card";

        const thumbHtml = r.image_url
          ? `<img src="${r.image_url}" alt="${r.title}" class="chatbot-card-thumb" />`
          : `<div class="chatbot-card-thumb-empty">🍳</div>`;

        card.innerHTML = `
          ${thumbHtml}
          <div class="chatbot-card-info">
            <span class="chatbot-card-tag">추천 레시피</span>
            <div class="chatbot-card-title">${r.title}</div>
            <div class="chatbot-card-desc">${r.description || "재료 보러가기"}</div>
          </div>
        `;
        cardContainer.appendChild(card);
      });

      contentDiv.appendChild(cardContainer);
    }

    msgDiv.appendChild(contentDiv);
    messagesContainer.appendChild(msgDiv);
    scrollToBottom();
  }

  // 전송 처리
  async function sendMessage(userText) {
    const message = (userText || input.value).trim();
    if (!message) return;

    input.value = "";
    input.disabled = true;

    // 사용자 메시지 표시
    appendMessage("user", message);
    conversationHistory.push({ sender: "user", text: message });

    // 로딩 표시
    loadingIndicator.classList.remove("d-none");
    scrollToBottom();

    try {
      const response = await fetch("/api/chatbot/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({
          message: message,
          history: conversationHistory.slice(-6),
        }),
      });

      const data = await response.json();
      loadingIndicator.classList.add("d-none");

      if (response.ok) {
        appendMessage("bot", data.reply, data.recipes);
        conversationHistory.push({ sender: "bot", text: data.reply });
      } else {
        const errMsg = data.error || "답변을 불러오지 못했습니다.";
        appendMessage("bot", `⚠️ 오류: ${errMsg}`);
      }
    } catch (err) {
      loadingIndicator.classList.add("d-none");
      appendMessage(
        "bot",
        "서버와의 통신 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
      );
    } finally {
      input.disabled = false;
      input.focus();
      scrollToBottom();
    }
  }

  // 폼 서밋 핸들러
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    sendMessage();
  });
});

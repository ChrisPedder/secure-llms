"use strict";

const RSA_MAX_PLAINTEXT = 190;
let publicKey = null;

const chat = document.getElementById("chat");
const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const status = document.getElementById("status");

async function init() {
  try {
    const res = await fetch("/public-key");
    if (!res.ok) throw new Error("Failed to fetch public key");
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    publicKey = await importPublicKey(data.public_key_pem);

    status.textContent = "Encryption ready";
    status.className = "status ready";
    input.disabled = false;
    sendBtn.disabled = false;
    input.focus();
  } catch (e) {
    status.textContent = "Encryption unavailable: " + e.message;
    status.className = "status error";
  }
}

async function importPublicKey(pem) {
  const pemBody = pem
    .replace("-----BEGIN PUBLIC KEY-----", "")
    .replace("-----END PUBLIC KEY-----", "")
    .replace(/\s/g, "");
  const der = Uint8Array.from(atob(pemBody), (c) => c.charCodeAt(0));

  return crypto.subtle.importKey(
    "spki",
    der.buffer,
    { name: "RSA-OAEP", hash: "SHA-256" },
    false,
    ["encrypt", "wrapKey"]
  );
}

async function encryptDirect(message) {
  const encoded = new TextEncoder().encode(message);
  const ciphertext = await crypto.subtle.encrypt(
    { name: "RSA-OAEP" },
    publicKey,
    encoded
  );
  return {
    ciphertext: arrayBufferToBase64(ciphertext),
  };
}

async function encryptHybrid(message) {
  const aesKey = await crypto.subtle.generateKey(
    { name: "AES-GCM", length: 256 },
    true,
    ["encrypt"]
  );

  const nonce = crypto.getRandomValues(new Uint8Array(12));
  const encoded = new TextEncoder().encode(message);
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: nonce },
    aesKey,
    encoded
  );

  const wrappedKey = await crypto.subtle.wrapKey("raw", aesKey, publicKey, {
    name: "RSA-OAEP",
  });

  return {
    ciphertext: arrayBufferToBase64(ciphertext),
    encrypted_data_key: arrayBufferToBase64(wrappedKey),
    nonce: arrayBufferToBase64(nonce),
  };
}

async function encryptMessage(message) {
  const byteLength = new TextEncoder().encode(message).length;
  if (byteLength <= RSA_MAX_PLAINTEXT) {
    return encryptDirect(message);
  }
  return encryptHybrid(message);
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function addMessage(text, role) {
  const div = document.createElement("div");
  div.className = "message " + role;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

function removeMessage(el) {
  if (el && el.parentNode) el.parentNode.removeChild(el);
}

async function sendMessage(message) {
  addMessage(message, "user");
  const thinking = addMessage("Thinking...", "thinking");

  input.disabled = true;
  sendBtn.disabled = true;

  try {
    const encrypted = await encryptMessage(message);

    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(encrypted),
    });

    removeMessage(thinking);

    const data = await res.json();
    if (data.error) {
      addMessage(data.error, "error");
    } else {
      addMessage(data.response, "assistant");
    }
  } catch (e) {
    removeMessage(thinking);
    addMessage("Failed to send message: " + e.message, "error");
  } finally {
    input.disabled = false;
    sendBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  sendMessage(message);
});

init();

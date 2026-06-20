<script setup>
import { ref } from 'vue'
import axios from 'axios'

const xmlFile = ref(null)
const zipFile = ref(null)
const gedcomFile = ref(null)
const xmlStatus = ref({ type: '', text: '' })
const zipStatus = ref({ type: '', text: '' })
const gedcomStatus = ref({ type: '', text: '' })
const uploading = ref({ xml: false, zip: false, gedcom: false })

const newLogin = ref('')
const newPassword = ref('')
const passwdStatus = ref({ type: '', text: '' })
const changingPass = ref(false)

function onXmlChange(e) {
  xmlFile.value = e.target.files[0] || null
  xmlStatus.value = { type: '', text: '' }
}

function onZipChange(e) {
  zipFile.value = e.target.files[0] || null
  zipStatus.value = { type: '', text: '' }
}

function onGedcomChange(e) {
  gedcomFile.value = e.target.files[0] || null
  gedcomStatus.value = { type: '', text: '' }
}

async function uploadXml() {
  if (!xmlFile.value) return
  uploading.value.xml = true
  xmlStatus.value = { type: 'loading', text: 'Загрузка…' }
  try {
    const form = new FormData()
    form.append('file', xmlFile.value)
    const res = await axios.post('/api/admin/load_xml_file', form)
    xmlStatus.value = { type: 'ok', text: res.data.message || 'Готово' }
    xmlFile.value = null
  } catch (e) {
    const msg = e.response?.data?.detail || e.message
    xmlStatus.value = { type: 'error', text: `Ошибка: ${msg}` }
  } finally {
    uploading.value.xml = false
  }
}

async function uploadZip() {
  if (!zipFile.value) return
  uploading.value.zip = true
  zipStatus.value = { type: 'loading', text: 'Загрузка…' }
  try {
    const form = new FormData()
    form.append('file', zipFile.value)
    const res = await axios.post('/api/admin/load_photos', form)
    const count = res.data.count_files ?? "?"
    zipStatus.value = { type: 'ok', text: `Загружено ${count} файлов` }
    zipFile.value = null
  } catch (e) {
    const msg = e.response?.data?.detail || e.message
    zipStatus.value = { type: 'error', text: `Ошибка: ${msg}` }
  } finally {
    uploading.value.zip = false
  }
}

async function uploadGedcom() {
  if (!gedcomFile.value) return
  uploading.value.gedcom = true
  gedcomStatus.value = { type: 'loading', text: 'Загрузка…' }
  try {
    const form = new FormData()
    form.append('file', gedcomFile.value)
    const res = await axios.post('/api/admin/load_gedcom', form)
    const msg = res.data.message || 'Готово'
    gedcomStatus.value = { type: 'ok', text: msg }
    gedcomFile.value = null
  } catch (e) {
    const msg = e.response?.data?.detail || e.message
    gedcomStatus.value = { type: 'error', text: `Ошибка: ${msg}` }
  } finally {
    uploading.value.gedcom = false
  }
}

function removeXml() {
  xmlFile.value = null
  xmlStatus.value = { type: '', text: '' }
}

function removeZip() {
  zipFile.value = null
  zipStatus.value = { type: '', text: '' }
}

function removeGedcom() {
  gedcomFile.value = null
  gedcomStatus.value = { type: '', text: '' }
}


async function changeAccount() {
  const login = newLogin.value.trim()
  const pwd = newPassword.value.trim()
  if (!login && !pwd) {
    passwdStatus.value = { type: 'error', text: 'Введите новое имя пользователя или пароль' }
    return
  }
  if (pwd && pwd.length < 4) {
    passwdStatus.value = { type: 'error', text: 'Пароль должен быть минимум 4 символа' }
    return
  }
  changingPass.value = true
  passwdStatus.value = { type: 'loading', text: 'Сохранение…' }
  try {
    const body = {}
    if (login) body.login = login
    if (pwd) body.password = pwd
    const res = await axios.post('/api/admin/change_account', body)
    passwdStatus.value = { type: 'ok', text: res.data.message || 'Данные изменены' }
    newLogin.value = ''
    newPassword.value = ''
  } catch (e) {
    const msg = e.response?.data?.detail || e.message
    passwdStatus.value = { type: 'error', text: `Ошибка: ${msg}` }
  } finally {
    changingPass.value = false
  }
}
</script>

<template>
  <div class="admin-page">
    <div class="page-head">
      <h1 class="page-title">Администрирование</h1>
      <p class="page-sub">Загрузка данных и фотографий</p>
    </div>

    <div class="cards-grid">
      <!-- ─── XML ─── -->
      <div class="admin-card glass">
        <div class="card-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
               stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
          </svg>
        </div>
        <h2 class="card-title">Импорт XML</h2>
        <p class="card-desc">Загрузите экспортированный XML-файл с данными семейного древа</p>

        <div class="drop-zone" :class="{ 'has-file': xmlFile }">
          <label class="file-label" v-if="!xmlFile">
            <input type="file" accept=".xml,text/xml,application/xml" @change="onXmlChange" />
            <span class="drop-hint">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
                   stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <span>Выберите XML-файл</span>
            </span>
          </label>
          <div class="file-info" v-else>
            <div class="file-name">{{ xmlFile.name }}</div>
            <div class="file-size">{{ (xmlFile.size / 1024).toFixed(1) }} KB</div>
            <div class="file-actions">
              <button class="btn btn-ghost" @click="removeXml">Отмена</button>
              <button class="btn btn-primary" :disabled="uploading.xml" @click="uploadXml">
                <span v-if="uploading.xml" class="btn-spinner"></span>
                <span v-else>Загрузить</span>
              </button>
            </div>
          </div>
        </div>

        <div v-if="xmlStatus.type" class="status-msg" :class="xmlStatus.type">
          <span v-if="xmlStatus.type === 'loading'" class="status-spinner"></span>
          {{ xmlStatus.text }}
        </div>
      </div>

      <!-- ─── ZIP ─── -->
      <div class="admin-card glass">
        <div class="card-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
               stroke-linejoin="round">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
            <line x1="12" y1="22.08" x2="12" y2="12"/>
          </svg>
        </div>
        <h2 class="card-title">Импорт ZIP</h2>
        <p class="card-desc">Загрузите ZIP-архив с фотографиями участников древа</p>

        <div class="drop-zone" :class="{ 'has-file': zipFile }">
          <label class="file-label" v-if="!zipFile">
            <input type="file" accept=".zip,application/zip,application/x-zip-compressed" @change="onZipChange" />
            <span class="drop-hint">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
                   stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <span>Выберите ZIP-файл</span>
            </span>
          </label>
          <div class="file-info" v-else>
            <div class="file-name">{{ zipFile.name }}</div>
            <div class="file-size">{{ (zipFile.size / 1024).toFixed(1) }} KB</div>
            <div class="file-actions">
              <button class="btn btn-ghost" @click="removeZip">Отмена</button>
              <button class="btn btn-primary" :disabled="uploading.zip" @click="uploadZip">
                <span v-if="uploading.zip" class="btn-spinner"></span>
                <span v-else>Загрузить</span>
              </button>
            </div>
          </div>
        </div>

        <div v-if="zipStatus.type" class="status-msg" :class="zipStatus.type">
          <span v-if="zipStatus.type === 'loading'" class="status-spinner"></span>
          {{ zipStatus.text }}
        </div>
      </div>

      <!-- ─── GEDCOM ─── -->
      <div class="admin-card glass">
        <div class="card-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
               stroke-linejoin="round">
            <polyline points="16 18 22 12 16 6"/>
            <polyline points="8 6 2 12 8 18"/>
          </svg>
        </div>
        <h2 class="card-title">Импорт GEDCOM</h2>
        <p class="card-desc">Загрузите файл в формате GEDCOM (.ged) для импорта всего древа</p>

        <div class="drop-zone" :class="{ 'has-file': gedcomFile }">
          <label class="file-label" v-if="!gedcomFile">
            <input type="file" accept=".ged,application/x-gedcom" @change="onGedcomChange" />
            <span class="drop-hint">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
                   stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <span>Выберите GEDCOM-файл</span>
            </span>
          </label>
          <div class="file-info" v-else>
            <div class="file-name">{{ gedcomFile.name }}</div>
            <div class="file-size">{{ (gedcomFile.size / 1024).toFixed(1) }} KB</div>
            <div class="file-actions">
              <button class="btn btn-ghost" @click="removeGedcom">Отмена</button>
              <button class="btn btn-primary" :disabled="uploading.gedcom" @click="uploadGedcom">
                <span v-if="uploading.gedcom" class="btn-spinner"></span>
                <span v-else>Загрузить</span>
              </button>
            </div>
          </div>
        </div>

        <div v-if="gedcomStatus.type" class="status-msg" :class="gedcomStatus.type">
          <span v-if="gedcomStatus.type === 'loading'" class="status-spinner"></span>
          {{ gedcomStatus.text }}
        </div>
      </div>

      <!-- ─── Смена учётной записи ─── -->
      <div class="admin-card glass">
        <div class="card-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
               stroke-linejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
        </div>
        <h2 class="card-title">Смена учётной записи</h2>
        <p class="card-desc">Измените имя пользователя и/или пароль для входа в админ-панель</p>

        <div class="account-form">
          <div class="account-input-wrap">
            <input
              class="account-input"
              type="text"
              placeholder="Новое имя пользователя"
              v-model="newLogin"
              @keyup.enter="changeAccount"
            />
          </div>
          <div class="account-input-wrap">
            <input
              class="account-input"
              type="text"
              placeholder="Новый пароль"
              v-model="newPassword"
              @keyup.enter="changeAccount"
            />
          </div>
          <button class="btn btn-primary btn-block" :disabled="changingPass || (!newLogin.trim() && !newPassword.trim())" @click="changeAccount">
            <span v-if="changingPass" class="btn-spinner"></span>
            <span v-else>Сохранить</span>
          </button>
        </div>

        <div v-if="passwdStatus.type" class="status-msg" :class="passwdStatus.type">
          <span v-if="passwdStatus.type === 'loading'" class="status-spinner"></span>
          {{ passwdStatus.text }}
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.admin-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}

/* ─── Заголовок ─── */
.page-head {
  margin-bottom: 32px;
}
.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 6px;
}
.page-sub {
  font-size: 14px;
  color: var(--ink-3);
}

/* ─── Сетка карточек ─── */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 24px;
}

/* ─── Карточка ─── */
.admin-card {
  padding: 28px;
  border-radius: var(--r-lg);
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.card-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--r-md);
  background: var(--tint-tr);
  color: var(--tint);
  display: flex;
  align-items: center;
  justify-content: center;
}
.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--ink);
}
.card-desc {
  font-size: 13px;
  color: var(--ink-3);
  line-height: 1.5;
  margin-bottom: 4px;
}

/* ─── Drop zone ─── */
.drop-zone {
  border: 1.5px dashed var(--hairline);
  border-radius: var(--r-md);
  padding: 16px;
  transition: border-color .2s var(--ease-out), background .2s var(--ease-out);
}
.drop-zone:hover {
  border-color: var(--tint-tr);
  background: var(--tint-tr);
}
.drop-zone.has-file {
  border-style: solid;
  border-color: var(--tint);
  background: var(--tint-tr);
}

.file-label {
  display: block;
  cursor: pointer;
}
.file-label input {
  display: none;
}
.drop-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 0;
  color: var(--ink-3);
  font-size: 13px;
  font-weight: 500;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--ink);
  word-break: break-all;
}
.file-size {
  font-size: 12px;
  color: var(--ink-3);
}
.file-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* ─── Кнопки ─── */
.btn {
  padding: 8px 20px;
  border-radius: var(--r-pill);
  border: 1px solid var(--hairline);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all .15s var(--ease-out);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.btn-block {
  width: 100%;
}
.btn:disabled {
  opacity: .5;
  cursor: not-allowed;
}
.btn-ghost {
  background: transparent;
  color: var(--ink-2);
}
.btn-ghost:hover {
  background: var(--glass-thin);
  color: var(--ink);
}
.btn-primary {
  background: var(--tint);
  border-color: var(--tint);
  color: #fff;
}
.btn-primary:hover:not(:disabled) {
  background: var(--tint-2);
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .6s linear infinite;
}

/* ─── Статус ─── */
.status-msg {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  padding: 10px 14px;
  border-radius: var(--r-sm);
}
.status-msg.ok {
  background: rgba(52, 199, 89, 0.12);
  color: #34C759;
}
.status-msg.error {
  background: rgba(217, 74, 107, 0.12);
  color: #D94A6B;
}
.status-msg.loading {
  background: var(--tint-tr);
  color: var(--tint);
}
.status-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(58, 107, 217, 0.3);
  border-top-color: var(--tint);
  border-radius: 50%;
  animation: spin .6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ─── Смена учётной записи ─── */
.account-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.account-input-wrap {
  width: 100%;
}
.account-input {
  width: 100%;
  padding: 9px 14px;
  border-radius: var(--r-pill);
  border: 1px solid var(--hairline);
  background: var(--glass-thin);
  color: var(--ink);
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: border-color .15s var(--ease-out);
  box-sizing: border-box;
}
.account-input:focus {
  border-color: var(--tint);
}
.account-input::placeholder {
  color: var(--ink-4);
}
</style>

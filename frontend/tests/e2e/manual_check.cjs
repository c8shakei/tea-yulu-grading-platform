const { chromium } = require('playwright-core')
const path = require('path')
const fs = require('fs')

const BASE_URL = 'http://localhost:5173'
const SCREENSHOT_DIR = path.join(__dirname, 'screenshots')
const FIXTURE_DIR = path.join(__dirname, 'fixtures')

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true })
}
if (!fs.existsSync(FIXTURE_DIR)) {
  fs.mkdirSync(FIXTURE_DIR, { recursive: true })
}

// 负向用例辅助文件
const OVERSIZE_FILE = path.join(FIXTURE_DIR, 'oversize_12mb.jpg')
const NON_IMAGE_FILE = path.join(FIXTURE_DIR, 'not_an_image.txt')
if (!fs.existsSync(OVERSIZE_FILE)) {
  fs.writeFileSync(OVERSIZE_FILE, Buffer.alloc(12 * 1024 * 1024, 0xff))
}
if (!fs.existsSync(NON_IMAGE_FILE)) {
  fs.writeFileSync(NON_IMAGE_FILE, 'this is not an image')
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function screenshot(page, name) {
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${name}.png`), fullPage: true })
}

async function waitFor(page, text) {
  await page.waitForFunction(
    t => document.body.innerText.includes(t),
    text,
    { timeout: 10000 }
  )
}

async function dumpPage(page, label) {
  const body = await page.evaluate(() => document.body.innerText)
  console.log(`[${label}] URL:`, page.url())
  console.log(`[${label}] body:`, body.slice(0, 300).replace(/\n/g, ' | '))
}

(async () => {
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } })
  const logs = []
  context.on('page', page => {
    page.on('console', msg => logs.push(`[console] ${msg.type()}: ${msg.text()}`))
    page.on('pageerror', err => logs.push(`[pageerror] ${err.message}`))
    page.on('requestfailed', req => logs.push(`[requestfailed] ${req.url()} ${req.failure()?.errorText}`))
  })

  // 1. 未登录访问首页
  const page1 = await context.newPage()
  await page1.goto(`${BASE_URL}/`)
  await waitFor(page1, '首页仪表盘')
  await screenshot(page1, '01_dashboard_anon')

  // 2. 未登录访问 history 应重定向到 login
  const page2 = await context.newPage()
  await page2.goto(`${BASE_URL}/history`)
  await sleep(1000)
  if (!page2.url().includes('/login')) {
    throw new Error('未登录访问 /history 未重定向到 /login: ' + page2.url())
  }
  await waitFor(page2, '登录')
  await screenshot(page2, '02_history_redirect_to_login')

  // 3. 注册
  const page = await context.newPage()
  await page.goto(`${BASE_URL}/register`)
  await waitFor(page, '注册')
  const ts = Date.now()
  await page.fill('input[placeholder="请输入用户名"]', `w4test_${ts}`)
  await page.fill('input[placeholder="请输入密码"]', '123456')
  await page.fill('input[placeholder="请再次输入密码"]', '123456')
  await page.click('button:has-text("注册")')
  await sleep(3000)
  const bodyAfterRegister = await page.evaluate(() => document.body.innerText)
  console.log('注册后 URL:', page.url())
  console.log('注册后 body 前 500 字:', bodyAfterRegister.slice(0, 500))
  await screenshot(page, '03_register_after_click')
  if (!page.url().includes('/login')) {
    throw new Error('注册后未跳转到登录页: ' + page.url())
  }
  await screenshot(page, '03_register_success')

  // 4. 登录
  await page.fill('input[placeholder="请输入用户名"]', `w4test_${ts}`)
  await page.fill('input[placeholder="请输入密码"]', '123456')
  await page.click('button:has-text("登录")')
  await waitFor(page, '个人中心')
  await screenshot(page, '04_login_success')

  // 5. 首页仪表盘
  await page.goto(`${BASE_URL}/`)
  await waitFor(page, '总检测数')
  await dumpPage(page, 'dashboard')
  await screenshot(page, '05_dashboard_loggedin')

  // 6. 检测工作台
  await page.goto(`${BASE_URL}/detect`)
  await waitFor(page, '上传茶叶图片')
  const testImage = path.join(__dirname, 'test_tea.jpg')
  const [fileChooser] = await Promise.all([
    page.waitForEvent('filechooser'),
    page.click('.el-upload__text em'),
  ])
  await fileChooser.setFiles(testImage)
  await sleep(3000)
  await waitFor(page, '检测结果')
  const detectBody = await page.evaluate(() => document.body.innerText)
  const traceMatch = detectBody.match(/溯源 ID：\s*([a-f0-9\-]+)/)
  const traceId = traceMatch ? traceMatch[1] : null
  console.log('detect trace_id:', traceId)
  await dumpPage(page, 'detect')
  await screenshot(page, '06_detect')

  // 7. 历史记录
  await page.goto(`${BASE_URL}/history`)
  await waitFor(page, '历史记录')
  await dumpPage(page, 'history')
  await screenshot(page, '07_history')

  // 8. 溯源验证
  await page.goto(`${BASE_URL}/trace`)
  await waitFor(page, 'trace_id')
  if (traceId) {
    await page.fill('input[placeholder="请输入 trace_id"]', traceId)
    await page.click('button:has-text("查询")')
    await sleep(2000)
    await waitFor(page, '哈希链验证通过')
  }
  await dumpPage(page, 'trace')
  await screenshot(page, '08_trace')

  // 9. 个人中心
  await page.goto(`${BASE_URL}/profile`)
  await waitFor(page, '个人中心')
  await dumpPage(page, 'profile')
  await screenshot(page, '09_profile')

  // 10. 低代码演示
  await page.goto(`${BASE_URL}/lowcode`)
  await waitFor(page, 'JSON 编辑器')
  await dumpPage(page, 'lowcode')
  await screenshot(page, '10_lowcode')

  // 11. 训练曲线看板
  await page.goto(`${BASE_URL}/training`)
  await waitFor(page, 'W2 训练曲线')
  await dumpPage(page, 'training')
  await screenshot(page, '11_training')

  // 12. 负向用例：未登录访问 /detect 应重定向到登录页（使用全新 browser context）
  const anonContext = await browser.newContext({ viewport: { width: 1280, height: 900 } })
  const anonPage = await anonContext.newPage()
  await anonPage.goto(`${BASE_URL}/detect`)
  await sleep(1000)
  if (!anonPage.url().includes('/login')) {
    throw new Error('未登录访问 /detect 未重定向到 /login: ' + anonPage.url())
  }
  await screenshot(anonPage, '12_detect_anon_redirect')
  await anonPage.close()
  await anonContext.close()

  // 13. 负向用例：上传超过 10MB 的图片，前端应拦截
  await page.goto(`${BASE_URL}/detect`)
  await waitFor(page, '上传茶叶图片')
  let alertMsg = ''
  page.once('dialog', async dialog => {
    alertMsg = dialog.message()
    await dialog.accept()
  })
  const [oversizeChooser] = await Promise.all([
    page.waitForEvent('filechooser'),
    page.click('.el-upload__text em'),
  ])
  await oversizeChooser.setFiles(OVERSIZE_FILE)
  await sleep(500)
  if (!alertMsg.includes('10MB')) {
    throw new Error('超大文件未触发 10MB 限制提示，实际提示：' + alertMsg)
  }
  await screenshot(page, '13_oversize_rejected')

  // 14. 负向用例：上传非图片文件，应被判为最低等级（等外 / 置信度 0%）
  await page.goto(`${BASE_URL}/detect`)
  await waitFor(page, '上传茶叶图片')
  const [badChooser] = await Promise.all([
    page.waitForEvent('filechooser'),
    page.click('.el-upload__text em'),
  ])
  await badChooser.setFiles(NON_IMAGE_FILE)
  await sleep(4000)
  const bodyAfterBad = await page.evaluate(() => document.body.innerText)
  if (!bodyAfterBad.includes('检测结果') || !(bodyAfterBad.includes('等外') || bodyAfterBad.includes('0%'))) {
    console.log('非图片文件检测结果 body:', bodyAfterBad.slice(0, 500))
    throw new Error('非图片文件未被判为等外或置信度 0%')
  }
  await screenshot(page, '14_nonimage_rejected')

  console.log('--- browser logs ---')
  logs.forEach(l => console.log(l))
  await browser.close()
  console.log('E2E 全量巡检通过，截图保存到:', SCREENSHOT_DIR)
})().catch(e => {
  console.error('E2E 巡检失败:', e)
  process.exit(1)
})

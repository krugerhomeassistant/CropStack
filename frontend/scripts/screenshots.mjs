// Visual check before a release (docs/DESIGN.md): every page × light/dark × phone/desktop.
// Usage: CROPSTACK_URL=http://127.0.0.1:8000 npm run screenshots
// Needs a running server. On a fresh one it registers `screens` and sets up a garden; otherwise it logs in.
// Output: frontend/screenshots/<page>-<theme>-<device>.png (git-ignored).
import { mkdirSync } from 'node:fs'
import { chromium } from 'playwright'

const base = process.env.CROPSTACK_URL ?? 'http://127.0.0.1:8000'
const user = process.env.CROPSTACK_USER ?? 'screens'
const password = process.env.CROPSTACK_PASSWORD ?? 'screens-only-123'
const out = new URL('../screenshots/', import.meta.url).pathname
const pages = ['today', 'garden', 'more', 'climate', 'household', 'settings']
const devices = { phone: { width: 390, height: 844 }, desktop: { width: 1440, height: 900 } }

mkdirSync(out, { recursive: true })
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH })

// Sign in once and reuse the cookie for every context.
const setup = await browser.newPage()
await setup.goto(base)
const create = setup.getByRole('button', { name: 'Create account' })
await setup.getByLabel('Username').fill(user)
await setup.getByLabel('Password').fill(password)
if (await create.isVisible()) {
  await setup.getByLabel('Your name').fill(process.env.CROPSTACK_NAME ?? 'Sam')
  await create.click()
} else await setup.getByRole('button', { name: 'Log in' }).click()
const latitude = setup.getByLabel('Latitude')
await Promise.race([latitude.waitFor(), setup.getByRole('navigation').first().waitFor()])
if (await latitude.isVisible()) {
  await latitude.fill('-33.93')
  await setup.getByLabel('Longitude').fill('18.86')
  await setup.getByRole('button', { name: 'Save garden' }).click()
  await setup.waitForURL(/\/today$/)
}
const state = await setup.context().storageState()
await setup.close()

for (const [device, viewport] of Object.entries(devices))
  for (const colorScheme of ['light', 'dark']) {
    const context = await browser.newContext({ viewport, colorScheme, storageState: state })
    const page = await context.newPage()
    for (const name of pages) {
      await page.goto(`${base}/${name}`)
      await page.waitForLoadState('networkidle')
      await page.screenshot({ path: `${out}${name}-${colorScheme}-${device}.png`, fullPage: true })
    }
    await context.close()
  }
await browser.close()
console.log(`${pages.length * 4} screenshots in ${out}`)

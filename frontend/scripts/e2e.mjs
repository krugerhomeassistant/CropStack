// End-to-end check of the main flows in a real browser. Run against a FRESH server (empty data dir):
//   CROPSTACK_URL=http://127.0.0.1:8000 npm run e2e
// The server's outside services should be stubbed (see CONTRIBUTING.md, "E2E"); nothing here needs the network.
// Exits non-zero on the first failed step.
import assert from 'node:assert/strict'
import { chromium } from 'playwright'

const base = process.env.CROPSTACK_URL ?? 'http://127.0.0.1:8000'
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH })
const errors = []

async function phone() {
  const page = await (await browser.newContext({ viewport: { width: 390, height: 844 } })).newPage()
  page.on('pageerror', (e) => errors.push(e.message))
  return page
}
const path = (page) => new URL(page.url()).pathname
const nav = (page, name) => page.getByRole('navigation', { name: 'Main' }).getByRole('link', { name }).click()
const step = (name) => console.log(`✓ ${name}`)

try {
  // Owner: sign up, set up the garden, land on Today
  const owner = await phone()
  await owner.goto(base)
  await owner.getByLabel('Your name').fill('Jan')
  await owner.getByLabel('Username').fill('jan')
  await owner.getByLabel('Password').fill('garden123')
  await owner.getByRole('button', { name: 'Create account' }).click()
  await owner.getByLabel('Latitude').fill('-33.93')
  await owner.getByLabel('Longitude').fill('18.86')
  await owner.getByLabel(/Cautious/).check()
  await owner.getByRole('button', { name: 'Save garden' }).click()
  await owner.getByText('Your daily jobs will appear here').waitFor()
  assert.equal(path(owner), '/today')
  await owner.getByRole('list', { name: 'Next 7 days' }).waitFor()
  step('sign up, garden setup, Today with weather')

  // Garden: edit and cancel, then edit and save a new name
  await nav(owner, 'Garden')
  await owner.getByRole('button', { name: 'Edit garden' }).click()
  await owner.getByRole('button', { name: 'Cancel' }).click()
  await owner.getByRole('button', { name: 'Edit garden' }).click()
  await owner.getByLabel('Garden name').fill('Back yard')
  await owner.getByRole('button', { name: 'Save garden' }).click()
  await owner.getByRole('heading', { name: 'Back yard' }).waitFor()
  step('garden edit, cancel and save')

  // Climate
  await nav(owner, 'More')
  await owner.getByRole('link', { name: /Climate/ }).click()
  await owner.getByText(/^Zone /).waitFor()
  step('climate card')

  // Charts: temperature lines with a tooltip on hover and a table alternative; rain bars; no frost chart without frost
  await owner.getByRole('heading', { name: 'Temperature through the year' }).waitFor()
  const chart = owner.getByRole('group', { name: 'Temperature through the year' })
  await chart.scrollIntoViewIfNeeded()
  const box = await chart.boundingBox()
  await owner.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
  await chart.getByRole('status').getByText('Daily high').waitFor()
  await owner.getByRole('img', { name: 'Rain per month' }).waitFor()
  await owner.getByText('Show as a table').first().click()
  await owner.getByRole('cell', { name: 'January' }).first().waitFor()
  if (await owner.getByRole('heading', { name: 'Chance of a freezing night' }).count())
    throw new Error('frost chart shown for a climate without frost')
  step('climate charts')

  // Crops: search, open one, its values carry numbered sources
  await nav(owner, 'More')
  await owner.getByRole('link', { name: /Crops/ }).click()
  await owner.getByLabel('Search crops').fill('tamatie')
  await owner.getByRole('link', { name: /Tomato/ }).click()
  await owner.getByRole('heading', { name: 'Sowing' }).waitFor()
  await owner.getByRole('heading', { name: 'Growing conditions' }).waitFor()
  await owner.getByText(/Grows between .* best between/).waitFor()
  await owner.getByRole('link', { name: 'Source 1' }).first().waitFor()
  assert.ok(await owner.getByRole('heading', { name: 'Sources' }).isVisible())
  await owner.getByLabel('Back').click()
  await owner.getByRole('link', { name: 'Where the crop data comes from' }).click()
  await owner.getByRole('heading', { name: 'Included in CropStack' }).waitFor()
  step('crop catalog: search, detail with sources, credits')

  // Settings: start screen and units persist after a reload
  await owner.goto(`${base}/settings`)
  await owner.getByLabel(/Imperial/).check()
  await owner.getByLabel(/^Garden/).check()
  await owner.waitForTimeout(400)
  await owner.goto(base)
  await owner.waitForURL(/\/garden$/)
  await owner.goto(`${base}/settings`)
  assert.ok(await owner.getByLabel(/Imperial/).isChecked())
  await owner.getByLabel(/Metric/).check()
  await owner.getByLabel(/^Today/).check()
  step('settings: start screen and units persist')

  // Data sources: switching place search off hides it in garden setup
  const placeSwitch = owner.getByRole('switch', { name: /Nominatim/ })
  await placeSwitch.uncheck()
  await owner.waitForTimeout(400)
  await owner.goto(`${base}/garden`)
  await owner.getByRole('button', { name: 'Edit garden' }).click()
  await owner.getByLabel('Latitude').waitFor()
  await owner.waitForTimeout(400)
  assert.equal(await owner.getByPlaceholder('Town, address or postal code').count(), 0)
  await owner.getByRole('button', { name: 'Cancel' }).click()
  await owner.goto(`${base}/settings`)
  await owner.getByRole('switch', { name: /Nominatim/ }).check()
  step('data-source switch hides place search')

  // Household: rename, invite a member
  await owner.goto(`${base}/household`)
  await owner.getByLabel('Household name').fill('Kruger homestead')
  await owner.getByRole('button', { name: 'Save name' }).click()
  await owner.getByRole('button', { name: 'Save name' }).waitFor({ state: 'detached' })
  await owner.getByLabel(/^Member/).check()
  await owner.getByRole('button', { name: 'Create invite link' }).click()
  const link = await owner.getByLabel('Invite link').inputValue()
  step('household rename and invite link')

  // Member: join via the link, sees Today, cannot edit the garden or invite
  const member = await phone()
  await member.goto(link)
  await member.getByText(/invited to join Kruger homestead/).waitFor()
  await member.getByLabel('Your name').fill('Marie')
  await member.getByLabel('Username').fill('marie')
  await member.getByLabel('Password').fill('garden456')
  await member.getByRole('button', { name: 'Join Kruger homestead' }).click()
  await member.getByText('Your daily jobs will appear here').waitFor()
  await nav(member, 'Garden')
  await member.getByRole('heading', { name: 'Back yard' }).waitFor()
  assert.equal(await member.getByRole('button', { name: 'Edit garden' }).count(), 0)
  await member.goto(`${base}/household`)
  await member.getByRole('heading', { name: 'People' }).waitFor()
  assert.equal(await member.getByRole('heading', { name: 'Invite someone' }).count(), 0)
  step('member joins by invite with member rights')

  // Owner: change the member's role, then remove them
  await owner.reload()
  await owner.getByLabel('Role for Marie').selectOption('viewer')
  await owner.waitForTimeout(400)
  assert.equal(await owner.getByLabel('Role for Marie').inputValue(), 'viewer')
  await owner.getByRole('button', { name: 'Remove Marie' }).click()
  await owner.getByRole('button', { name: 'Remove login?' }).click()
  await owner.getByText('@marie').waitFor({ state: 'detached' })
  step('role change and remove member')

  // Log out
  await nav(owner, 'More')
  await owner.getByRole('button', { name: 'Log out' }).click()
  await owner.getByRole('button', { name: 'Log in' }).waitFor()
  await owner.getByLabel('Username').fill('jan')
  await owner.getByLabel('Password').fill('wrong-password')
  await owner.getByRole('button', { name: 'Log in' }).click()
  await owner.getByRole('alert').waitFor()
  step('log out and failed log in')

  // Desktop: the side rail replaces the bottom bar
  const desk = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage()
  await desk.goto(base)
  await desk.getByLabel('Username').fill('jan')
  await desk.getByLabel('Password').fill('garden123')
  await desk.getByRole('button', { name: 'Log in' }).click()
  await desk.getByRole('navigation', { name: 'Main' }).getByRole('link', { name: 'Household' }).click()
  await desk.waitForURL(/\/household$/)
  step('desktop rail navigation')

  assert.deepEqual(errors, [], 'page errors')
  console.log('E2E passed')
} finally {
  await browser.close()
}

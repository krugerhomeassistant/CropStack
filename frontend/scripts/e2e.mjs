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
/** A bounding box once the layout has stopped moving (lists above it load late). */
async function stableBox(locator) {
  let last = ''
  for (let i = 0; i < 40; i++) {
    const box = await locator.boundingBox()
    const now = JSON.stringify(box)
    if (now === last) return box
    last = now
    await locator.page().waitForTimeout(150)
  }
  throw new Error('layout never settled')
}
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
  await owner.getByText('Nothing to do today').waitFor()
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
  await owner.getByRole('heading', { name: 'When to sow here' }).waitFor()
  await owner.getByRole('heading', { name: 'Start indoors, set out seedlings' }).waitFor()
  await owner.getByText(/Grows between .* best between/).waitFor()
  await owner.getByRole('link', { name: 'Source 1' }).first().waitFor()
  assert.ok(await owner.getByRole('heading', { name: 'Sources' }).isVisible())
  await owner.getByRole('button', { name: 'Plant this' }).first().click()
  await owner.getByLabel('How many').fill('6')
  await owner.getByLabel('Where').fill('Bed 1')
  await owner.getByRole('button', { name: 'Save planting' }).click()
  await owner.getByText('Added to your plantings').waitFor()
  await owner.getByLabel('Back').click()
  await owner.getByRole('link', { name: 'Where the crop data comes from' }).click()
  await owner.getByRole('heading', { name: 'Included in CropStack' }).waitFor()
  step('crop catalog: search, detail with sources, credits')

  // The planting is listed on the Garden page and moves along
  await owner.goto(`${base}/garden`)
  await owner.getByRole('heading', { name: 'Plantings' }).waitFor()
  await owner.getByText('6 planted · Bed 1').waitFor()
  await owner.getByRole('button', { name: 'Mark sown' }).click()
  await owner.getByText('Sown', { exact: true }).waitFor()
  step('plant from a window, list and advance')

  // Garden plan: add a bed, drag it, and give a planting a place in it
  await owner.getByRole('heading', { name: 'What to plant' }).waitFor() // it loads late and moves the page
  const plan = owner.getByRole('img', { name: 'Plan of the garden beds' })
  await plan.scrollIntoViewIfNeeded()
  const planBox = await stableBox(plan)
  await owner.getByRole('button', { name: 'Draw bed' }).click()
  await owner.mouse.move(planBox.x + 60, planBox.y + 40)
  await owner.mouse.down()
  await owner.mouse.move(planBox.x + 160, planBox.y + 120, { steps: 5 })
  await owner.mouse.up()
  await owner.getByRole('button', { name: /^Plant in Bed 1/ }).first().waitFor() // the list grows once it knows the bed
  const drawn = (await (await owner.request.get(`${base}/api/v1/beds`)).json())[0]
  assert.ok(drawn.width > 1 && drawn.length > 1, 'the bed takes the size that was dragged')
  const bedRect = owner.locator('svg[role=img] rect[stroke-width]').first()
  await bedRect.scrollIntoViewIfNeeded()
  const bedBox = await stableBox(bedRect)
  await owner.mouse.move(bedBox.x + 10, bedBox.y + 10)
  await owner.mouse.down()
  await owner.mouse.move(bedBox.x + 70, bedBox.y + 50, { steps: 5 })
  await owner.mouse.up()
  await owner.waitForTimeout(500) // the move is saved on release
  const [bed] = await (await owner.request.get(`${base}/api/v1/beds`)).json()
  if (bed.x <= 0.5 && bed.y <= 0.5) throw new Error(`bed did not move: ${JSON.stringify(bedBox)} ${bed.x},${bed.y}`)
  // Resize by the corner handle, and group into a layout that moves as one
  const logs = []
  owner.on('console', (m) => logs.push(m.text()))
  owner.on('pageerror', (e) => logs.push(String(e)))
  await owner.getByTestId('resize-handle').evaluate((el) => el.scrollIntoView({ block: 'center' })) // clear of the bottom bar
  const handle = await stableBox(owner.getByTestId('resize-handle'))
  const before = (await (await owner.request.get(`${base}/api/v1/beds`)).json())[0]
  await owner.mouse.move(handle.x + handle.width / 2, handle.y + handle.height / 2)
  await owner.mouse.down()
  await owner.mouse.move(handle.x + handle.width / 2 + 40, handle.y + handle.height / 2 + 40, { steps: 4 })
  await owner.mouse.up()
  let after = before
  for (let i = 0; i < 20 && after.width <= before.width; i++) {
    await owner.waitForTimeout(250) // the new size is saved on release
    after = (await (await owner.request.get(`${base}/api/v1/beds`)).json())[0]
  }
  assert.ok(after.width > before.width && after.length > before.length, `the corner handle resizes the bed: ${JSON.stringify([before.width, after.width, handle])} ${await owner.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); return el ? el.outerHTML.slice(0, 160) : 'nothing' }, [handle.x + handle.width / 2, handle.y + handle.height / 2])} ${logs.join('|')} ${JSON.stringify((await (await owner.request.get(`${base}/api/v1/beds`)).json()).map((b) => [b.id, b.x, b.y, b.width, b.length]))} ${await owner.getByRole('button', { name: 'Draw bed' }).getAttribute('aria-pressed')}`)
  await owner.getByLabel('Layout', { exact: true }).fill('Back garden')
  await owner.getByRole('button', { name: 'Save', exact: true }).first().click()
  await owner.getByText(/Back garden/).first().waitFor()
  await owner.getByLabel(/^Bed for/).first().selectOption({ label: 'Bed 1' })
  await owner.getByText(/1 planted here/).waitFor()
  step('garden plan: add, drag and place a planting')

  // Cells: paint two crops into one bed, then see recommendations with a place in the plan
  await owner.getByRole('button', { name: /^Bed 1/ }).click()
  await owner.getByLabel('Plant', { exact: true }).selectOption('lettuce')
  await owner.getByRole('img', { name: 'Cells of Bed 1' }).scrollIntoViewIfNeeded()
  const cells = await stableBox(owner.getByRole('img', { name: 'Cells of Bed 1' }))
  await owner.mouse.move(cells.x + 10, cells.y + 10)
  await owner.mouse.down()
  await owner.mouse.move(cells.x + cells.width * 0.6, cells.y + 10, { steps: 6 })
  await owner.mouse.up()
  await owner.getByText(/In this bed: .*Lettuce/).waitFor()
  await owner.getByLabel('Plant', { exact: true }).selectOption('radish')
  await owner.mouse.move(cells.x + cells.width * 0.9, cells.y + 10)
  await owner.mouse.down()
  await owner.mouse.up()
  await owner.getByText(/In this bed: .*Radish/).waitFor()
  step('garden plan: paint a mixed bed, recommendations shown')

  // Harvests are logged once a crop is growing
  const first = (await (await owner.request.get(`${base}/api/v1/plantings`)).json()).find((p) => p.quantity === 6) // the one sown above
  for (const status of ['germinated', 'harvesting'])
    await owner.request.patch(`${base}/api/v1/plantings/${first.id}`, { data: { status } })
  await owner.reload()
  await owner.getByRole('button', { name: 'Log a harvest' }).first().click()
  await owner.getByLabel('How much').fill('1.5')
  await owner.getByRole('button', { name: 'Save', exact: true }).click()
  await owner.getByText(/Picked: 1\.5/).waitFor()
  step('log a harvest')

  // A job that is due today shows on Today with its reason, and finishing it moves the planting
  const todayIso = new Date().toISOString().slice(0, 10)
  await owner.request.post(`${base}/api/v1/plantings`, {
    data: { crop: 'lettuce', method: 'direct', start_date: todayIso, quantity: 3, location: 'Bed 2' },
  })
  await nav(owner, 'Today')
  await owner.getByRole('heading', { name: 'Sow lettuce (3) in Bed 2' }).waitFor()
  await owner.getByText('You planned to sow on').first().waitFor()
  await owner.getByText('How to do it').first().click()
  await owner.getByText(/Firm the soil gently/).first().waitFor()
  await owner.getByRole('listitem').filter({ has: owner.getByRole('heading', { name: 'Sow lettuce (3) in Bed 2' }) }).getByRole('button', { name: 'Mark sown' }).click()
  await owner.getByRole('heading', { name: 'Sow lettuce (3) in Bed 2' }).waitFor({ state: 'detached' })
  step('Today shows the due job and finishing it moves the planting')

  // Garden assistant: off until an owner picks a service; the key is saved but never shown again
  await owner.goto(`${base}/ask`)
  await owner.getByText('The garden assistant is off').waitFor()
  await owner.goto(`${base}/settings`)
  await owner.getByLabel('Service').selectOption('openai')
  await owner.getByLabel('Model').fill('test-model')
  await owner.getByLabel('API key').fill('sk-e2e-secret')
  await owner.getByRole('button', { name: 'Save', exact: true }).click()
  await owner.getByText('A key is saved').waitFor()
  assert.equal(await owner.getByLabel('API key').inputValue(), '')
  assert.ok(!(await owner.content()).includes('sk-e2e-secret'))
  await owner.goto(`${base}/ask`)
  await owner.getByLabel('Your question').waitFor()
  await owner.request.delete(`${base}/api/v1/ai`)
  step('Garden assistant: set up in Settings, key never shown')

  // Settings: start screen and units persist after a reload
  await owner.goto(`${base}/settings`)
  await owner.getByLabel(/Imperial/).check()
  await owner.getByRole('radio', { name: /^Garden / }).check()
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
  await member.getByRole('link', { name: 'Garden' }).first().waitFor() // Today has jobs now: the painted cells are plantings
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

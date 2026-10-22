import { expect, type Locator, type Page, test } from "@playwright/test"

import type { Role } from "../src/client"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

const matrix: {
  role: Role
  canListUsers: boolean
  canManageUsers: boolean
  canViewMetrics: boolean
}[] = [
  {
    role: "admin",
    canListUsers: true,
    canManageUsers: true,
    canViewMetrics: true,
  },
  {
    role: "manager",
    canListUsers: true,
    canManageUsers: false,
    canViewMetrics: true,
  },
  {
    role: "member",
    canListUsers: false,
    canManageUsers: false,
    canViewMetrics: false,
  },
]

test.use({ storageState: { cookies: [], origins: [] } })

async function logInAs(page: Page, role: Role) {
  const email = randomEmail()
  const password = randomPassword()
  await createUser({ email, password, role })
  await logInUser(page, email, password)
}

async function expectShown(locator: Locator, shown: boolean) {
  if (shown) {
    await expect(locator).toBeVisible()
  } else {
    await expect(locator).toHaveCount(0)
  }
}

for (const { role, canListUsers, canManageUsers, canViewMetrics } of matrix) {
  test.describe(`as ${role}`, () => {
    test.beforeEach(async ({ page }) => {
      await logInAs(page, role)
    })

    test("sidebar shows only permitted links", async ({ page }) => {
      await expectShown(
        page.getByRole("link", { name: "Users", exact: true }),
        canListUsers,
      )
      await expectShown(
        page.getByRole("link", { name: "Metrics", exact: true }),
        canViewMetrics,
      )
    })

    test("users page", async ({ page }) => {
      const otherUserEmail = randomEmail()
      await createUser({ email: otherUserEmail, password: randomPassword() })

      await page.goto("/admin")

      if (!canListUsers) {
        await expect(page.getByTestId("forbidden")).toBeVisible()
        return
      }
      const otherUserRow = page
        .getByRole("row")
        .filter({ hasText: otherUserEmail })
      await expect(otherUserRow).toBeVisible()
      await expectShown(
        page.getByRole("button", { name: "Add User" }),
        canManageUsers,
      )
      await expectShown(otherUserRow.getByRole("button"), canManageUsers)
    })

    test("metrics page", async ({ page }) => {
      await page.goto("/metrics")

      if (!canViewMetrics) {
        await expect(page.getByTestId("forbidden")).toBeVisible()
        return
      }
      await expect(page.getByRole("heading", { name: "Metrics" })).toBeVisible()
      await expect(page.getByText("Total users")).toBeVisible()
    })

    test("can edit own profile", async ({ page }) => {
      const updatedName = `Renamed ${role}`

      await page.goto("/settings")
      await page.getByRole("tab", { name: "My profile" }).click()
      await page.getByRole("button", { name: "Edit" }).click()
      await page.getByLabel("Full name").fill(updatedName)
      await page.getByRole("button", { name: "Save" }).click()

      await expect(page.getByText("User updated successfully")).toBeVisible()
    })
  })
}

test("a 403 from the API shows the error and keeps the user signed in", async ({
  page,
}) => {
  await logInAs(page, "member")
  await page.route(
    (url) => url.pathname === "/api/v1/users/me",
    (route) =>
      route.request().method() === "PATCH"
        ? route.fulfill({
            status: 403,
            json: { detail: "The user doesn't have enough privileges" },
          })
        : route.fallback(),
  )

  await page.goto("/settings")
  await page.getByRole("tab", { name: "My profile" }).click()
  await page.getByRole("button", { name: "Edit" }).click()
  await page.getByLabel("Full name").fill("Blocked change")
  await page.getByRole("button", { name: "Save" }).click()

  await expect(
    page.getByText("The user doesn't have enough privileges"),
  ).toBeVisible()
  await expect(page).toHaveURL(/\/settings/)
})

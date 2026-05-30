import { test, expect } from "@playwright/test";

test.describe("Connexion WebSocket", () => {
  test("L'orb est visible et le status s'affiche", async ({ page }) => {
    await page.goto("/");

    // L'orb doit être présent
    const orb = page.getByTestId("voice-orb");
    await expect(orb).toBeVisible();
    await expect(orb).toHaveAttribute("data-state", "idle");

    // Le status de connexion doit être affiché
    const status = page.getByTestId("connection-status");
    await expect(status).toBeVisible();
  });

  test("Le status passe à Connected quand le backend tourne", async ({ page }) => {
    await page.goto("/");
    const status = page.getByTestId("connection-status");
    // Attendre max 5s que la connexion s'établisse
    await expect(status).toContainText("Connected", { timeout: 5000 });
  });

  test("L'input texte et le bouton Envoyer sont présents", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("text-input")).toBeVisible();
    await expect(page.getByRole("button", { name: "Envoyer" })).toBeVisible();
  });

  test("Les Quick Actions sont présentes (5 boutons)", async ({ page }) => {
    await page.goto("/");
    const toolbar = page.getByTestId("quick-actions");
    await expect(toolbar).toBeVisible();
    const buttons = toolbar.locator("button");
    await expect(buttons).toHaveCount(5);
  });
});

import { test, expect } from "@playwright/test";

test.describe("Fallback mode texte", () => {
  test("Envoyer un message texte quand backend connecté", async ({ page }) => {
    await page.goto("/");
    // Attendre connexion
    await expect(page.getByTestId("connection-status")).toContainText(
      "Connected",
      { timeout: 5000 }
    );

    const input = page.getByTestId("text-input");
    await input.fill("Bonjour Jarvis");
    await input.press("Enter");

    // La bulle user doit apparaître
    await expect(page.getByTestId("msg-user").first()).toContainText(
      "Bonjour Jarvis",
      { timeout: 3000 }
    );

    // La bulle assistant doit apparaître (streaming)
    await expect(page.getByTestId("msg-assistant").first()).toBeVisible({
      timeout: 10000,
    });
  });
});

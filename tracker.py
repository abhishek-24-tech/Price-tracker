import json, time
from playwright.sync_api import sync_playwright
from notifier import send_email, send_telegram

def login_amazon(page):
    print("Logging into Amazon...")
    email = input("Enter Amazon email: ")
    password = input("Enter Amazon password: ")

    page.goto("https://www.amazon.in/ap/signin")
    page.fill("input[name='email']", email)
    page.click("input#continue")
    page.fill("input[name='password']", password)
    page.click("input#signInSubmit")
    time.sleep(5)  # wait for login to complete

def get_price(page, url):
    page.goto(url)
    page.wait_for_selector("#productTitle", timeout=10000)
    title = page.query_selector("#productTitle").inner_text().strip()

    price_el = page.query_selector("span.a-price-whole")
    if not price_el:
        return title, None
    price = int(price_el.inner_text().replace(",", "").strip())
    return title, price

def main():
    with open("config.json") as f:
        config = json.load(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        login_amazon(page)

        for product in config["products"]:
            title, price = get_price(page, product["url"])
            if price is None:
                print(f"❌ Could not fetch price for {title}")
                continue

            print(f"✅ {title}: ₹{price}")
            if price < product["threshold"]:
                msg = f"Price Drop Alert!\n{title}\nCurrent Price: ₹{price}\nLink: {product['url']}"

                if config["email"]["enabled"]:
                    send_email(
                        config["email"]["sender"],
                        config["email"]["password"],
                        config["email"]["receiver"],
                        "Amazon Price Alert 🚨",
                        msg
                    )

                if config["telegram"]["enabled"]:
                    send_telegram(
                        config["telegram"]["bot_token"],
                        config["telegram"]["chat_id"],
                        msg
                    )

        browser.close()

if __name__ == "__main__":
    main()
